# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Outspline.
#
# Outspline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Outspline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Outspline.  If not, see <http://www.gnu.org/licenses/>.

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin
import sys
import time as _time
import os

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import log
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.extensions.organism_alarms_api as organism_alarms_api

COLUMNS = (
    ('Database', 120),
    ('Title', 200),
    ('Start', 120),
    ('End', 120),
    ('Alarm', 120),
)


class AutoListView(wx.ListView, ListCtrlAutoWidthMixin, ColumnSorterMixin):
    imagelistsmall = None
    imagemap = None

    def __init__(self, parent):
        # Note that this makes use of ListView, which is an interface for
        # ListCtrl
        wx.ListView.__init__(self, parent, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)
        ColumnSorterMixin.__init__(self, len(COLUMNS))

        self.set_image_lists()

    def GetListCtrl(self):
        return self

    def set_image_lists(self):
        self.imagelistsmall = wx.ImageList(16, 16)
        self.imagemap = {
            'small': {}
        }

        self.imagemap['small']['sortup'] = self.imagelistsmall.Add(
                 wx.ArtProvider.GetBitmap('@sortup', wx.ART_TOOLBAR, (16, 16)))
        self.imagemap['small']['sortdown'] = self.imagelistsmall.Add(
               wx.ArtProvider.GetBitmap('@sortdown', wx.ART_TOOLBAR, (16, 16)))

        self.SetImageList(self.imagelistsmall, wx.IMAGE_LIST_SMALL)

    def GetSortImages(self):
        return (self.imagemap['small']['sortup'],
                                            self.imagemap['small']['sortdown'])


class TaskList():
    list_ = None
    occs = None
    datamap = None
    DELAY = None
    delay = None
    timer = None

    def __init__(self, parent):
        self.list_ = AutoListView(parent)

        for col, values in enumerate(COLUMNS):
            self.list_.InsertColumn(col, values[0], width=values[1])

        # Note that columns are counted from 1 here (thus 2 is 'Title')
        self.list_.setResizeColumn(2)

        self.DELAY = coreaux_api.get_plugin_configuration('wxtasklist'
                                                      ).get_int('refresh_delay')

        # Initialize self.delay with a dummy function (int())
        self.delay = wx.CallLater(self.DELAY, int())
        self.timer = wx.CallLater(0, self.restart)

        core_api.bind_to_update_item(self.delay_restart_on_text_update)
        # Note that self.delay_restart is *not* bound to
        # organism_timer_api.bind_to_get_next_occurrences which is signalled by
        # self.refresh signal because of the call to
        # organism_timer_api.get_next_occurrences, otherwise this would make
        # self.refresh recur infinitely
        organism_timer_api.bind_to_search_next_occurrences(self.delay_restart)
        organism_alarms_api.bind_to_alarm_off(self.delay_restart)

    def delay_restart_on_text_update(self, kwargs=None):
        if kwargs['text'] is not None:
            self.delay_restart()

    def delay_restart(self, kwargs=None):
        # Instead of self.restart, bind _this_ function to events that can be
        # signalled many times in a loop, so that self.restart is executed only
        # once after the last signal
        self.delay.Stop()
        self.delay = wx.CallLater(self.DELAY, self.restart)

    def restart(self, kwargs=None):
        self.timer.Stop()
        delays = self.refresh()

        try:
            delay = min(delays)
        except ValueError:
            # delays could be empty
            pass
        else:
            log.debug('Next tasklist refresh in {} seconds'.format(delay))

            # delay may become too big (long instead of int), limit it to 24h
            # This has also the advantage of limiting the drift of the timer
            try:
                self.timer.Restart(delay * 1000)
            except OverflowError:
                self.timer.Restart(min(86400000, sys.maxint))

    def refresh(self, mint=None, dt=86400, max_=60):
        log.debug('Refresh tasklist')

        if not mint:
            now = int(_time.time())
            # Round down to the previous minute, so as to include also the
            # occurrences that fall in the current minute, in fact now is
            # calculated after the exact minute has already stricken
            mint = now - 60
            maxt = now + dt
        else:
            maxt = mint + dt

        occsobj = organism_api.get_occurrences_range(mint=mint, maxt=maxt)
        occurrences = occsobj.get_list()

        # Always add active (but not snoozed) alarms if time interval includes
        # current time
        if mint <= now <= maxt:
            occurrences.extend(occsobj.get_active_list())

        def compare(c):
            return c['start']

        occurrences.sort(key=compare)

        if max_:
            occurrences = occurrences[:max_]

        self.occs = {}

        # Defining an itemDataMap dictionary is required by ColumnSorterMixin
        self.list_.itemDataMap = {}

        # Create an alias for self.itemDataMap to save it from any future
        # attribute renaming
        self.datamap = self.list_.itemDataMap

        self.list_.DeleteAllItems()

        for i, o in enumerate(occurrences):
            self.insert_occurrence(i, o)

        next_completion = occsobj.get_next_completion_time()

        # Note that this does *not* use
        # organism_timer_api.search_next_occurrences which would signal
        # search_next_occurrences_event, thus making this very method recur
        # infinitely
        nextoccs = organism_timer_api.get_next_occurrences(base_time=maxt)

        # Note that next_occurrence could even be a time of an occurrence that's
        # already displayed in the list (e.g. if an occurrence has a start time
        # within the queried range but an end time later than the maximum end)
        next_occurrence = nextoccs.get_next_occurrence_time()

        delays = []

        try:
            # At completion time, because of the approximation, next_completion
            # and mint are the same, thus giving a difference of 0: this would
            # refresh the tasklist repeatedly until the following second
            # strikes, so adding 1 here will make the previous cycle refresh the
            # tasklist 1 second after completion time, thus giving the expected
            # behaviour. Note that using max(((next_completion - mint), 1))
            # would give a worse behaviour, in fact the tasklist would always be
            # refreshed twice, the first time after 1 second, and the second
            # time after the correct delay
            d1 = next_completion - mint + 1
        except TypeError:
            # next_completion could be None
            pass
        else:
            delays.append(d1)

        try:
            # Note that, unlike before, next_occurrence is always greater than
            # maxt, so this difference will never be 0
            d2 = next_occurrence - maxt
        except TypeError:
            # next_occurrence could be None
            pass
        else:
            delays.append(d2)

        return delays

    def insert_occurrence(self, i, occ):
        filename = occ['filename']
        id_ = occ['id_']
        start = occ['start']
        end = occ['end']
        alarm = occ['alarm']

        self.occs[i] = ListItem(filename, id_, start, end, alarm)

        fname = os.path.basename(filename)
        text = core_api.get_item_text(filename, id_)
        title = ListItem.make_heading(text)
        startdate = _time.strftime('%Y.%m.%d %H:%M', _time.localtime(start))
        if isinstance(end, int):
            enddate = _time.strftime('%Y.%m.%d %H:%M', _time.localtime(end))
        else:
            enddate = 'none'
        if isinstance(alarm, int):
            alarmdate = _time.strftime('%Y.%m.%d %H:%M',
                                       _time.localtime(alarm))
        else:
            alarmdate = 'none'

        # Both the key and the values of this dictionary must comply with the
        # requirements of ColumnSorterMixin
        self.datamap[i] = (fname, title, startdate, enddate, alarmdate)

        index = self.list_.InsertStringItem(sys.maxint, fname)
        self.list_.SetStringItem(index, 1, title)
        self.list_.SetStringItem(index, 2, startdate)
        self.list_.SetStringItem(index, 3, enddate)
        self.list_.SetStringItem(index, 4, alarmdate)
        # In order for ColumnSorterMixin to work, all items must have a unique
        # data value
        self.list_.SetItemData(index, i)


class ListItem():
    filename = None
    id_ = None
    start = None
    end = None
    alarm = None

    def __init__(self, filename, id_, start, end, alarm):
        self.filename = filename
        self.id_ = id_
        self.start = start
        self.end = end
        self.alarm = alarm

    @staticmethod
    def make_heading(text):
        return text.partition('\n')[0]


def main():
    nb = wxgui_api.get_right_nb()
    wxgui_api.add_plugin_to_right_nb(TaskList(nb).list_, 'List', close=False)
