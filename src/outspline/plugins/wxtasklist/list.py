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
import threading

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import log
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api

import filters
import menus
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

        self.AssignImageList(self.imagelistsmall, wx.IMAGE_LIST_SMALL)

    def GetSortImages(self):
        return (self.imagemap['small']['sortup'],
                                            self.imagemap['small']['sortdown'])


class OccurrencesView(object):
    def __init__(self, tasklist, navigator):
        self.tasklist = tasklist
        self.navigator = navigator

        self.occs = []

        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

        self._init_list()

        formatter = Formatter(self.config, self.listview)
        self.refengine = RefreshEngine(self.config, self, formatter, self.occs,
                                                                self.datamap)

        self._init_autoscroll()
        self._init_filters()
        self._init_show_options()

        # RefreshEngine needs the filter and show options to be set before
        # being started
        self.refengine.pre_enable()

    def _init_list(self):
        self.DATABASE_COLUMN = 0
        self.HEADING_COLUMN = 1
        self.START_COLUMN = 2
        self.DURATION_COLUMN = 3
        self.END_COLUMN = 4
        self.STATE_COLUMN = 5
        self.ALARM_COLUMN = 6
        COLUMNS_COUNT = 7

        self.listview = ListView(self.tasklist.panel, COLUMNS_COUNT)

        # Override ColumnSorterMixin's method for sorting items that have equal
        # primary sort value
        self.listview.GetSecondarySortValues = self._get_secondary_sort_values

        # Defining an itemDataMap dictionary is required by ColumnSorterMixin
        self.listview.itemDataMap = {}
        # Create an alias for self.itemDataMap to save it from any future
        # attribute renaming
        self.datamap = self.listview.itemDataMap

        # No need to validate the values, as they are reset every time the
        # application is closed, and if a user edits them manually he knows
        # he's done something wrong in the configuration file
        self.listview.InsertColumn(self.DATABASE_COLUMN, 'Database',
                        width=self.config('ColumnWidths').get_int('database'))
        self.listview.InsertColumn(self.HEADING_COLUMN, 'Heading',
                        width=self.config('ColumnWidths').get_int('heading'))
        self.listview.InsertColumn(self.START_COLUMN, 'Start',
                        width=self.config('ColumnWidths').get_int('start'))
        self.listview.InsertColumn(self.DURATION_COLUMN, 'Duration',
                        width=self.config('ColumnWidths').get_int('duration'))
        self.listview.InsertColumn(self.END_COLUMN, 'End',
                        width=self.config('ColumnWidths').get_int('end'))
        self.listview.InsertColumn(self.STATE_COLUMN, 'State',
                        width=self.config('ColumnWidths').get_int('state'))
        self.listview.InsertColumn(self.ALARM_COLUMN, 'Alarm',
                        width=self.config('ColumnWidths').get_int('alarm'))

        # Initialize sort column and order *before* enabling the autoscroll
        self.listview.SortListItems(self.STATE_COLUMN, 1)

        # Do not self.listview.setResizeColumn(self.HEADING_COLUMN) because it
        # gives a non-standard feeling; the last column is auto-resized by
        # default

        self.listview.Bind(wx.EVT_CONTEXT_MENU, self._popup_context_menu)

    def _init_autoscroll(self):
        self.autoscroll = Autoscroll(self.listview, self.refengine,
                self.config.get_int('autoscroll_padding'), self.STATE_COLUMN,
                self.config.get_bool('autoscroll'))

    def _init_filters(self):
        try:
            self.set_filter(self.navigator.get_current_configuration())
        except OutOfRangeError:
            self.set_filter(self.navigator.get_default_configuration())

    def _init_show_options(self):
        self.active_alarms_modes = {
            'in_range': lambda mint, now, maxt: False,
            'auto': lambda mint, now, maxt: mint <= now <= maxt,
            'all': lambda mint, now, maxt: True,
        }

        self.active_alarms_mode = self.config['active_alarms']

        self.show_gaps = self.config.get_bool('show_gaps')
        self.show_overlappings = self.config.get_bool('show_overlappings')

    def _init_context_menu(self, mainmenu):
        self.cmenu = menus.ListContextMenu(self.tasklist, mainmenu)

    def _get_secondary_sort_values(self, col, key1, key2):
        return (self.datamap[key1][self.START_COLUMN],
                                        self.datamap[key2][self.START_COLUMN])

    def enable_refresh(self):
        self.refengine.enable()

    def disable_refresh(self):
        self.refengine.disable()

    def refresh(self):
        self.refengine.delay_restart()

    def set_filter(self, config):
        self.autoscroll.pre_execute()
        self.refengine.set_filter(config)

    def is_time_in_range(self, now, min_time, max_time):
        return self.active_alarms_modes[self.active_alarms_mode](min_time, now,
                                                                    max_time)

    def get_gaps_and_overlappings_setting(self):
        return (self.show_gaps, self.show_overlappings)

    def insert_items(self):
        # This method is always executed in the main thread, so there can't be
        # races, except for self.occs that may be re-created meanwhile, but
        # it's enough to iterate over a copy

        # Explicitly preserve the scrolled attribute of Autoscroll, because
        # DeleteAllItems generates EVT_SCROLLWIN that would always set it to
        # True
        scrolled = self.autoscroll.is_scrolled()

        # The number of items should have been limited by RefreshEngine
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

        # Iterate over a copy of self.occs because it may be changed meanwhile
        # by RefreshEngine
        for i, item in enumerate(self.occs[:]):
            # Splitting this part and calling with CallAfter directly from the
            #  engine thread every time an occurrence is added to self.occs
            #  doesn't make the interface responsive anyway, so just do
            #  everything here

            # Initialize the first column with an empty string
            index = self.listview.InsertStringItem(sys.maxint, '')
            self.listview.SetStringItem(index, self.DATABASE_COLUMN,
                                                item.get_formatted_filename())
            self.listview.SetStringItem(index, self.HEADING_COLUMN,
                                                item.get_title())
            self.listview.SetStringItem(index, self.START_COLUMN,
                                                item.get_start_date())
            self.listview.SetStringItem(index, self.DURATION_COLUMN,
                                                item.get_duration())
            self.listview.SetStringItem(index, self.END_COLUMN,
                                                item.get_end_date())
            self.listview.SetStringItem(index, self.STATE_COLUMN,
                                                item.get_state())
            self.listview.SetStringItem(index, self.ALARM_COLUMN,
                                                item.get_alarm_date())

            self.listview.SetItemTextColour(index, item.get_color())

            # In order for ColumnSorterMixin to work, all items must have a
            # unique data value
            self.listview.SetItemData(index, i)

        # Use SortListItems instead of occurrences.sort(), so that the heading
        # will properly display the arrow icon
        # Using (-1, -1) will preserve the current sort column and order
        self.listview.SortListItems(-1, -1)

        # The list must be autoscrolled *after* sorting the items, so that the
        # correct y values will be got
        self.autoscroll.set_scrolled(scrolled)
        self.autoscroll.execute(yscroll)

        self.tasklist.set_tab_icon_stopped()

    def _popup_context_menu(self, event):
        self.cmenu.update()
        self.listview.PopupMenu(self.cmenu)

    def get_shown_items_count(self):
        return self.listview.GetItemCount()

    def get_item_values_by_position(self, pos):
        return self.occs[self.listview.GetItem(pos).GetData()
                                                        ].get_export_values()

    def get_active_alarms(self):
        return self.refengine.get_active_alarms()

    def get_selected_active_alarms(self):
        sel = self.listview.GetFirstSelected()
        alarmsd = {}

        while sel > -1:
            item = self.occs[self.listview.GetItemData(sel)]
            filename = item.get_filename()
            id_ = item.get_id()
            alarmid = item.get_alarm_id()

            # Do not simply check if item.filename is None because that could
            # be true not only for ListAuxiliaryItem instances, but also for
            # ListItem instances that are not active alarms
            if alarmid is not None:
                try:
                    alarmsd[filename]
                except KeyError:
                    alarmsd[filename] = {id_: []}
                else:
                    try:
                        alarmsd[filename][id_]
                    except KeyError:
                        alarmsd[filename][id_] = []

                alarmsd[filename][id_].append(alarmid)

            sel = self.listview.GetNextSelected(sel)

        return alarmsd

    def cancel_refresh(self):
        self.refengine.cancel()

    def set_tab_icon_stopped(self):
        self.tasklist.set_tab_icon_stopped()

    def warn_limit_exceeded(self):
        self.listview.DeleteAllItems()
        self.tasklist.show_warning("Search results limit exceeded")
        self.tasklist.set_tab_icon_stopped()

    def warn_out_of_range(self):
        self.tasklist.show_warning("The search parameters are out of the "
                                                            "supported range")

    def reset_warnings(self):
        self.tasklist.set_tab_icon_ongoing()
        self.tasklist.dismiss_warning()

    def save_configuration(self):
        config = coreaux_api.get_plugin_configuration('wxtasklist')

        config('ColumnWidths')['database'] = str(self.listview.GetColumnWidth(
                                                        self.DATABASE_COLUMN))
        config('ColumnWidths')['heading'] = str(self.listview.GetColumnWidth(
                                                        self.HEADING_COLUMN))
        config('ColumnWidths')['start'] = str(self.listview.GetColumnWidth(
                                                            self.START_COLUMN))
        config('ColumnWidths')['duration'] = str(self.listview.GetColumnWidth(
                                                        self.DURATION_COLUMN))
        config('ColumnWidths')['end'] = str(self.listview.GetColumnWidth(
                                                            self.END_COLUMN))
        config('ColumnWidths')['state'] = str(self.listview.GetColumnWidth(
                                                            self.STATE_COLUMN))
        config('ColumnWidths')['alarm'] = str(self.listview.GetColumnWidth(
                                                            self.ALARM_COLUMN))
        config['active_alarms'] = self.active_alarms_mode
        config['show_gaps'] = 'yes' if self.show_gaps else 'no'
        config['show_overlappings'] = 'yes' if self.show_overlappings else 'no'
        config['autoscroll'] = 'on' if self.autoscroll.is_enabled() else 'off'


class RefreshEngineStop(UserWarning):
    # This class is used as an exception, but used internally, so there's no
    # need to store it in the exceptions module
    pass


class RefreshEngineLimit(UserWarning):
    # This class is used as an exception, but used internally, so there's no
    # need to store it in the exceptions module
    pass


class RefreshEngine(object):
    def __init__(self, config, occview, formatter, occs, datamap):
        self.occview = occview
        self.formatter = formatter
        self.occs = occs
        self.datamap = datamap
        self.activealarms = {}
        self.TIMER_NAME = "wxtasklist_engine"
        self.DELAY = config.get_int('refresh_delay')
        self.LIMIT = config.get_int('maximum_items')
        self.pastN = 0

        self.filterclasses = {
            'relative': filters.FilterRelative,
            'date': filters.FilterDate,
            'month': filters.FilterMonth,
        }

        self.filterlimits = (
            int(_time.mktime(_datetime.datetime(
                    config.get_int('minimum_year'), 1, 1).timetuple())),
            int(_time.mktime(_datetime.datetime(
                    config.get_int('maximum_year') + 1, 1, 1).timetuple())) - 1
        )

    def pre_enable(self):
        # Initialize self.timerdelay with a dummy function (int)
        self.timerdelay = wx.CallLater(self.DELAY, int)

        self.cancel_request = False

        # self._restart cancels the timer, so it must be initialized here,
        # instead of calling self._refresh directly
        # Call a dummy function (int) instead of self._refresh because if the
        # session manager is disabled or there aren't any databases to open,
        # the tasklist will be disabled (and hidden) and self._refresh will
        # fail
        self.timer = threading.Timer(0, int)
        self.timer.name = self.TIMER_NAME
        self.timer.start()

    def _handle_closing_database(self, kwargs):
        # There's no need to check if there are any more open compatible
        # databases, and possibly completely disable the tasklist, in fact the
        # next refresh would be very quick anyway, not finding any occurrences
        # Anyway, in case it was implemented in the future, remember to
        # re-enable the tasklist when opening another database
        self.cancel()

    def cancel(self):
        self.timer.cancel()

        # The timer delay may have already expired, but the called function may
        # be still executing, so we have to stop it first
        self.cancel_request = True

        try:
            self.search.stop()
        except AttributeError:
            # The search may not have been initialized yet
            pass

        self.timer.join()

        self.cancel_request = False

    def enable(self):
        core_api.bind_to_update_item(self._delay_restart_on_text_update)
        # The old occurrences are searched on a separate thread, so they may be
        # found *after* the next occurrences, so _delay_restart must be bound
        # to this one too
        organism_alarms_api.bind_to_activate_alarms_range_end(
                                                        self._delay_restart)
        # Note that self.delay_restart is *not* bound to
        # organism_timer_api.bind_to_get_next_occurrences which is signalled by
        # self._refresh signal because of the call to
        # organism_timer_api.get_next_occurrences, otherwise this would make
        # self._refresh recur infinitely
        organism_timer_api.bind_to_search_next_occurrences(self._delay_restart)
        organism_alarms_api.bind_to_alarm_off(self._delay_restart)

        core_api.bind_to_closing_database(self._handle_closing_database)

    def disable(self):
        self.cancel()

        # Do not even think of disabling refreshing when the notebook tab is
        # not selected, because then it should always be refreshed when
        # selecting it, which would make everything more sluggish
        core_api.bind_to_update_item(self._delay_restart_on_text_update, False)
        organism_alarms_api.bind_to_activate_alarms_range_end(
                                                    self._delay_restart, False)
        organism_timer_api.bind_to_search_next_occurrences(self._delay_restart,
                                                                        False)
        organism_alarms_api.bind_to_alarm_off(self._delay_restart, False)
        core_api.bind_to_closing_database(self._handle_closing_database, False)

    def set_filter(self, config):
        self.filter_ = self.filterclasses[config['mode']](config)

    def get_past_count(self):
        return self.pastN

    def get_active_alarms(self):
        return self.activealarms

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

    def _delay_restart_on_text_update(self, kwargs):
        if kwargs['text'] is not None:
            self.delay_restart()

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

    def _restart(self, delay=0):
        self.cancel()

        if delay is not None:
            # delay may become too big (long instead of int), limit it to 24h
            # This has also the advantage of limiting the drift of the timer
            delay = min(86400, delay)
            self.timer = threading.Timer(delay, self._refresh)
            self.timer.name = self.TIMER_NAME
            self.timer.start()
            log.debug('Next tasklist refresh in {} seconds'.format(delay))

    def _refresh(self):
        log.debug('Refresh tasklist')

        self.now = int(_time.time())

        try:
            self.min_time, self.max_time = self.filter_.compute_limits(
                                                                self.now)
        except OutOfRangeError:
            wx.CallAfter(self.occview.warn_out_of_range)
        else:
            if self.min_time < self.filterlimits[0] or \
                                    self.max_time > self.filterlimits[1]:
                wx.CallAfter(self.occview.warn_out_of_range)
            else:
                wx.CallAfter(self.occview.reset_warnings)
                try:
                    delay = self._refresh_continue()
                except RefreshEngineStop:
                    wx.CallAfter(self.occview.set_tab_icon_stopped)
                except RefreshEngineLimit:
                    wx.CallAfter(self.occview.warn_limit_exceeded)
                except core_api.NoLongerExistingItem:
                    self._delay_restart(kwargs=None)
                else:
                    # Since self._refresh_end (and so
                    # self.occview.insert_items) is always run in the main
                    # thread, there can't be races
                    wx.CallAfter(self._refresh_end, delay)

    def _refresh_continue(self):
        self.search = organism_api.get_occurrences_range(mint=self.min_time,
                        maxt=self.max_time,
                        filenames=organism_api.get_supported_open_databases())
        self.search.start()

        if self.cancel_request:
            raise RefreshEngineStop()

        occsobj = self.search.get_results()
        occurrences = occsobj.get_list()

        if len(occurrences) > self.LIMIT:
            raise RefreshEngineLimit()

        # Always add active (but not snoozed) alarms if time interval includes
        # current time
        if self.occview.is_time_in_range(self.now, self.min_time,
                                                                self.max_time):
            occurrences.extend(occsobj.get_active_list())

        # Don't re-assign = [] or the other live references to the object won't
        # be updated anymore (they'll still refer to the old object)
        self.occs[:] = []
        self.datamap.clear()
        self.activealarms.clear()
        self.pastN = 0

        self.timealloc = TimeAllocation(self.min_time, self.max_time,
                                                            self.occview, self)

        for occurrence in occurrences:
            self._insert_occurrence(occurrence)

        self.timealloc.insert_gaps_and_overlappings()

        delay = self.filter_.compute_delay(occsobj, self.now, self.min_time,
                                                                self.max_time)

        return delay

    def _refresh_end(self, delay):
        self.occview.insert_items()
        self._restart(delay)

    def _insert_occurrence(self, occurrence):
        item = ListRegularItem(occurrence, self, self.now, self.formatter)
        self.timealloc.compute_time_allocation(item.get_start(),
                                                                item.get_end())
        self._insert_item(item)

    def insert_gap(self, start, end, minstart, maxend):
        item = ListAuxiliaryItem('[gap]', start, end, minstart, maxend, 'gap',
                                                    self.now, self.formatter)
        self._insert_item(item)

    def insert_overlapping(self, start, end, minstart, maxend):
        item = ListAuxiliaryItem('[overlapping]', start, end, minstart, maxend,
                                    'overlapping', self.now, self.formatter)
        self._insert_item(item)

    def _insert_item(self, item):
        i = len(self.occs)
        self.occs.append(item)

        # Both the key and the values of self.datamap must comply with the
        # requirements of ColumnSorterMixin
        self.datamap[i] = item.get_comparison_values()

        self.pastN += item.get_past_count()

        # No point in inserting the item in the tasklist here with CallAfter,
        #  as it wouldn't make the interface responsive anyway


class TimeAllocation(object):
    def __init__(self, min_time, max_time, occview, refengine):
        self.min_time = min_time
        self.max_time = max_time
        self.occview = occview
        self.refengine = refengine

        self.show_gaps, self.show_overlappings = \
                            self.occview.get_gaps_and_overlappings_setting()

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

    def compute_time_allocation(self, start, end):
        # This method is assigned dynamically
        pass

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

    def insert_gaps_and_overlappings(self):
        # This method is assigned dynamically
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
            self._find_gaps_or_overlappings(gaps, self.refengine.insert_gap)

        if self.show_overlappings:
            overlappings = '{:b}'.format(self.time_allocation_overlap).zfill(
                                                                interval)[::-1]
            self._find_gaps_or_overlappings(overlappings,
                                            self.refengine.insert_overlapping)

    def _insert_gaps_and_overlappings_dummy(self):
        pass

    def _find_gaps_or_overlappings(self, bitstring, call):
        maxend = False

        # Find a gap/overlapping at the beginning of the interval separately
        if bitstring[0] == '1':
            bitstart = 0

            bitend, maxend = self._find_gaps_or_overlappings_continue(
                                    bitstring, bitstart, True, maxend, call)
        else:
            bitend = 0

        while True:
            try:
                bitstart = bitstring.index('01', bitend) + 1
            except ValueError:
                break
            else:
                bitend, maxend = self._find_gaps_or_overlappings_continue(
                                    bitstring, bitstart, False, maxend, call)

    def _find_gaps_or_overlappings_continue(self, bitstring, bitstart,
                                                    minstart, maxend, call):
        try:
            bitend = bitstring.index('10', bitstart) + 1
        except ValueError:
            bitend = len(bitstring)
            maxend = True

        start = bitstart * 60 + self.min_time
        end = bitend * 60 + self.min_time

        call(start, end, minstart, maxend)

        return (bitend, maxend)


class Formatter(object):
    def __init__(self, config, listview):
        self.config = config
        self.listview = listview
        self.startformat = config('Formats')['start']
        self.endformat = config('Formats')['end']
        self.alarmformat = config('Formats')['alarm']

        if self.endformat == 'start':
            self.endformat = self.startformat

        if self.alarmformat == 'start':
            self.alarmformat = self.startformat

        if config('Formats')['database'] == 'full':
            self.format_database = self._format_database_full
        else:
            self.format_database = self._format_database_short

        if config('Formats')['duration'] == 'compact':
            self.format_duration = self._format_duration_compact
        else:
            self.format_duration = self._format_duration_expanded

        self._init_colors()

    def _init_colors(self):
        system = self.listview.GetTextColour()
        colpast = self.config('Colors')['past']
        colongoing = self.config('Colors')['ongoing']
        colfuture = self.config('Colors')['future']
        colactive = self.config('Colors')['active']
        colgap = self.config('Colors')['gap']
        coloverlap = self.config('Colors')['overlapping']
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

    def get_start_format(self):
        return self.startformat

    def get_end_format(self):
        return self.endformat

    def get_alarm_format(self):
        return self.alarmformat

    def get_color(self, type_):
        return self.colors[type_]

    def format_database(self, filename):
        # This method is assigned dynamically
        pass

    def _format_database_short(self, filename):
        return os.path.basename(filename)

    def _format_database_full(self, filename):
        return filename

    def format_duration(self, duration):
        # This method is assigned dynamically
        pass

    def _format_duration_compact(self, duration):
        if duration % 604800 == 0:
            return '{} weeks'.format(str(duration // 604800))
        elif duration % 86400 == 0:
            return '{} days'.format(str(duration // 86400))
        elif duration % 3600 == 0:
            return '{} hours'.format(str(duration // 3600))
        elif duration % 60 == 0:
            return '{} minutes'.format(str(duration // 60))

    def _format_duration_expanded(self, duration):
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
    def __init__(self, listview, refengine, padding, state_column, enable):
        self.listview = listview
        self.refengine = refengine
        self.padding = padding
        self.state_column = state_column

        if enable:
            self.enable()
        else:
            self.disable()

        core_api.bind_to_open_database_dirty(self._pre_execute)
        wxgui_api.bind_to_close_database(self._pre_execute)

    def enable(self):
        self.enabled = True
        self.execute = self._execute_auto
        self.set_scrolled(True)

    def disable(self):
        self.enabled = False
        self.execute = self._execute_maintain
        self.set_scrolled(True)

    def is_enabled(self):
        return self.enabled

    def _pre_execute(self, kwargs):
        self.pre_execute()

    def pre_execute(self):
        # The original behavior was to autoscroll only once and then set
        # self.execute = self._execute_maintain, however after implementing the
        # threaded refresh this started suffering of race bugs, in fact it
        # could be possible that more self.pre_execute are called before a real
        # refresh is even done, which would then set
        # self.execute = self._execute_maintain and the following refreshes,
        # despite having called self.pre_execute, wouldn't autoscroll the list
        # (this for example happens when launching Outspline with a database
        # to be opened when restoring the session)
        if self.enabled:
            self.set_scrolled(False)
        else:
            self.execute = self._execute_dummy

    def _handle_scroll(self, event):
        self.set_scrolled(True)

        # Skip the event, otherwise the list won't be updated when scrolling
        event.Skip()

    def is_scrolled(self):
        return self.scrolled

    def set_scrolled(self, scrolled):
        if scrolled:
            # Use CallAfter, or a segmentation fault will happen
            wx.CallAfter(self.listview.Unbind, wx.EVT_SCROLLWIN,
                                                handler=self._handle_scroll)
        else:
            self.listview.Bind(wx.EVT_SCROLLWIN, self._handle_scroll)

        self.scrolled = scrolled

    def execute(self, yscroll):
        # This function is defined dynamically
        pass

    def _execute_auto(self, yscroll):
        # This method must get the same arguments as the other _execute_*
        # methods

        if not self.scrolled:
            # Don't even think of checking the sort state in self.pre_execute,
            # since this method is indirectly launched from a thread that in
            # turn is launched after self.pre_execute, so races may happen and
            # there would be no way to determine which self.pre_execute was
            # associated with this particular call
            column, ascending = self.listview.GetSortState()

            if column == self.state_column and ascending == 1:
                pastn = self.refengine.get_past_count()

                if self.listview.GetItemCount() > 0:
                    # Note that the autoscroll relies on the items to be
                    # initially sorted by State ascending
                    top = self.listview.GetTopItem()
                    height = self.listview.GetItemRect(top).GetHeight()

                    # If given a negative dy, ScrollList doesn't work if
                    # abs(dy) is less than the current y position (cannot
                    # scroll "over the top", or to negative item indices)
                    scroll = max(pastn - self.padding, 0)
                    yscrollauto = (scroll - top) * height
                    self.listview.ScrollList(0, yscrollauto)
            else:
                self._execute_maintain(yscroll)
        else:
            self._execute_maintain(yscroll)

    def _execute_dummy(self, yscroll):
        # This method must get the same arguments as the other _execute_*
        # methods

        # When changing filter or opening/closing a database, do not restore
        # the y scroll from the previous filter
        self.execute = self._execute_maintain

    def _execute_maintain(self, yscroll):
        # This method must get the same arguments as the other _execute_*
        # methods
        # For some reason it doesn't work without first calling GetItemPosition
        #  (?!?)
        #  Checking is then necessary because calling GetItemPosition on an
        #  empty list raises an exception
        if self.listview.GetItemCount() > 0:
            self.listview.GetItemPosition(0)
            self.listview.ScrollList(0, yscroll)

    def execute_force(self):
        self.set_scrolled(False)
        self.listview.SortListItems(self.state_column, 1)
        self._execute_auto(None)


class _ListItem(object):
    # Virtual class

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    def get_alarm(self):
        return self.alarm

    def get_alarm_id(self):
        return self.alarmid

    def get_formatted_filename(self):
        return self.fname

    def get_title(self):
        return self.title

    def get_start(self):
        return self.start

    def get_start_date(self):
        return self.startdate

    def get_duration(self):
        return self.durationstr

    def get_end(self):
        return self.end

    def get_end_date(self):
        return self.enddate

    def get_state(self):
        return self.state

    def get_alarm_date(self):
        return self.alarmdate

    def get_comparison_values(self):
        return (self.fname, self.title, self.start, self.duration, self.end,
                                                    self.stateid, self.alarm)

    def get_export_values(self):
        return {
            "filename": self.filename,
            "heading": self.title,
            "start": self.start,
            "end": self.end,
            "alarm": self.alarm,
        }

    def get_color(self):
        return self.color

    def get_past_count(self):
        return self.pastN


class ListRegularItem(_ListItem):
    def __init__(self, occ, refengine, now, formatter):
        self.filename = occ['filename']
        self.id_ = occ['id_']
        self.start = occ['start']
        self.end = occ['end']
        self.alarm = occ['alarm']

        self.fname = formatter.format_database(self.filename)

        mnow = now // 60 * 60

        if mnow < self.start:
            self.state = 'future'
            self.stateid = 2
            self.pastN = 0
            self.color = formatter.get_color('future')
        # If end is None, as soon as the start time arrives, the
        # occurrence is finished, so it can't have an 'ongoing' state and has
        # to be be immediately marked as 'past'
        # Besides, if an 'ongoing' state was set, e.g. for 1 minute from the
        # start, the dynamic filter should be able to calculate the time to
        # refresh the list in order to mark the occurrence as 'past', which
        # wouldn't happen with the current implementation
        # There's no need to test if end is None here, as mnow can be <
        # end only if end is not None
        elif self.start <= mnow < self.end:
            self.state = 'ongoing'
            self.stateid = 1
            self.pastN = 0
            self.color = formatter.get_color('ongoing')
        else:
            self.state = 'past'
            self.stateid = 0
            self.pastN = 1
            self.color = formatter.get_color('past')

        text = core_api.get_item_text(self.filename, self.id_)
        self.title = text.partition('\n')[0]

        self.startdate = _time.strftime(formatter.get_start_format(),
                                                _time.localtime(self.start))

        if self.end is not None:
            self.enddate = _time.strftime(formatter.get_end_format(),
                                                    _time.localtime(self.end))
            self.duration = self.end - self.start
            self.durationstr = formatter.format_duration(self.duration)
        else:
            self.enddate = ''
            self.duration = None
            self.durationstr = ''

        if self.alarm is None:
            self.alarmdate = ''
            self.alarmid = None
        elif self.alarm is False:
            self.alarmdate = 'active'
            self.alarmid = occ['alarmid']
            refengine.add_active_alarm(self.filename, self.id_, self.alarmid)
            # Note that the assignment of the active color must come after any
            # previous color assignment, in order to override them
            self.color = formatter.get_color('active')
        # Note that testing if isinstance(alarm, int) *before* testing if
        # alarm is False would return True also when alarm is False!
        else:
            self.alarmdate = _time.strftime(formatter.get_alarm_format(),
                                                _time.localtime(self.alarm))
            self.alarmid = None


class ListAuxiliaryItem(_ListItem):
    def __init__(self, title, start, end, minstart, maxend, type_, now,
                                                                    formatter):
        self.filename = None
        self.id_ = None
        self.fname = ''
        self.title = title
        self.start = start
        self.end = end
        self.alarm = None
        self.alarmid = None

        self.color = formatter.get_color(type_)

        mnow = now // 60 * 60

        if mnow < self.start:
            self.state = 'future'
            self.stateid = 2
            self.pastN = 0
        elif self.start <= mnow < self.end:
            self.state = 'ongoing'
            self.stateid = 1
            self.pastN = 0
        else:
            self.state = 'past'
            self.stateid = 0
            self.pastN = 1

        if minstart:
            # Don't show the start date if the gap/overlapping is at the
            # beginning of the search interval, otherwise it should be updated
            # every minute
            self.startdate = ''
        else:
            self.startdate = _time.strftime(formatter.get_start_format(),
                                                _time.localtime(self.start))

        # Do *not* merge this check with the others for minstart (above) and
        # maxend (below)
        if minstart or maxend:
            # Don't show the duration if the gap/overlapping is at the start or
            # the end of the search interval, otherwise it should be updated
            # every minute
            self.duration = None
            self.durationstr = ''
        else:
            self.duration = self.end - self.start
            self.durationstr = formatter.format_duration(self.duration)

        if maxend:
            # Don't show the end date if the gap/overlapping is at the end of
            # the search interval, otherwise it should be updated every minute
            self.enddate = ''
        else:
            self.enddate = _time.strftime(formatter.get_end_format(),
                                                    _time.localtime(self.end))

        self.alarmdate = ''
