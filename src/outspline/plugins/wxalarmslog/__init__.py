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
import wx.propgrid as wxpg
# Temporary workaround for bug #279
import time as time_

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api

base = None


class Main(object):
    def __init__(self):
        wxgui_api.install_bundled_icon('@alarmslog', ("alarmslog16.png", ))

        self.alarmlogs = {}
        self.mainmenu = LogsMenu(self)

        wxgui_api.bind_to_creating_tree(self._handle_creating_tree)
        wxgui_api.bind_to_load_property_options(self._handle_load_options)
        wxgui_api.bind_to_close_database(self._handle_close_database)

    def _handle_creating_tree(self, kwargs):
        filename = kwargs['filename']

        if filename in organism_alarms_api.get_supported_open_databases():
            self.alarmlogs[filename] = AlarmsLog(wxgui_api.get_logs_parent(
                                            filename), filename, self.mainmenu)

    def _handle_load_options(self, kwargs):
        filename = kwargs['filename']

        if filename in organism_alarms_api.get_supported_open_databases():
            alimit = organism_alarms_api.get_alarms_log_limit(filename)
            prop = wxpg.IntProperty("Alarms log soft limit",
                            "options.extension.organism_alarms.alimit", alimit)
            prop.SetEditor("SpinCtrl")
            wxgui_api.add_property_option(filename, prop,
                                        self.alarmlogs[filename].set_log_limit)

    def _handle_close_database(self, kwargs):
        try:
            del self.alarmlogs[kwargs['filename']]
        except KeyError:
            pass

    def get_selected_log(self):
        filename = wxgui_api.get_selected_database_filename()

        try:
            return self.alarmlogs[filename]
        except KeyError:
            return False


class AlarmsLogModel(wx.dataview.PyDataViewIndexListModel):
    def __init__(self, data):
        # Using a model is necessary to disable the native "live" search
        # See bugs #349 and #351
        super(AlarmsLogModel, self).__init__()
        self.data = data

        # The wxPython demo uses weak references for the item objects: see if
        # it can be used also in this case (bug #348)
        #self.objmapper.UseWeakRefs(True)

    def GetValueByRow(self, row, col):
        return self.data[row][col]

    def GetColumnCount(self):
        return 3

    def GetCount(self):
        return len(self.data)

    '''def GetColumnType(self, col):
        # It seems not needed to override this method, it's not done in the
        # demos either
        # Besides, returning "string" here would activate the "live" search
        # feature that belongs to the native GTK widget used by DataViewCtrl
        # See also bug #349
        # https://groups.google.com/d/msg/wxpython-users/QvSesrnD38E/31l8f6AzIhAJ
        # https://groups.google.com/d/msg/wxpython-users/4nsv7x1DE-s/ljQHl9RTnuEJ
        return None'''


class AlarmsLog(object):
    def __init__(self, parent, filename, mainmenu):
        self.filename = filename

        self.view = wx.dataview.DataViewCtrl(parent,
                        style=wx.dataview.DV_MULTIPLE |
                        wx.dataview.DV_ROW_LINES | wx.dataview.DV_NO_HEADER)

        self.data = []
        self.dvmodel = AlarmsLogModel(self.data)
        self.view.AssociateModel(self.dvmodel)
        # According to DataViewModel's documentation (as of September 2014)
        # its reference count must be decreased explicitly to avoid memory
        # leaks; the wxPython demo, however, doesn't do it, and if done here,
        # the application crashes with a segfault when closing all databases
        # See also bug #104
        #self.dvmodel.DecRef()

        # Temporary workaround for bug #279
        #self.view.AppendDateColumn('Timestamp', 0,
        #        width=wx.COL_WIDTH_AUTOSIZE, align=wx.ALIGN_CENTER_VERTICAL)
        self.view.AppendTextColumn('Timestamp', 0, width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Action', 1, width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Item', 2)

        config = coreaux_api.get_plugin_configuration('wxalarmslog')(
                                                        'ExtendedShortcuts')
        wxgui_api.install_accelerators(self.view, {
            config["find"]: lambda event: self.find_in_tree(),
        })

        self.reasons = {0: '[snoozed]',
                        1: '[dismissed]',
                        2: '[deleted]'}

        cmenu = ContextMenu(mainmenu, self)

        self.tool_id, menu_items, popup_cmenu = wxgui_api.add_log(filename,
                                self.view, "Alarms",
                                wxgui_api.get_log_icon('@alarmslog'),
                                cmenu.get_items(), cmenu.update)
        cmenu.store_items(menu_items)

        self.view.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU,
                                                                popup_cmenu)
        organism_alarms_api.bind_to_alarm_off(self._handle_alarm_off)
        wxgui_api.bind_to_close_database(self._handle_close_database)

        self._refresh()

    def _handle_alarm_off(self, kwargs):
        self._refresh()

    def _handle_close_database(self, kwargs):
        organism_alarms_api.bind_to_alarm_off(self._handle_alarm_off, False)

    def is_shown(self):
        return self.view.IsShown()

    def has_selection(self):
        return self.view.HasSelection()

    def get_selections(self):
        return self.view.GetSelections()

    def get_item_id(self, item):
        return self.data[self.dvmodel.GetRow(item)][3]

    def get_tool_id(self):
        return self.tool_id

    def _refresh(self):
        del self.data[:]
        cursor = organism_alarms_api.get_alarms_log(self.filename)

        for row in cursor:
            # 4 values are stored per row, but only the first 3 must be shown
            self.data.append(self._format_values(row))

        self.dvmodel.Reset(len(self.data))

    def _format_values(self, row):
        # Temporary workaround for bug #279
        #tstamp = wx.DateTime().SetTimeT(row['AOL_tstamp'])
        tstamp = time_.strftime('%Y-%m-%d %H:%M', time_.localtime(
                                                            row['AOL_tstamp']))
        reason = self.reasons[row['AOL_reason']]
        text = row['AOL_text']
        id_ = row['AOL_item']
        return (tstamp, reason, text, id_)

    def set_log_limit(self, data, value):
        if core_api.block_databases():
            organism_alarms_api.update_alarms_log_limit(self.filename, value)
            core_api.release_databases()

    def find_in_tree(self):
        sel = self.get_selections()

        if len(sel) > 0:
            wxgui_api.unselect_all_items(self.filename)

            # Do not loop directly on view.GetSelections(), e.g.
            #   for s in view.GetSelections():
            # because it doesn't work as expected!
            for item in sel:
                id_ = self.get_item_id(item)

                # The logged item may not exist anymore
                if core_api.is_item(self.filename, id_):
                    wxgui_api.add_item_to_selection(self.filename, id_)


class LogsMenu(object):
    def __init__(self, plugin):
        self.plugin = plugin

        self.ID_ALARMS = wx.NewId()
        self.ID_SELECT = wx.NewId()
        self.ID_FIND = wx.NewId()

        submenu = wx.Menu()

        config = coreaux_api.get_plugin_configuration('wxalarmslog')(
                                                                'Shortcuts')

        self.alarms = wx.MenuItem(wxgui_api.get_menu_logs(), self.ID_ALARMS,
                            '&Alarms', 'Alarms log commands', subMenu=submenu)
        self.select = wx.MenuItem(submenu, self.ID_SELECT,
                "&Select\t{}".format(config['select']),
                "Select the alarms history log")
        self.find = wx.MenuItem(submenu, self.ID_FIND,
                "Find in &database\t{}".format(config['find']),
                "Select the database items associated to the selected entries")

        self.alarms.SetBitmap(wxgui_api.get_menu_icon('@alarmslog'))
        self.select.SetBitmap(wxgui_api.get_menu_icon('@jump'))
        self.find.SetBitmap(wxgui_api.get_menu_icon('@dbfind'))

        wxgui_api.add_menu_logs_item(self.alarms)
        submenu.AppendItem(self.select)
        submenu.AppendItem(self.find)

        wxgui_api.bind_to_menu(self._select, self.select)
        wxgui_api.bind_to_menu(self._find_in_tree, self.find)

        wxgui_api.bind_to_menu_view_logs_update(self._update_items)
        wxgui_api.bind_to_menu_view_logs_disable(self._disable_items)
        wxgui_api.bind_to_reset_menu_items(self._reset_items)

    def _update_items(self, kwargs):
        self.find.Enable(False)

        log = self.plugin.get_selected_log()

        if log and log.is_shown() and log.has_selection():
            self.find.Enable()

    def _disable_items(self, kwargs):
        self.alarms.Enable(False)

    def _reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.alarms.Enable()
        self.find.Enable()

    def _select(self, event):
        log = self.plugin.get_selected_log()

        if log:
            wxgui_api.select_log(log.get_tool_id())

    def _find_in_tree(self, event):
        log = self.plugin.get_selected_log()

        if log and log.is_shown():
            log.find_in_tree()


class ContextMenu(object):
    def __init__(self, mainmenu, log):
        self.log = log

        self.find_paramaters = (mainmenu.ID_FIND, "&Find in database",
                                wxgui_api.get_menu_icon('@dbfind'))

    def get_items(self):
        return (self.find_paramaters, )

    def store_items(self, items):
        self.find = items[0]

    def update(self):
        if self.log.has_selection():
            self.find.Enable()
        else:
            self.find.Enable(False)


def main():
    global base
    base = Main()
