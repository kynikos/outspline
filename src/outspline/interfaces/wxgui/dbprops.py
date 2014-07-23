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

import os.path
import time as time_
import wx
import wx.propgrid as wxpg

from outspline.coreaux_api import Event
import outspline.core_api as core_api

import notebooks
import databases

load_options_event = Event()


class DatabasePropertyManager(object):
    def __init__(self):
        self.open_panels = {}

        # No need to also bind to "save as" because it closes and opens the
        # database anyway, thus also closing the property tab if open
        core_api.bind_to_save_database(self._handle_save_database)
        core_api.bind_to_history_insert(self._handle_items_number)
        core_api.bind_to_history_remove(self._handle_items_number)
        core_api.bind_to_insert_item(self._handle_items_number)
        core_api.bind_to_delete_item(self._handle_items_number)
        # No need to bind to pasting items

        databases.close_database_event.bind(self._handle_close_database)

    def post_init(self):
        self.nb_icon_index = wx.GetApp().nb_right.add_image(
                                        wx.ArtProvider.GetBitmap('@properties',
                                        wx.ART_TOOLBAR, (16, 16)))

    def open(self, filename):
        if filename not in self.open_panels:
            self.open_panels[filename] = DatabaseProperties(self, filename)
            self.open_panels[filename].configure()
        else:
            nb = wx.GetApp().nb_right
            nb.SetSelection(nb.GetPageIndex(self.open_panels[filename].panel))

    def _handle_save_database(self, kwargs):
        try:
            manager = self.open_panels[kwargs['filename']]
        except KeyError:
            pass
        else:
            manager.refresh_file_properties()

    def _handle_items_number(self, kwargs):
        try:
            manager = self.open_panels[kwargs['filename']]
        except KeyError:
            pass
        else:
            manager.refresh_database_statistics()

    def _handle_close_database(self, kwargs):
        filename = kwargs['filename']

        try:
            panel = self.open_panels[filename].panel
        except KeyError:
            pass
        else:
            self.close(panel, filename)

    def close(self, panel, filename):
        nb = wx.GetApp().nb_right
        nb.close_page(nb.GetPageIndex(panel))
        del self.open_panels[filename]

    def get_manager(self, filename):
        return self.open_panels[filename]

    def get_notebook_icon_index(self):
        return self.nb_icon_index


class DatabasePropertiesPanel(wx.Panel):
    def __init__(self, parent, manager, filename):
        wx.Panel.__init__(self, parent)
        self.ctabmenu = TabContextMenu(manager, self, filename)

    def get_tab_context_menu(self):
        return self.ctabmenu


class DatabaseProperties(object):
    def __init__(self, manager, filename):
        self.manager = manager
        self.filename = filename
        nb = wx.GetApp().nb_right

        self.panel = DatabasePropertiesPanel(nb, self.manager, self.filename)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(sizer)

        self.propgrid = wxpg.PropertyGrid(self.panel, style=wxpg.PG_TOOLTIPS)
        self.propgrid.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)

        sizer.Add(self.propgrid, 1, flag=wx.EXPAND)

        nb.add_page(self.panel, os.path.basename(self.filename),
                                imageId=self.manager.get_notebook_icon_index())

        self.onchange_actions = {}

        self.propgrid.Bind(wxpg.EVT_PG_CHANGED, self._handle_property_changed)

        notebooks.plugin_close_event.bind(self._handle_close_tab)

    def _handle_property_changed(self, event):
        property_ = event.GetProperty()
        self.onchange_actions[property_.GetName()](property_.GetValue())

    def _handle_close_tab(self, kwargs):
        if kwargs['page'] is self.panel:
            self.manager.close(self.panel, self.filename)

    def configure(self):
        self._init_file_props()
        self._init_db_stats()
        self._init_dependencies()
        self._init_options()

        self.propgrid.SetSplitterLeft()

    def _init_file_props(self):
        self.propgrid.Append(wxpg.PropertyCategory("File properties", "file"))

        props = (
            wxpg.FileProperty("Location", "file.location", ""),
            wxpg.StringProperty("Last modified", "file.modified", ""),
            wxpg.StringProperty("Last accessed", "file.accessed", ""),
            # os.path.getctime just returns the modification time on Unix
            #wxpg.StringProperty("Created", "file.created", ""),
            wxpg.StringProperty("Size", "file.size", ""),
        )

        for prop in props:
            self.propgrid.Append(prop)
            prop.Enable(False)

        self.propgrid.SetPropertyAttribute("file.size", "Units", "KiB")

        self.refresh_file_properties()

    def _init_db_stats(self):
        self.propgrid.Append(wxpg.PropertyCategory("Database statistics",
                                                                        "db"))

        prop = wxpg.IntProperty("Number of items", "db.items", 0)
        self.propgrid.Append(prop)
        prop.Enable(False)

        self.refresh_database_statistics()

    def _init_dependencies(self):
        self.propgrid.Append(wxpg.PropertyCategory("Extension dependencies",
                                                            "dependencies"))

        cursor = core_api.get_database_dependencies(self.filename)

        for i, row in enumerate(cursor):
            addon = row['CM_addon']

            # No need to display core
            if addon != 'core':
                prop = wxpg.BoolProperty(addon,
                                        "dependencies.{}".format(str(i)), True)
                self.propgrid.Append(prop)
                prop.SetAttribute("UseCheckbox", True)
                prop.Enable(False)

    def _init_options(self):
        self.propgrid.Append(wxpg.PropertyCategory("Miscellaneous options",
                                                                    "options"))

        hlimit = core_api.get_database_history_soft_limit(self.filename)

        prop = wxpg.IntProperty("Items log soft limit", "options.core.hlimit",
                                                                        hlimit)

        self.onchange_actions["options.core.hlimit"] = self._set_history_limit

        # SpinCtrl looks too ugly...
        #prop.SetEditor("SpinCtrl")
        prop.SetAttribute("Min", 0)
        prop.SetAttribute("Max", 999)
        self.propgrid.Append(prop)

        load_options_event.signal(filename=self.filename)

    def add_option(self, prop, action):
        self.propgrid.Append(prop)
        self.onchange_actions[prop.GetName()] = action

    def _set_history_limit(self, value):
        core_api.update_database_history_soft_limit(self.filename, value)

    def refresh_file_properties(self):
        self.propgrid.SetPropertyValue("file.location", self.filename)
        self.propgrid.SetPropertyValue("file.modified",
                                    time_.strftime('%x %X', time_.localtime(
                                    os.path.getmtime(self.filename))))
        self.propgrid.SetPropertyValue("file.accessed",
                                    time_.strftime('%x %X', time_.localtime(
                                    os.path.getatime(self.filename))))
        # os.path.getctime just returns the modification time on Unix
        #self.propgrid.SetPropertyValue("file.created",
        #                            time_.strftime('%x %X', time_.localtime(
        #                            os.path.getctime(self.filename))))
        self.propgrid.SetPropertyValue("file.size",
                                str(os.path.getsize(self.filename) / 1024.0))

    def refresh_database_statistics(self):
        self.propgrid.SetPropertyValue("db.items",
                                    core_api.get_items_count(self.filename))


class TabContextMenu(wx.Menu):
    def __init__(self, manager, panel, filename):
        # Without implementing this menu, the menu of the previously selected
        # tab is shown when righ-clicking the tab
        self.manager = manager
        self.panel = panel
        self.filename = filename

        wx.Menu.__init__(self)

        self.ID_CLOSE = wx.NewId()

        self.close = wx.MenuItem(self, self.ID_CLOSE, "&Close")

        self.close.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))

        self.AppendItem(self.close)

        wx.GetApp().Bind(wx.EVT_MENU, self._close_tab, self.close)

    def _close_tab(self, event):
        self.manager.close(self.panel, self.filename)
