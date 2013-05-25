# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import sys
import time as _time
import os

import organism.coreaux_api as coreaux_api
from organism.coreaux_api import log
import organism.core_api as core_api
import organism.interfaces.wxgui_api as wxgui_api
import organism.extensions.organizer_api as organizer_api
import organism.extensions.organizer_alarms_api as organizer_alarms_api
development_api = coreaux_api.import_extension_api('development')
wxcopypaste_api = coreaux_api.import_plugin_api('wxcopypaste')


class AutoListView(wx.ListView, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        # Note that this makes use of ListView, which is an interface for
        # ListCtrl
        wx.ListView.__init__(self, parent, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)


class TaskList():
    list_ = None
    occs = None

    def __init__(self, parent):
        self.list_ = AutoListView(parent)

        self.occs = {}

        self.list_.InsertColumn(0, 'Database', width=80)
        self.list_.InsertColumn(1, 'Title', width=200)
        self.list_.InsertColumn(2, 'Start', width=120)
        self.list_.InsertColumn(3, 'End', width=120)
        self.list_.InsertColumn(4, 'Alarm', width=120)

        self.refresh()

        organizer_alarms_api.bind_to_alarms(self.handle_alarms)
        organizer_alarms_api.bind_to_alarm_off(self.handle_refresh)

        wxgui_api.bind_to_apply_editor_2(self.handle_refresh)
        wxgui_api.bind_to_open_database(self.handle_refresh)
        wxgui_api.bind_to_save_database_as(self.handle_refresh)
        wxgui_api.bind_to_close_database(self.handle_refresh)
        wxgui_api.bind_to_undo_tree(self.handle_refresh)
        wxgui_api.bind_to_redo_tree(self.handle_refresh)
        wxgui_api.bind_to_move_item(self.handle_refresh)
        wxgui_api.bind_to_delete_items(self.handle_refresh)

        if development_api:
            development_api.bind_to_populate_tree(self.handle_refresh)

        if wxcopypaste_api:
            wxcopypaste_api.bind_to_cut_items(self.handle_refresh)
            wxcopypaste_api.bind_to_paste_items(self.handle_refresh)

    def handle_alarms(self, kwargs):
        wx.CallAfter(self.refresh)

    def handle_refresh(self, kwargs):
        self.refresh()

    def refresh(self, t=None, dt=86400, max=50):
        log.debug('Tasklist refresh')

        self.occs = {}
        self.list_.DeleteAllItems()

        if t == None:
            # Always round down to the previous second
            t = int(_time.time()) - 1

        occurrences = organizer_api.get_occurrences_range(mint=t, maxt=t + dt)

        def compare(c):
            return c['start']

        occurrences.sort(key=compare)

        if max:
            occurrences = occurrences[:max]

        for i, o in enumerate(occurrences):
            filename = o['filename']
            id_ = o['id_']
            start = o['start']
            end = o['end']
            alarm = o['alarm']

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

            index = self.list_.InsertStringItem(sys.maxint, fname)
            self.list_.SetStringItem(index, 1, title)
            self.list_.SetStringItem(index, 2, startdate)
            self.list_.SetStringItem(index, 3, enddate)
            self.list_.SetStringItem(index, 4, alarmdate)


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
