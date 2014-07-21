# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2014 Dario Giovannetti <dev@dariogiovannetti.net>
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
import datetime as _datetime
import os
import string as string_

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import log
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api

import filters
import menus
import msgboxes
from exceptions import OutOfRangeError


class ListView(wx.ListView, ListCtrlAutoWidthMixin, ColumnSorterMixin):
    def __init__(self, parent, colsn):
        wx.ListView.__init__(self, parent, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)
        ColumnSorterMixin.__init__(self, colsn)

        self._set_image_lists()

    def GetListCtrl(self):
        return self

    def _set_image_lists(self):
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


class OccurrencesView(object):
    def __init__(self, tasklist, navigator):
        self.DATABASE_COLUMN = 0
        self.HEADING_COLUMN = 1
        self.START_COLUMN = 2
        self.DURATION_COLUMN = 3
        self.END_COLUMN = 4
        self.STATE_COLUMN = 5
        self.ALARM_COLUMN = 6
        COLUMNS_NUMBER = 7

        self.tasklist = tasklist
        self.navigator = navigator
        self.listview = ListView(tasklist.panel, COLUMNS_NUMBER)

        # Override ColumnSorterMixin's method for sorting items that have equal
        # primary sort value
        self.listview.GetSecondarySortValues = self._get_secondary_sort_values

        config = coreaux_api.get_plugin_configuration('wxtasklist')

        # No need to validate the values, as they are reset every time the
        # application is closed, and if a user edits them manually he knows
        # he's done something wrong in the configuration file
        self.listview.InsertColumn(self.DATABASE_COLUMN, 'Database',
                                    width=config.get_int('database_column'))
        self.listview.InsertColumn(self.HEADING_COLUMN, 'Heading',
                                        width=config.get_int('heading_column'))
        self.listview.InsertColumn(self.START_COLUMN, 'Start',
                                        width=config.get_int('start_column'))
        self.listview.InsertColumn(self.DURATION_COLUMN, 'Duration',
                                    width=config.get_int('duration_column'))
        self.listview.InsertColumn(self.END_COLUMN, 'End',
                                            width=config.get_int('end_column'))
        self.listview.InsertColumn(self.STATE_COLUMN, 'State',
                                        width=config.get_int('state_column'))
        self.listview.InsertColumn(self.ALARM_COLUMN, 'Alarm',
                                        width=config.get_int('alarm_column'))

        # Initialize sort column and order *before* enabling the autoscroll
        self.listview.SortListItems(self.STATE_COLUMN, 1)

        self.autoscroll = Autoscroll(self, self.listview,
                    config.get_int('autoscroll_padding'), self.STATE_COLUMN)

        if config.get_bool('autoscroll'):
            # Autoscroll is instantiated as disabled, so there's no need for an
            # else clause
            self.autoscroll.enable()

        self.filterlimits = (
            int(_time.mktime(_datetime.datetime(config.get_int('minimum_year'),
                                                        1, 1).timetuple())),
            int(_time.mktime(_datetime.datetime(
                    config.get_int('maximum_year') + 1, 1, 1).timetuple())) - 1
        )

        self.filterclasses = {
            'relative': filters.FilterRelative,
            'date': filters.FilterDate,
            'month': filters.FilterMonth,
        }

        try:
            self.set_filter(self.navigator.get_current_configuration())
        except OutOfRangeError:
            self.set_filter(self.navigator.get_default_configuration())

        self._set_colors(config)

        # Do not self.listview.setResizeColumn(2) because it gives a
        # non-standard feeling; the last column is auto-resized by default

        self.DELAY = config.get_int('refresh_delay')
        self.startformat = config['start_format']
        self.endformat = config['end_format']
        self.alarmformat = config['alarm_format']

        if self.endformat == 'start':
            self.endformat = self.startformat

        if self.alarmformat == 'start':
            self.alarmformat = self.startformat

        if config['database_format'] == 'full':
            self.format_database = self._format_database_full
        else:
            self.format_database = self._format_database_short

        if config['duration_format'] == 'compact':
            self.format_duration = self._format_duration_compact
        else:
            self.format_duration = self._format_duration_expanded

        self.active_alarms_modes = {
            'in_range': lambda mint, now, maxt: False,
            'auto': lambda mint, now, maxt: mint <= now <= maxt,
            'all': lambda mint, now, maxt: True,
        }
        self.active_alarms_mode = config['active_alarms']

        self.show_gaps = config.get_bool('show_gaps')
        self.show_overlappings = config.get_bool('show_overlappings')

        self.timer = wx.CallLater(0, self._restart)
        # Initialize self.timerdelay with a dummy function (int)
        self.timerdelay = wx.CallLater(self.DELAY, int)

        self.enable_refresh()

        self.listview.Bind(wx.EVT_CONTEXT_MENU, self._popup_context_menu)

    def _init_context_menu(self, mainmenu):
        self.cmenu = menus.ListContextMenu(self.tasklist, mainmenu)

    def _get_secondary_sort_values(self, col, key1, key2):
        return (self.datamap[key1][2], self.datamap[key2][2])

    def _set_colors(self, config):
        system = self.listview.GetTextColour()
        colpast = config['color_past']
        colongoing = config['color_ongoing']
        colfuture = config['color_future']
        colactive = config['color_active']
        colgap = config['color_gap']
        coloverlap = config['color_overlapping']
        self.colors = {}

        if colpast == 'system':
            self.colors['past'] = system
        elif colpast == 'auto':
            DIFF = 64
            avg = (system.Red() + system.Green() + system.Blue()) // 3

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

        self.colors['gap'] = colgap
        self.colors['overlapping'] = coloverlap

    def _delay_restart_on_text_update(self, kwargs):
        if kwargs['text'] is not None:
            self.delay_restart()

    def enable_refresh(self):
        core_api.bind_to_update_item(self._delay_restart_on_text_update)
        # The old occurrences are searched on a separate thread, so they may be
        # found *after* the next occurrences, so _delay_restart must be bound
        # to this one too
        organism_timer_api.bind_to_activate_occurrences_range(
                                                        self._delay_restart)
        # Note that self.delay_restart is *not* bound to
        # organism_timer_api.bind_to_get_next_occurrences which is signalled by
        # self._refresh signal because of the call to
        # organism_timer_api.get_next_occurrences, otherwise this would make
        # self._refresh recur infinitely
        organism_timer_api.bind_to_search_next_occurrences(self._delay_restart)
        organism_alarms_api.bind_to_alarm_off(self._delay_restart)

    def disable_refresh(self):
        # Do not even think of disabling refreshing when the notebook tab is
        # not selected, because then it should always be refreshed when
        # selecting it, which would make everything more sluggish
        core_api.bind_to_update_item(self._delay_restart_on_text_update, False)
        organism_timer_api.bind_to_activate_occurrences_range(
                                                    self._delay_restart, False)
        organism_timer_api.bind_to_search_next_occurrences(self._delay_restart,
                                                                        False)
        organism_alarms_api.bind_to_alarm_off(self._delay_restart, False)

    def _delay_restart(self, kwargs):
        # self.delay_restart uses wx.CallLater, which cannot be called from
        # other threads than the main one
        wx.CallAfter(self.delay_restart)

    def delay_restart(self):
        # Instead of self._restart, bind _this_ function to events that can be
        # signalled many times in a loop, so that self._restart is executed
        # only once after the last signal
        self.timerdelay.Stop()
        self.timerdelay = wx.CallLater(self.DELAY, self._restart)

    def _restart(self):
        self.timer.Stop()

        # This method is called with CallLater, so this may cause race bugs;
        # for example it's possible that, when closing the application, this
        # method is called when closing the last database, but when it's
        # actually executed the tasklist has already been destroyed
        if self.listview:
            delay = self._refresh()

            if delay is not None:
                # delay may become too big (long instead of int), limit it to
                # 24h
                # This has also the advantage of limiting the drift of the
                # timer
                try:
                    self.timer.Restart(delay * 1000)
                except OverflowError:
                    delay = min(86400000, sys.maxint)
                    self.timer.Restart(delay)

                # Log after the try-except block because the delay can still be
                # modified there
                log.debug('Next tasklist refresh in {} seconds'.format(delay))

    def set_filter(self, config):
        self.autoscroll.pre_execute()
        self.filter_ = self.filterclasses[config['mode']](config)

    def _refresh(self):
        log.debug('Refresh tasklist')

        self.now = int(_time.time())

        try:
            self.min_time, self.max_time = self.filter_.compute_limits(
                                                                    self.now)
        except OutOfRangeError:
            msgboxes.warn_out_of_range().ShowModal()
        else:
            if self.min_time < self.filterlimits[0] or \
                                        self.max_time > self.filterlimits[1]:
                msgboxes.warn_out_of_range().ShowModal()
            else:
                return self._refresh_continue()

    def _refresh_continue(self):
        search = organism_api.get_occurrences_range(mint=self.min_time,
                maxt=self.max_time, filenames=core_api.get_open_databases())
        search.start()
        occsobj = search.get_results()
        occurrences = occsobj.get_list()

        # Always add active (but not snoozed) alarms if time interval includes
        # current time
        if self.active_alarms_modes[self.active_alarms_mode](self.min_time,
                                                    self.now, self.max_time):
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

        self._prepare_time_allocation()

        if self.listview.GetItemCount() > 0:
            # Save the scroll y for restoring it after inserting the items
            # I could instead save
            #   self.listview.GetItemData(self.listview.GetTopItem()), but in
            #   case that disappears or moves in the list, the thing should
            #   start being complicated, and probably even confusing for the
            #   user
            # Note that self.listview.GetItemRect(0).GetY() gives a slightly
            # wrong value
            yscroll = abs(self.listview.GetItemPosition(0).y)
            self.listview.DeleteAllItems()
        else:
            yscroll = 0

        self._insert_items(occurrences)

        # Do this *after* inserting the items but *before* sorting
        self.insert_gaps_and_overlappings()

        # Use SortListItems instead of occurrences.sort(), so that the heading
        # will properly display the arrow icon
        # Using (-1, -1) will preserve the current sort column and order
        self.listview.SortListItems(-1, -1)

        # The list must be autoscrolled *after* sorting the items, so that the
        # correct y values will be got
        self.autoscroll.execute(yscroll)

        return self.filter_.compute_delay(occsobj, self.now, self.min_time,
                                                                self.max_time)

    def _insert_items(self, occurrences):
        for i, o in enumerate(occurrences):
            self.occs[i] = ListItem(i, o, self, self.listview)

            # Both the key and the values of self.datamap must comply with the
            # requirements of ColumnSorterMixin
            self.datamap[i] = self.occs[i].get_values()

            self.states[self.occs[i].get_state()].append(i)

    def _prepare_time_allocation(self):
        if self.show_gaps or self.show_overlappings:
            # Bit array that stores the minutes occupied by at least an
            # occurrence
            self.time_allocation = 0

            # Bit array that stores the minutes occupied by at least two
            # occurrences
            self.time_allocation_overlap = 0

            self.compute_time_allocation = self._compute_time_allocation_real
            self.insert_gaps_and_overlappings = \
                                        self._insert_gaps_and_overlappings_real
        else:
            self.compute_time_allocation = self._compute_time_allocation_dummy
            self.insert_gaps_and_overlappings = \
                                    self._insert_gaps_and_overlappings_dummy

    def _compute_time_allocation_real(self, start, end):
        # Don't even think of using the duration calculated for the occurrence,
        # since part of it may be out of the interval
        # The occurrence could span outside of the interval, for example if
        # it's been retrieved because its alarm time is in the interval instead
        # If end is None the following test will never be True
        # Also consider start == self.max_time, in accordance with the
        # behaviour of the occurrence search algorithm
        if start <= self.max_time and end > self.min_time:
            minr = max((start - self.min_time, 0)) // 60
            # Add 1 to self.max_time because if an occurrence is exceeding it,
            # it *is* occupying that minute too
            maxr = (min((end, self.max_time + 60)) - self.min_time) // 60
            interval = maxr - minr
            occrarr = 2 ** interval - 1
            occarr = occrarr << minr
            occoverlap = self.time_allocation & occarr
            self.time_allocation |= occarr
            self.time_allocation_overlap |= occoverlap

    def _compute_time_allocation_dummy(self, start, end):
        pass

    def _insert_gaps_and_overlappings_real(self):
        # Don't find gaps/overlappings for occurrences out of the search
        # interval, e.g. old active alarms
        # Add 1 minute to self.max_time (and hence to the whole interval)
        # because that minute is *included* in the occurrence search interval
        interval = (self.max_time + 60 - self.min_time) // 60

        if self.show_gaps:
            gaps = '{:b}'.format(self.time_allocation).zfill(interval
                                ).translate(string_.maketrans("10","01"))[::-1]
            self._find_gaps_or_overlappings(gaps,self._insert_gap)

        if self.show_overlappings:
            overlappings = '{:b}'.format(self.time_allocation_overlap).zfill(
                                                                interval)[::-1]
            self._find_gaps_or_overlappings(overlappings,
                                                    self._insert_overlapping)

    def _insert_gaps_and_overlappings_dummy(self):
        pass

    def _find_gaps_or_overlappings(self, bitstring, call):
        maxend = False

        # Find a gap/overlapping at the beginning of the interval separately
        if bitstring[0] == '1':
            bitstart = 0

            try:
                bitend = bitstring.index('10', bitstart) + 1
            except ValueError:
                bitend = len(bitstring)
                maxend = True

            call(bitstart, bitend, True, maxend)
        else:
            bitend = 0

        while True:
            try:
                bitstart = bitstring.index('01', bitend) + 1
            except ValueError:
                break
            else:
                try:
                    bitend = bitstring.index('10', bitstart) + 1
                except ValueError:
                    bitend = len(bitstring)
                    maxend = True

                call(bitstart, bitend, False, maxend)

    def _insert_gap(self, mstart, mend, minstart, maxend):
        i = len(self.occs)
        start = mstart * 60 + self.min_time
        end = mend * 60 + self.min_time

        self.occs[i] = ListAuxiliaryItem(i, '[gap]', start, end, minstart,
                            maxend, self.colors['gap'], self, self.listview)

        # Both the key and the values of self.datamap must comply with the
        # requirements of ColumnSorterMixin
        self.datamap[i] = self.occs[i].get_values()

        self.states[self.occs[i].get_state()].append(i)

    def _insert_overlapping(self, mstart, mend, minstart, maxend):
        i = len(self.occs)
        start = mstart * 60 + self.min_time
        end = mend * 60 + self.min_time

        self.occs[i] = ListAuxiliaryItem(i, '[overlapping]', start, end,
            minstart, maxend, self.colors['overlapping'], self, self.listview)

        # Both the key and the values of self.datamap must comply with the
        # requirements of ColumnSorterMixin
        self.datamap[i] = self.occs[i].get_values()

        self.states[self.occs[i].get_state()].append(i)

    def _popup_context_menu(self, event):
        self.cmenu.update()
        self.listview.PopupMenu(self.cmenu)

    def add_active_alarm(self, filename, id_, alarmid):
        try:
            self.activealarms[filename]
        except KeyError:
            self.activealarms[filename] = {id_: []}
        else:
            try:
                self.activealarms[filename][id_]
            except KeyError:
                self.activealarms[filename][id_] = []

        self.activealarms[filename][id_].append(alarmid)

    def get_selected_active_alarms(self):
        sel = self.listview.GetFirstSelected()
        alarmsd = {}

        while sel > -1:
            item = self.occs[self.listview.GetItemData(sel)]
            filename = item.filename
            id_ = item.id_

            # Do not simply check if item.filename is None because that could
            # be true not only for ListAuxiliaryItem instances, but also for
            # ListItem instances that are not active alarms
            if item.alarmid is not None:
                try:
                    alarmsd[filename]
                except KeyError:
                    alarmsd[filename] = {id_: []}
                else:
                    try:
                        alarmsd[filename][id_]
                    except KeyError:
                        alarmsd[filename][id_] = []

                alarmsd[filename][id_].append(item.alarmid)

            sel = self.listview.GetNextSelected(sel)

        return alarmsd

    def get_states(self):
        return self.states

    def save_configuration(self):
        config = coreaux_api.get_plugin_configuration('wxtasklist')

        config['database_column'] = str(self.listview.GetColumnWidth(
                                                        self.DATABASE_COLUMN))
        config['heading_column'] = str(self.listview.GetColumnWidth(
                                                        self.HEADING_COLUMN))
        config['start_column'] = str(self.listview.GetColumnWidth(
                                                            self.START_COLUMN))
        config['duration_column'] = str(self.listview.GetColumnWidth(
                                                        self.DURATION_COLUMN))
        config['end_column'] = str(self.listview.GetColumnWidth(
                                                            self.END_COLUMN))
        config['state_column'] = str(self.listview.GetColumnWidth(
                                                            self.STATE_COLUMN))
        config['alarm_column'] = str(self.listview.GetColumnWidth(
                                                            self.ALARM_COLUMN))
        config['active_alarms'] = self.active_alarms_mode
        config['show_gaps'] = 'yes' if self.show_gaps else 'no'
        config['show_overlappings'] = 'yes' if self.show_overlappings else 'no'
        config['autoscroll'] = 'on' if self.autoscroll.is_enabled() else 'off'

    @staticmethod
    def _format_database_short(filename):
        return os.path.basename(filename)

    @staticmethod
    def _format_database_full(filename):
        return filename

    @staticmethod
    def _format_duration_compact(duration):
        if duration % 604800 == 0:
            return '{} weeks'.format(str(duration // 604800))
        elif duration % 86400 == 0:
            return '{} days'.format(str(duration // 86400))
        elif duration % 3600 == 0:
            return '{} hours'.format(str(duration // 3600))
        elif duration % 60 == 0:
            return '{} minutes'.format(str(duration // 60))

    @staticmethod
    def _format_duration_expanded(duration):
        strings = []
        w, r = divmod(duration, 604800)
        d, r = divmod(r, 86400)
        h, r = divmod(r, 3600)
        m = r // 60

        if w > 0:
            strings.append('{}w'.format(str(w)))

        if d > 0:
            strings.append('{}d'.format(str(d)))

        if h > 0:
            strings.append('{}h'.format(str(h)))

        if m > 0:
            strings.append('{}m'.format(str(m)))

        return ' '.join(strings)


class Autoscroll(object):
    def __init__(self, occview, listview, padding, state_column):
        self.occview = occview
        self.listview = listview
        self.padding = padding
        self.state_column = state_column
        self.enabled = False

        core_api.bind_to_open_database_dirty(self._pre_execute)
        wxgui_api.bind_to_close_database(self._pre_execute)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def is_enabled(self):
        return self.enabled

    def _pre_execute(self, kwargs):
        self.pre_execute()

    def pre_execute(self):
        if self.enabled:
            column, ascending = self.listview.GetSortState()

            if column == self.state_column and ascending == 1:
                self.execute = self._execute_auto
            else:
                self.execute = self._execute_maintain
        else:
            # When changing filter or opening/closing a database, do not
            # restore the y scroll from the previous filter
            self.execute = self._execute_dummy

    def execute(self, yscroll):
        # This function is defined dynamically
        pass

    def _execute_auto(self, yscroll):
        # This method must get the same arguments as the other execute_*
        # methods
        pastn = len(self.occview.get_states()['past'])

        if self.listview.GetItemCount() > 0:
            # Note that the autoscroll relies on the items to be initially
            # sorted by State ascending
            top = self.listview.GetTopItem()
            height = self.listview.GetItemRect(top).GetHeight()

            # If given a negative dy, ScrollList doesn't work if abs(dy) is
            # less than the current y position (cannot scroll "over the top",
            # or to negative item indices).
            scroll = max(pastn - self.padding, 0)
            yscrollauto = (scroll - top) * height
            self.listview.ScrollList(0, yscrollauto)

        self.execute = self._execute_maintain

    def _execute_dummy(self, yscroll):
        # This method must get the same arguments as the other execute_*
        # methods
        self.execute = self._execute_maintain

    def _execute_maintain(self, yscroll):
        # This method must get the same arguments as the other execute_*
        # methods
        # For some reason it doesn't work without CallAfter...
        wx.CallAfter(self.listview.ScrollList, 0, yscroll)

    def execute_force(self):
        self.listview.SortListItems(self.state_column, 1)
        self._execute_auto(None)


class ListItem(object):
    def __init__(self, i, occ, occview, listview):
        self.filename = occ['filename']
        self.id_ = occ['id_']
        self.start = occ['start']
        self.end = occ['end']
        self.alarm = occ['alarm']

        # Initialize the first column with an empty string
        index = listview.InsertStringItem(sys.maxint, '')

        self.fname = occview.format_database(self.filename)

        mnow = occview.now // 60 * 60

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
        self.title = self._make_heading(text)

        startdate = _time.strftime(occview.startformat, _time.localtime(
                                                                self.start))

        if self.end is not None:
            enddate = _time.strftime(occview.endformat, _time.localtime(
                                                                    self.end))
            self.duration = self.end - self.start
            durationstr = occview.format_duration(self.duration)
        else:
            enddate = ''
            self.duration = None
            durationstr = ''

        if self.alarm is None:
            alarmdate = ''
            self.alarmid = None
        elif self.alarm is False:
            alarmdate = 'active'
            self.alarmid = occ['alarmid']
            occview.add_active_alarm(self.filename, self.id_, self.alarmid)
            # Note that the assignment of the active color must come after any
            # previous color assignment, in order to override them
            listview.SetItemTextColour(index, occview.colors['active'])
        # Note that testing if isinstance(self.alarm, int) *before* testing if
        # self.alarm is False would return True also when self.alarm is False!
        else:
            alarmdate = _time.strftime(occview.alarmformat, _time.localtime(
                                                                   self.alarm))
            self.alarmid = None

        listview.SetStringItem(index, occview.DATABASE_COLUMN, self.fname)
        listview.SetStringItem(index, occview.HEADING_COLUMN, self.title)
        listview.SetStringItem(index, occview.START_COLUMN, startdate)
        listview.SetStringItem(index, occview.DURATION_COLUMN, durationstr)
        listview.SetStringItem(index, occview.END_COLUMN, enddate)
        listview.SetStringItem(index, occview.STATE_COLUMN, self.state)
        listview.SetStringItem(index, occview.ALARM_COLUMN, alarmdate)

        # In order for ColumnSorterMixin to work, all items must have a unique
        # data value
        listview.SetItemData(index, i)

        occview.compute_time_allocation(self.start, self.end)

    def get_values(self):
        # These values must comply with the requirements of ColumnSorterMixin
        return (self.fname, self.title, self.start, self.duration, self.end,
                                                    self.stateid, self.alarm)

    def get_state(self):
        return self.state

    @staticmethod
    def _make_heading(text):
        return text.partition('\n')[0]


class ListAuxiliaryItem(object):
    def __init__(self, i, title, start, end, minstart, maxend, color, occview,
                                                                    listview):
        self.filename = None
        self.id_ = None
        self.fname = ''
        self.title = title
        self.start = start
        self.end = end
        self.alarm = None
        self.alarmid = None

        # Initialize the first column with an empty string
        index = listview.InsertStringItem(sys.maxint, '')

        mnow = occview.now // 60 * 60

        if mnow < self.start:
            self.state = 'future'
            self.stateid = 2
        elif self.start <= mnow < self.end:
            self.state = 'ongoing'
            self.stateid = 1
        else:
            self.state = 'past'
            self.stateid = 0

        listview.SetItemTextColour(index, color)

        if minstart:
            # Don't show the start date if the gap/overlapping is at the
            # beginning of the search interval, otherwise it should be updated
            # every minute
            startdate = ''
        else:
            startdate = _time.strftime(occview.startformat, _time.localtime(
                                                                self.start))

        # Do *not* merge this check with the others for minstart (above) and
        # maxend (below)
        if minstart or maxend:
            # Don't show the duration if the gap/overlapping is at the start or
            # the end of the search interval, otherwise it should be updated
            # every minute
            self.duration = None
            durationstr = ''
        else:
            self.duration = self.end - self.start
            durationstr = occview.format_duration(self.duration)

        if maxend:
            # Don't show the end date if the gap/overlapping is at the end of
            # the search interval, otherwise it should be updated every minute
            enddate = ''
        else:
            enddate = _time.strftime(occview.endformat,
                                                    _time.localtime(self.end))

        alarmdate = ''

        listview.SetStringItem(index, occview.DATABASE_COLUMN, self.fname)
        listview.SetStringItem(index, occview.HEADING_COLUMN, self.title)
        listview.SetStringItem(index, occview.START_COLUMN, startdate)
        listview.SetStringItem(index, occview.DURATION_COLUMN, durationstr)
        listview.SetStringItem(index, occview.END_COLUMN, enddate)
        listview.SetStringItem(index, occview.STATE_COLUMN, self.state)
        listview.SetStringItem(index, occview.ALARM_COLUMN, alarmdate)

        # In order for ColumnSorterMixin to work, all items must have a unique
        # data value
        listview.SetItemData(index, i)

    def get_values(self):
        # These values must comply with the requirements of ColumnSorterMixin
        return (self.fname, self.title, self.start, self.duration, self.end,
                                                    self.stateid, self.alarm)

    def get_state(self):
        return self.state
