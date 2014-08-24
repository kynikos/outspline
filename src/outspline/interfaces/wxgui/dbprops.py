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
import shutil
import time as time_
import wx
import wx.propgrid as wxpg

import outspline.dbdeps as dbdeps
import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import Event
import outspline.core_api as core_api

import notebooks
import databases
import msgboxes

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

        if filename in self.open_panels:
            self.close(filename)

    def close(self, filename):
        nb = wx.GetApp().nb_right
        nb.close_page(nb.GetPageIndex(self.open_panels[filename].panel))
        del self.open_panels[filename]

    def get_open_tab(self, filename):
        return self.open_panels[filename]

    def get_notebook_icon_index(self):
        return self.nb_icon_index


class DatabasePropertiesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.ctabmenu = TabContextMenu()

    def get_tab_context_menu(self):
        return self.ctabmenu


class DatabaseProperties(object):
    def __init__(self, manager, filename):
        self.manager = manager
        self.filename = filename
        nb = wx.GetApp().nb_right

        self.panel = DatabasePropertiesPanel(nb)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(sizer)

        # PropertyGrid doesn't support TAB traversal (bug #331)
        # PropertyGrid doesn't get focused immediately, also blocking the first
        #   attempt to use a keyboard shortcut (bug #337)
        self.propgrid = wxpg.PropertyGrid(self.panel, style=wxpg.PG_TOOLTIPS)
        self.propgrid.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)

        sizer.Add(self.propgrid, 1, flag=wx.EXPAND)

        nb.add_page(self.panel, os.path.basename(self.filename),
                            self.manager.close, closeArgs=(self.filename, ),
                            imageId=self.manager.get_notebook_icon_index())

        self.onchange_actions = {}

        self.propgrid.Bind(wxpg.EVT_PG_CHANGED, self._handle_property_changed)

        notebooks.plugin_close_event.bind(self._handle_close_tab)

    def _handle_property_changed(self, event):
        property_ = event.GetProperty()
        self.onchange_actions[property_.GetName()](property_.GetClientData(),
                                                        property_.GetValue())

    def _handle_close_tab(self, kwargs):
        if kwargs['page'] is self.panel:
            self.manager.close(self.filename)

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
        self.propgrid.Append(wxpg.PropertyCategory("Extensions support",
                                                            "dependencies"))

        extensions = coreaux_api.get_addons_info(disabled=False)('Extensions')
        self.dependencies = core_api.get_database_dependencies(self.filename,
                                                                ignored=True)
        del self.dependencies[None]

        for ext in extensions.get_sections():
            if extensions(ext).get_bool('affects_database'):
                propname = "dependencies.{}".format(ext)
                prop = wxpg.EnumProperty(ext, propname, ('Enabled',
                                    'Disabled (remind)', 'Disabled (ignore)'))
                prop.SetClientData(ext)
                self.onchange_actions[propname] = self._change_dependencies
                self.propgrid.Append(prop)
                self.refresh_dependency(ext)

    def _init_options(self):
        self.propgrid.Append(wxpg.PropertyCategory("Miscellaneous options",
                                                                    "options"))

        hlimit = core_api.get_database_history_soft_limit(self.filename)

        prop = wxpg.IntProperty("Items log soft limit", "options.core.hlimit",
                                                                        hlimit)

        self.onchange_actions["options.core.hlimit"] = self._set_history_limit

        prop.SetEditor("SpinCtrl")
        prop.SetAttribute("Min", 0)
        prop.SetAttribute("Max", 999)
        self.propgrid.Append(prop)

        load_options_event.signal(filename=self.filename)

    def add_option(self, prop, action):
        self.propgrid.Append(prop)
        self.onchange_actions[prop.GetName()] = action

    def _change_dependencies(self, data, value):
        if core_api.block_databases():
            ext = data
            newchoice = value

            try:
                ver = self.dependencies[ext]
            except KeyError:
                currchoice = 1
            else:
                if ver is None:
                    currchoice = 2
                else:
                    currchoice = 0

            extsinfo = coreaux_api.get_addons_info()('Extensions')

            # This method shouldn't be triggered if the value is not changed,
            # so there's no need to check that newchoice != currchoice
            if currchoice == 0:
                reverse_deps = []

                for udep in self.dependencies:
                    dep = str(udep)
                    # Core (None) has been removed from self.dependencies
                    if self.dependencies[dep] is not None:
                        try:
                            ddeps = extsinfo(dep)['dependencies'].split(" ")
                        except KeyError:
                            ddeps = []

                        for ddep in ddeps:
                            sddep = ddep.split(".")

                            if ".".join(sddep[0:2]) == 'extensions.{}'.format(
                                                                        ext):
                                reverse_deps.append(dep)

                if reverse_deps:
                    self.refresh_dependency(ext)
                    msgboxes.warn_disable_dependency(reverse_deps).ShowModal()
                else:
                    # The dialog should be completely independent from this
                    # object, because if the operation is confirmed, it needs
                    # to close the database, including the properties tab (so
                    # use CallAfter)
                    wx.CallAfter(DependencyDialogDisable, self.filename, ext,
                                                    newchoice, self.manager)
            else:
                if newchoice == 0 :
                    try:
                        deps = extsinfo(ext)['dependencies'].split(" ")
                    except KeyError:
                        deps = []

                    missing_deps = []

                    for dep in deps:
                        sdep = dep.split(".")

                        if sdep[0] == 'extensions':
                            try:
                                ver = self.dependencies[sdep[1]]
                            except KeyError:
                                if extsinfo(sdep[1]).get_bool(
                                                        'affects_database'):
                                    missing_deps.append(sdep[1])
                            else:
                                if ver is None:
                                    missing_deps.append(sdep[1])

                    if missing_deps:
                        self.refresh_dependency(ext)
                        msgboxes.warn_enable_dependency(missing_deps
                                                                ).ShowModal()
                    else:
                        # The dialog should be completely independent from this
                        # object, because if the operation is confirmed, it
                        # needs to close the database, including the properties
                        # tab (so use CallAfter)
                        wx.CallAfter(DependencyDialogEnable, self.filename,
                                                ext, newchoice, self.manager)
                else:
                    if newchoice == 1:
                        core_api.remove_database_ignored_dependency(
                                                            self.filename, ext)
                        del self.dependencies[ext]
                    else:
                        core_api.add_database_ignored_dependency(self.filename,
                                                                        ext)
                        self.dependencies[ext] = None

                    self.refresh_dependency(ext)

            core_api.release_databases()

    def _set_history_limit(self, data, value):
        if core_api.block_databases():
            core_api.update_database_history_soft_limit(self.filename, value)
            core_api.release_databases()

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

    def refresh_dependency(self, ext):
        if ext in self.dependencies:
            if self.dependencies[ext] is not None:
                choice = 0
            else:
                choice = 2
        else:
            choice = 1

        self.propgrid.SetPropertyValue("dependencies.{}".format(ext), choice)


class _DependencyDialog(object):
    def __init__(self, filename, ext, value, propmanager):
        self.filename = filename
        self.ext = ext
        self.value = value
        self.propmanager = propmanager

        self.dialog = wx.Dialog(parent=wx.GetApp().root, title=self.title)

        outsizer = wx.BoxSizer(wx.VERTICAL)
        self.dialog.SetSizer(outsizer)

        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Add vsizer right here because then I use Fit in order to make
        # vsizer.GetSize().GetWidth() work
        outsizer.Add(vsizer, flag=wx.EXPAND | wx.ALL, border=12)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = wx.StaticBitmap(self.dialog, bitmap=wx.ArtProvider.GetBitmap(
                                                "@warning", wx.ART_CMN_DIALOG))
        hsizer.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        label = wx.StaticText(self.dialog, label=self.warning)
        label.Wrap(320)
        hsizer.Add(label, flag=wx.ALIGN_TOP)

        vsizer.Add(hsizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=12)

        label = wx.StaticText(self.dialog, label="The database needs to be "
                        "closed and re-opened in order to apply the changes.")
        # Fit in order to make vsizer.GetSize().GetWidth() work
        self.dialog.Fit()
        label.Wrap(vsizer.GetSize().GetWidth())
        vsizer.Add(label, flag=wx.BOTTOM, border=12)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self.dialog, label="A backup will be saved in:")
        hsizer2.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        defpath = time_.strftime('{}_%Y%m%d%H%M%S{}'.format(
                                            *os.path.splitext(self.filename)))
        self.backup = wx. FilePickerCtrl(self.dialog, message="Save backup",
            wildcard="|".join(('Outspline database (*.{})|*.{}'.format(
                                coreaux_api.get_standard_extension(),
                                coreaux_api.get_standard_extension()),
                    "All files (*)|*")),
            style=wx.FLP_SAVE | wx.FLP_OVERWRITE_PROMPT | wx.FLP_USE_TEXTCTRL)
        # Instantiating FilePickerCtrl with 'path' doesn't seem to work well
        self.backup.SetPath(defpath)
        hsizer2.Add(self.backup, 1, flag=wx.ALIGN_CENTER_VERTICAL)

        vsizer.Add(hsizer2, flag=wx.EXPAND | wx.BOTTOM, border=12)

        hsizer3 = wx.BoxSizer(wx.HORIZONTAL)

        ok = wx.Button(self.dialog, label="OK")
        hsizer3.Add(ok, flag=wx.RIGHT, border=8)

        cancel = wx.Button(self.dialog, label="Cancel")
        hsizer3.Add(cancel)

        vsizer.Add(hsizer3, flag=wx.ALIGN_RIGHT)

        self.dialog.Bind(wx.EVT_BUTTON, self._proceed, ok)
        self.dialog.Bind(wx.EVT_BUTTON, self._abort, cancel)
        self.dialog.Bind(wx.EVT_CLOSE, self._handle_close)

        self.dialog.Fit()
        self.dialog.ShowModal()

    def _proceed(self, event):
        # Close the properties tab explicitly, otherwise if the closing is
        # aborted, the choice controls should be reset to the current
        # configuration, if the tab is still open, which is not necessarily
        # true because the closing of the properties tab would race e.g. with
        # the dialogs to save the database
        self.propmanager.close(self.filename)

        if databases.close_database(self.filename):
            shutil.copy2(self.filename, self.backup.GetPath())

            if self.value == 0:
                dbdeps.Database(self.filename).add((self.ext, ))
            elif self.value == 1:
                dbdeps.Database(self.filename).remove((self.ext, ))
            else:
                dbdeps.Database(self.filename).remove((self.ext, ),
                                                                ignored=True)

            # Use CallAfter or segfaults may happen
            wx.CallAfter(databases.open_database, self.filename,
                                                        open_properties=True)
            # Note that no other operation should be done on the database
            #  directly here, because opening the database may fail e.g.
            #  because of the compatibility checks
        else:
            self.propmanager.open(self.filename)

        # Always close the dialog because the property settings have been
        # reset by closing and reopening the property tab
        self._close()

    def _abort(self, event):
        self.propmanager.get_open_tab(self.filename).refresh_dependency(
                                                                    self.ext)
        self._close()

    def _handle_close(self, event):
        # Also handle closing with X or Alt+F4
        self._close()

    def _close(self):
        self.dialog.Destroy()


class DependencyDialogEnable(_DependencyDialog):
    def __init__(self, filename, ext, value, propmanager):
        self.title = "Enable dependency"
        self.warning = ("Warning: enabling a dependency will clear all the "
                        "history of the database.")
        super(DependencyDialogEnable, self).__init__(filename, ext, value,
                                                                propmanager)


class DependencyDialogDisable(_DependencyDialog):
    def __init__(self, filename, ext, value, propmanager):
        self.title = "Disable dependency"
        self.warning = ("Warning: disabling a dependency will remove any data "
                        "associated with it; it will also clear all the "
                        "history of the database.")
        super(DependencyDialogDisable, self).__init__(filename, ext, value,
                                                                propmanager)


class TabContextMenu(wx.Menu):
    def __init__(self):
        # Without implementing this menu, the menu of the previously selected
        # tab is shown when righ-clicking the tab
        wx.Menu.__init__(self)

        self.ID_CLOSE = wx.NewId()

        self.close = wx.MenuItem(self,
                            wx.GetApp().menu.navigation.ID_CLOSE_TAB, "&Close")

        self.close.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))

        self.AppendItem(self.close)
