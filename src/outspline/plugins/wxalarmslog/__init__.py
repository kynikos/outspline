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
# Temporary workaround for bug #279
import time as time_

import outspline.core_api as core_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api

base = None


class Main(object):
    def __init__(self):
        self.alarmlogs = {}
        self.mainmenu = LogsMenu(self)

        wxgui_api.bind_to_creating_tree(self._handle_creating_tree)
        wxgui_api.bind_to_close_database(self._handle_close_database)

    def _handle_creating_tree(self, kwargs):
        filename = kwargs['filename']

        if filename in organism_alarms_api.get_supported_open_databases():
            self.alarmlogs[filename] = AlarmsLog(wxgui_api.get_logs_parent(
                                            filename), filename, self.mainmenu)

    def _handle_close_database(self, kwargs):
        try:
            del self.alarmlogs[kwargs['filename']]
        except KeyError:
            pass

    def get_selected_log(self):
        filename = wxgui_api.get_selected_database_filename()

        try:
            return (self.alarmlogs[filename], filename)
        except KeyError:
            return (False, False)


class AlarmsLog(object):
    def __init__(self, parent, filename, mainmenu):
        self.filename = filename

        self.view = wx.dataview.DataViewListCtrl(parent,
                        style=wx.dataview.DV_MULTIPLE |
                        wx.dataview.DV_ROW_LINES | wx.dataview.DV_NO_HEADER)
        # Temporary workaround for bug #279
        # Note how AppendDateColumn requires a second argument, while
        # AppendTextColumn doesn't
        #self.view.AppendDateColumn('Timestamp', 0,
        #        width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_CENTER_VERTICAL)
        self.view.AppendTextColumn('Timestamp', width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Action', width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Item')

        self.reasons = {0: '[snoozed]',
                        1: '[dismissed]',
                        2: '[deleted]'}

        cmenu = ContextMenu(mainmenu, self.view)

        menu_items, popup_cmenu = wxgui_api.add_log(filename, self.view,
                    "Alarms", wx.ArtProvider.GetBitmap('@alarms', wx.ART_MENU),
                    cmenu.get_items(), cmenu.update)
        cmenu.store_items(menu_items)

        # Disable context menu (temporary workaround for bug #278)
        #self.view.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU,
                                                                #popup_cmenu)

        self.view.Bind(wx.dataview.EVT_DATAVIEW_ITEM_START_EDITING,
                                                    self._handle_item_editing)
        organism_alarms_api.bind_to_alarm_off(self._handle_alarm_off)
        wxgui_api.bind_to_close_database(self._handle_close_database)

        self._refresh()

    def _handle_item_editing(self, event):
        event.Veto()

    def _handle_alarm_off(self, kwargs):
        self._refresh()

    def _handle_close_database(self, kwargs):
        organism_alarms_api.bind_to_alarm_off(self._handle_alarm_off, False)

    def get_view(self):
        return self.view

    def _refresh(self):
        self.view.DeleteAllItems()

        cursor = organism_alarms_api.get_alarms_log(self.filename)

        for row in cursor:
            self.view.AppendItem(self._format_values(row),
                                                        data=row['AOL_item'])

    def _format_values(self, row):
        # Temporary workaround for bug #279
        #tstamp = wx.DateTime().SetTimeT(row['AOL_tstamp'])
        tstamp = time_.strftime('%Y-%m-%d %H:%M', time_.localtime(
                                                            row['AOL_tstamp']))
        reason = self.reasons[row['AOL_reason']]
        text = row['AOL_text']
        return (tstamp, reason, text)


class LogsMenu(object):
    def __init__(self, plugin):
        self.plugin = plugin

        self.ID_ALARMS = wx.NewId()
        self.ID_FIND = wx.NewId()

        submenu = wx.Menu()

        self.alarms = wx.MenuItem(wxgui_api.get_menu_logs(), self.ID_ALARMS,
                            '&Alarms', 'Alarms log commands', subMenu=submenu)
        self.find = wx.MenuItem(submenu, self.ID_FIND,
                "&Find in database\tCTRL+SHIFT+F6",
                "Select the database items associated to the selected entries")

        # Use an explicit accelerator (temporary workaround for bug #280)
        accel = wx.AcceleratorEntry(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_F5,
                                                                self.ID_FIND)
        accelt = wx.AcceleratorTable([accel, ])
        wx.GetApp().root.SetAcceleratorTable(accelt)

        self.alarms.SetBitmap(wx.ArtProvider.GetBitmap('@alarms', wx.ART_MENU))
        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))

        wxgui_api.add_menu_logs_item(self.alarms)
        submenu.AppendItem(self.find)

        wxgui_api.bind_to_menu(self._find_in_tree, self.find)
        wxgui_api.bind_to_reset_menu_items(self._reset_items)
        wxgui_api.bind_to_menu_logs_update(self._handle_menu_logs_update)

    def _handle_menu_logs_update(self, kwargs):
        self.find.Enable(False)

        log, filename = self.plugin.get_selected_log()

        if log:
            view = log.get_view()

            if view.IsShown():
                sel = view.GetSelectedItemsCount()

                if sel > 0:
                    self.find.Enable()

    def _reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.find.Enable()

    def _find_in_tree(self, event):
        log, filename = self.plugin.get_selected_log()

        if log:
            view = log.get_view()

            if view.IsShown():
                sel = view.GetSelections()

                if len(sel) > 0:
                    wxgui_api.unselect_all_items(filename)

                    # Do not loop directly on view.GetSelections(), e.g.
                    #   for s in view.GetSelections():
                    # because it doesn't work as expected!
                    for item in sel:
                        id_ = view.GetItemData(item)

                        # The logged item may not exist anymore
                        if core_api.is_item(filename, id_):
                            wxgui_api.add_item_to_selection(filename, id_)


class ContextMenu(object):
    def __init__(self, mainmenu, logview):
        self.logview = logview

        self.find_paramaters = (mainmenu.ID_FIND, "&Find in database",
                                wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))

    def get_items(self):
        return (self.find_paramaters, )

    def store_items(self, items):
        self.find = items[0]

    def update(self):
        self.find.Enable(False)

        sel = self.logview.GetSelectedItemsCount()

        if sel > 0:
            self.find.Enable()


def main():
    global base
    base = Main()
