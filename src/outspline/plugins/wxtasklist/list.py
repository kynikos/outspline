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
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api

import filters
import menus

COLUMNS = (
    (0, 'Database', 120),
    (1, 'Heading', 300),
    (2, 'Start', 120),
    (3, 'End', 120),
    (4, 'State', 80),
    (5, 'Alarm', 120),
)


class ListView(wx.ListView, ListCtrlAutoWidthMixin, ColumnSorterMixin):
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


class OccurrencesView():
    tasklist = None
    listview = None
    cmenu = None
    colors = None
    filter_ = None
    occs = None
    datamap = None
    states = None
    activealarms = None
    DELAY = None
    delay = None
    timer = None
    autoscroll = None

    def __init__(self, tasklist):
        self.tasklist = tasklist
        self.listview = ListView(tasklist.panel)

        self.set_filter(self.tasklist.filters.get_filter_configuration(
                                self.tasklist.filters.get_selected_filter()))

        # Override ColumnSorterMixin's method for sorting items that have equal
        # primary sort value
        self.listview.GetSecondarySortValues = self.get_secondary_sort_values

        self.set_colors()

        for col in COLUMNS:
            self.listview.InsertColumn(col[0], col[1], width=col[2])

        # Initialize sort column and order
        self.listview.SortListItems(4, 1)

        # Do not self.listview.setResizeColumn(2) because it gives a
        # non-standard feeling; the last column is auto-resized by default

        self.DELAY = coreaux_api.get_plugin_configuration('wxtasklist'
                                                     ).get_int('refresh_delay')

        # Initialize self.delay with a dummy function (int)
        self.delay = wx.CallLater(self.DELAY, int)
        self.timer = wx.CallLater(0, self.restart)

        self.enable_refresh()

        self.listview.Bind(wx.EVT_CONTEXT_MENU, self.popup_context_menu)

    def _init_context_menu(self, mainmenu):
        self.cmenu = menus.ListContextMenu(self, mainmenu)

    def get_secondary_sort_values(self, col, key1, key2):
        return (self.datamap[key1][2], self.datamap[key2][2])

    def set_colors(self):
        system = self.listview.GetTextColour()
        config = coreaux_api.get_plugin_configuration('wxtasklist')
        colpast = config['color_past']
        colongoing = config['color_ongoing']
        colfuture = config['color_future']
        colactive = config['color_active']
        self.colors = {}

        if colpast == 'system':
            self.colors['past'] = system
        elif colpast == 'auto':
            DIFF = 64
            avg = system.Red() + system.Green() + system.Blue() // 3

            if avg > 127:
                self.colors['past'] = wx.Colour(
                                              max((system.Red() - DIFF, 0)),
                                              max((system.Green() - DIFF, 0)),
                                              max((system.Blue() - DIFF, 0)))
            else:
                self.colors['past'] = wx.Colour(
                                            min((system.Red() + DIFF, 255)),
                                            min((system.Green() + DIFF, 255)),
                                            min((system.Blue() + DIFF, 255)))
        else:
            self.colors['past'] = wx.Colour()
            self.colors['past'].SetFromString(colpast)

        if colongoing == 'system':
            self.colors['ongoing'] = system
        else:
            self.colors['ongoing'] = wx.Colour()
            self.colors['ongoing'].SetFromString(colongoing)

        if colfuture == 'system':
            self.colors['future'] = system
        else:
            self.colors['future'] = wx.Colour()
            self.colors['future'].SetFromString(colfuture)

        if colactive == 'system':
            self.colors['active'] = system
        else:
            self.colors['active'] = wx.Colour()
            self.colors['active'].SetFromString(colactive)

    def delay_restart_on_text_update(self, kwargs=None):
        if kwargs['text'] is not None:
            self.delay_restart()

    def enable_refresh(self):
        core_api.bind_to_update_item(self.delay_restart_on_text_update)
        # Note that self.delay_restart is *not* bound to
        # organism_timer_api.bind_to_get_next_occurrences which is signalled by
        # self.refresh signal because of the call to
        # organism_timer_api.get_next_occurrences, otherwise this would make
        # self.refresh recur infinitely
        organism_timer_api.bind_to_search_next_occurrences(self.delay_restart)
        organism_alarms_api.bind_to_alarm_off(self.delay_restart)

    def disable_refresh(self):
        # Do not even think of disabling refreshing when the notebook tab is
        # not selected, because then it should always be refreshed when
        # selecting it, which would make everything more sluggish
        core_api.bind_to_update_item(self.delay_restart_on_text_update, False)
        organism_timer_api.bind_to_search_next_occurrences(self.delay_restart,
                                                                        False)
        organism_alarms_api.bind_to_alarm_off(self.delay_restart, False)

    def delay_restart(self, kwargs=None):
        # Instead of self.restart, bind _this_ function to events that can be
        # signalled many times in a loop, so that self.restart is executed only
        # once after the last signal
        self.delay.Stop()
        self.delay = wx.CallLater(self.DELAY, self.restart)

    def restart(self, kwargs=None):
        self.timer.Stop()
        delay = self.refresh()

        if delay is not None:
            # delay may become too big (long instead of int), limit it to 24h
            # This has also the advantage of limiting the drift of the timer
            try:
                self.timer.Restart(delay * 1000)
            except OverflowError:
                delay = min(86400000, sys.maxint)
                self.timer.Restart(delay)

            # Log after the try-except block because the delay can still be
            # modified there
            log.debug('Next tasklist refresh in {} seconds'.format(delay))

    def set_filter(self, config):
        self.autoscroll = Autoscroll(self.listview, config['autoscroll'])

        filterclasses = {
            'relative': filters.FilterRelative,
            'absolute': filters.FilterAbsolute,
            'regular': filters.FilterRegular,
            'staticmonth': filters.FilterMonthStatic,
            'month': filters.FilterMonthDynamic,
        }

        try:
            class_ = filterclasses[config['mode']]
        except KeyError:
            self.set_filter(filters.DEFAULT_FILTERS[0]['F0'])
        else:
            self.filter_ = class_(config)

    def refresh(self):
        log.debug('Refresh tasklist')

        now = int(_time.time())

        mint, maxt = self.filter_.compute_limits(now)

        occsobj = organism_api.get_occurrences_range(mint=mint, maxt=maxt)
        occurrences = occsobj.get_list()

        # Always add active (but not snoozed) alarms if time interval includes
        # current time
        if mint <= now <= maxt:
            occurrences.extend(occsobj.get_active_list())

        self.occs = {}

        # Defining an itemDataMap dictionary is required by ColumnSorterMixin
        self.listview.itemDataMap = {}

        # Create an alias for self.itemDataMap to save it from any future
        # attribute renaming
        self.datamap = self.listview.itemDataMap

        self.states = {
            'past': [],
            'ongoing': [],
            'future': [],
        }

        self.activealarms = {}

        # Save the scroll y for restoring it after inserting the items
        # I could instead save
        #   self.listview.GetItemData(self.listview.GetTopItem()), but in case
        #   that disappears or moves in the list, the thing should start being
        #   complicated, and probably even confusing for the user
        # Note that self.listview.GetItemRect(0).GetY() gives a slightly
        # wrong value
        yscroll = abs(self.listview.GetItemPosition(0).y)

        self.listview.DeleteAllItems()

        for i, o in enumerate(occurrences):
            self.occs[i] = ListItem(i, o, now, self, self.listview,
                                                               self.autoscroll)

            # Both the key and the values of self.datamap must comply with the
            # requirements of ColumnSorterMixin
            self.datamap[i] = self.occs[i].get_values()

            self.states[self.occs[i].get_state()].append(i)

        # Use SortListItems instead of occurrences.sort(), so that the heading
        # will properly display the arrow icon
        # Using (-1, -1) will preserve the current sort column and order
        self.listview.SortListItems(-1, -1)

        # The list must be autoscrolled *after* sorting the items, so that the
        # correct y values will be got
        self.autoscroll.execute(yscroll, self.states)

        return self.filter_.compute_delay(occsobj, now, mint, maxt)

    def popup_context_menu(self, event):
        self.cmenu.update()
        self.listview.PopupMenu(self.cmenu)

    def add_active_alarm(self, filename, alarmid):
        try:
            self.activealarms[filename]
        except KeyError:
            self.activealarms[filename] = []

        self.activealarms[filename].append(alarmid)

    def get_selected_active_alarms(self):
        sel = self.listview.GetFirstSelected()
        alarmsd = {}

        while sel > -1:
            item = self.occs[self.listview.GetItemData(sel)]
            filename = item.filename

            if item.alarmid is not None:
                try:
                    alarmsd[filename]
                except KeyError:
                    alarmsd[filename] = []

                alarmsd[filename].append(item.alarmid)

            sel = self.listview.GetNextSelected(sel)

        return alarmsd


class Autoscroll():
    listview = None
    padding = None
    execute = None
    height = None

    def __init__(self, listview, padding):
        self.listview = listview

        try:
            self.padding = int(padding)
        except ValueError:
            # Autoscroll disabled
            self.padding = None
            # Do not restore the y scroll from the previous filter
            self.execute = self.execute_dummy
        else:
            # Autoscroll enabled
            # Reset the scroll configuration to State ascending, which is
            # needed by the autoscroll
            self.listview.SortListItems(4, 1)
            self.execute = self.execute_auto

    def execute_auto(self, yscroll, states):
        # This height computation is tested safe even if there are no items in
        # the list
        self.height = self.listview.GetItemRect(self.listview.GetTopItem()
                                                                  ).GetHeight()

        # Note that the autoscroll relies on the items to be initially sorted
        # by State ascending
        pastn = len(states['past'])
        yscrollauto = (pastn - self.padding) * self.height
        self.listview.ScrollList(0, yscrollauto)

        # Autoscroll only once every time the filter is reset
        self.execute = self.execute_maintain

    def execute_dummy(self, yscroll, states):
        self.execute = self.execute_maintain

    def execute_maintain(self, yscroll, states):
        self.listview.ScrollList(0, yscroll)


class ListItem():
    filename = None
    id_ = None
    start = None
    end = None
    alarm = None
    alarmid = None
    fname = None
    title = None
    state = None
    stateid = None

    def __init__(self, i, occ, now, occview, listview, autoscroll):
        self.filename = occ['filename']
        self.id_ = occ['id_']
        self.start = occ['start']
        self.end = occ['end']
        self.alarm = occ['alarm']

        self.fname = os.path.basename(self.filename)
        index = listview.InsertStringItem(sys.maxint, self.fname)

        mnow = now // 60 * 60

        if mnow < self.start:
            self.state = 'future'
            self.stateid = 2
            listview.SetItemTextColour(index, occview.colors['future'])
        # If self.end is None, as soon as the start time arrives, the
        # occurrence is finished, so it can't have an 'ongoing' state and has
        # to be be immediately marked as 'past'
        # Besides, if an 'ongoing' state was set, e.g. for 1 minute from the
        # start, the dynamic filter should be able to calculate the time to
        # refresh the list in order to mark the occurrence as 'past', which
        # wouldn't happen with the current implementation
        # There's no need to test if self.end is None here, as mnow can be <
        # self.end only if self.end is not None
        elif self.start <= mnow < self.end:
            self.state = 'ongoing'
            self.stateid = 1
            listview.SetItemTextColour(index, occview.colors['ongoing'])
        else:
            self.state = 'past'
            self.stateid = 0
            listview.SetItemTextColour(index, occview.colors['past'])

        text = core_api.get_item_text(self.filename, self.id_)
        self.title = self.make_heading(text)

        startdate = _time.strftime('%Y.%m.%d %H:%M', _time.localtime(self.start
                                                                             ))

        if self.end is not None:
            enddate = _time.strftime('%Y.%m.%d %H:%M', _time.localtime(self.end
                                                                             ))
        else:
            enddate = 'none'

        if self.alarm is None:
            alarmdate = 'none'
        elif self.alarm is False:
            alarmdate = 'active'
            self.alarmid = occ['alarmid']
            occview.add_active_alarm(self.filename, self.alarmid)
            # Note that the assignment of the active color must come after any
            # previous color assignment, in order to override them
            listview.SetItemTextColour(index, occview.colors['active'])
        # Note that testing if isinstance(self.alarm, int) *before* testing if
        # self.alarm is False would return True also when self.alarm is False!
        else:
            alarmdate = _time.strftime('%Y.%m.%d %H:%M', _time.localtime(
                                                                   self.alarm))

        listview.SetStringItem(index, 1, self.title)
        listview.SetStringItem(index, 2, startdate)
        listview.SetStringItem(index, 3, enddate)
        listview.SetStringItem(index, 4, self.state)
        listview.SetStringItem(index, 5, alarmdate)

        # In order for ColumnSorterMixin to work, all items must have a unique
        # data value
        listview.SetItemData(index, i)

    def get_values(self):
        # These values must comply with the requirements of ColumnSorterMixin
        return (self.fname, self.title, self.start, self.end, self.stateid,
                                                                    self.alarm)

    def get_state(self):
        return self.state

    @staticmethod
    def make_heading(text):
        return text.partition('\n')[0]
