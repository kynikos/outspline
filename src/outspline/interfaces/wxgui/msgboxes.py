# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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
import traceback

import outspline.static.plural as plural

import outspline.coreaux_api as coreaux_api
import outspline.dbdeps as dbdeps

import databases

aborted_save_default_warning = ("An unspecified event has prevented the "
                                                "database from being saved.")


class DatabaseUpdaterAdd(object):
    def __init__(self, updater, open_properties):
        self.updater = updater
        self.open_properties = open_properties

        self.dialog = wx.Dialog(parent=wx.GetApp().root, title="Open database")

        outsizer = wx.BoxSizer(wx.VERTICAL)
        self.dialog.SetSizer(outsizer)

        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Add vsizer right here because then I use Fit in order to make
        # vsizer.GetSize().GetWidth() work
        outsizer.Add(vsizer, flag=wx.EXPAND | wx.ALL, border=12)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = wx.StaticBitmap(self.dialog,
                bitmap=wx.GetApp().artprovider.get_dialog_icon('@question'))
        hsizer.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        hvsizer = wx.BoxSizer(wx.VERTICAL)

        # Core will never be in the dependencies here
        label = wx.StaticText(self.dialog, label="{} is missing support for "
                        "the following installed extensions:".format(
                                                self.updater.get_filename()))
        label.Wrap(320)
        hvsizer.Add(label, flag=wx.BOTTOM, border=4)

        self.deplist = []
        deptext = []

        for addon in self.updater.get_addible_dependencies():
            self.deplist.append(addon)
            deptext.append(u"\u2022 {}".format(addon))

        label = wx.StaticText(self.dialog, label="\n".join(deptext))
        label.Wrap(320)
        hvsizer.Add(label)

        hsizer.Add(hvsizer, flag=wx.ALIGN_TOP)

        vsizer.Add(hsizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=12)

        add = wx.Button(self.dialog, label="Add &support and open database")
        vsizer.Add(add, flag=wx.EXPAND | wx.BOTTOM, border=4)

        label = wx.StaticText(self.dialog, label="Warning: enabling "
                    "dependencies will clear all the history of the database.")
        # Fit in order to make vsizer.GetSize().GetWidth() work
        self.dialog.Fit()
        label.Wrap(vsizer.GetSize().GetWidth())
        vsizer.Add(label, flag=wx.BOTTOM, border=4)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self.dialog, label="A backup will be saved in:")
        hsizer2.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        defpath = time_.strftime('{}_%Y%m%d%H%M%S{}'.format(
                            *os.path.splitext(self.updater.get_filename())))
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

        vsizer.Add(wx.StaticLine(self.dialog), flag=wx.EXPAND | wx.BOTTOM,
                                                                    border=12)

        skip = wx.Button(self.dialog, label="&Open database as it is")
        vsizer.Add(skip, flag=wx.EXPAND | wx.BOTTOM, border=4)

        label = wx.StaticText(self.dialog, label="This dialog will appear "
                                "every time the database is opened, unless "
                                "disabled in the database properties.")
        # Fit in order to make vsizer.GetSize().GetWidth() work
        self.dialog.Fit()
        label.Wrap(vsizer.GetSize().GetWidth())
        vsizer.Add(label, flag=wx.EXPAND | wx.BOTTOM, border=12)

        vsizer.Add(wx.StaticLine(self.dialog), flag=wx.EXPAND | wx.BOTTOM,
                                                                    border=12)

        abort = wx.Button(self.dialog, label="&Abort opening database")
        vsizer.Add(abort, flag=wx.EXPAND)

        self.dialog.Bind(wx.EVT_BUTTON, self._add, add)
        self.dialog.Bind(wx.EVT_BUTTON, self._skip, skip)
        self.dialog.Bind(wx.EVT_BUTTON, self._abort, abort)
        self.dialog.Bind(wx.EVT_CLOSE, self._handle_close)

        self.dialog.Fit()
        self.dialog.ShowModal()

    def _add(self, event):
        filename = self.updater.get_filename()
        shutil.copy2(filename, self.backup.GetPath())
        dbdeps.Database(filename).add(self.deplist)
        self._close()

        # Use CallAfter or segfaults may happen e.g. if re-opening after
        # changing the dependencies in the properties tab
        wx.CallAfter(databases.open_database, filename,
                                        open_properties=self.open_properties)

    def _skip(self, event):
        self._close()
        # Use CallAfter or segfaults may happen e.g. if re-opening after
        # changing the dependencies in the properties tab
        wx.CallAfter(databases.open_database, self.updater.get_filename(),
                                        check_new_extensions=False,
                                        open_properties=self.open_properties)

    def _abort(self, event):
        self._close()

    def _handle_close(self, event):
        # Also handle closing with X or Alt+F4
        self._close()

    def _close(self):
        self.dialog.Destroy()


class DatabaseUpdaterUpdate(object):
    def __init__(self, updater, open_properties):
        self.updater = updater
        self.open_properties = open_properties

        self.dialog = wx.Dialog(parent=wx.GetApp().root, title="Open database")

        outsizer = wx.BoxSizer(wx.VERTICAL)
        self.dialog.SetSizer(outsizer)

        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Add vsizer right here because then I use Fit in order to make
        # vsizer.GetSize().GetWidth() work
        outsizer.Add(vsizer, flag=wx.EXPAND | wx.ALL, border=12)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = wx.StaticBitmap(self.dialog,
                bitmap=wx.GetApp().artprovider.get_dialog_icon('@question'))
        hsizer.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        hvsizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self.dialog, label="{} is based on an old "
                    "version of the core or the following extensions:".format(
                                                self.updater.get_filename()))
        label.Wrap(320)
        hvsizer.Add(label, flag=wx.BOTTOM, border=4)

        dependencies = self.updater.get_updatable_dependencies()
        self.deplist = []
        deptext = []

        for addon in dependencies:
            dep = dependencies[addon]

            self.deplist.append(addon)

            if addon is None:
                deptext.append(u"\u2022 core (version {}.x supported, {}.x "
                                    "installed)".format(dep[1], dep[0]))
            else:
                deptext.append(u"\u2022 {} (version {}.x supported, {}.x "
                                    "installed)".format(addon, dep[1], dep[0]))

        label = wx.StaticText(self.dialog, label="\n".join(deptext))
        label.Wrap(320)
        hvsizer.Add(label)

        hsizer.Add(hvsizer, flag=wx.ALIGN_TOP)

        vsizer.Add(hsizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=12)

        update = wx.Button(self.dialog, label="&Update and open database")
        vsizer.Add(update, flag=wx.EXPAND | wx.BOTTOM, border=4)

        label = wx.StaticText(self.dialog, label="Warning: updating "
                    "dependencies will clear all the history of the database.")
        # Fit in order to make vsizer.GetSize().GetWidth() work
        self.dialog.Fit()
        label.Wrap(vsizer.GetSize().GetWidth())
        vsizer.Add(label, flag=wx.BOTTOM, border=4)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self.dialog, label="A backup will be saved in:")
        hsizer2.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        defpath = time_.strftime('{}_%Y%m%d%H%M%S{}'.format(
                            *os.path.splitext(self.updater.get_filename())))
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

        vsizer.Add(wx.StaticLine(self.dialog), flag=wx.EXPAND | wx.BOTTOM,
                                                                    border=12)

        abort = wx.Button(self.dialog, label="&Abort opening database")
        vsizer.Add(abort, flag=wx.EXPAND)

        self.dialog.Bind(wx.EVT_BUTTON, self._update, update)
        self.dialog.Bind(wx.EVT_BUTTON, self._abort, abort)
        self.dialog.Bind(wx.EVT_CLOSE, self._handle_close)

        self.dialog.Fit()
        self.dialog.ShowModal()

    def _update(self, event):
        filename = self.updater.get_filename()
        shutil.copy2(filename, self.backup.GetPath())
        dbdeps.Database(filename).upgrade(self.deplist)
        self._close()

        # Use CallAfter or segfaults may happen e.g. if re-opening after
        # changing the dependencies in the properties tab
        wx.CallAfter(databases.open_database, filename,
                                        open_properties=self.open_properties)

    def _abort(self, event):
        self._close()

    def _handle_close(self, event):
        # Also handle closing with X or Alt+F4
        self._close()

    def _close(self):
        self.dialog.Destroy()


class DatabaseUpdaterAbort(object):
    def __init__(self, updater):
        self.updater = updater

        self.dialog = wx.Dialog(parent=wx.GetApp().root, title="Open database")

        outsizer = wx.BoxSizer(wx.VERTICAL)
        self.dialog.SetSizer(outsizer)

        vsizer = wx.BoxSizer(wx.VERTICAL)

        outsizer.Add(vsizer, flag=wx.EXPAND | wx.ALL, border=12)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = wx.StaticBitmap(self.dialog,
                    bitmap=wx.GetApp().artprovider.get_dialog_icon('@warning'))
        hsizer.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        hvsizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self.dialog, label="In order to open {}, "
            "the core or the following extensions must be either installed "
            "or upgraded:".format(self.updater.get_filename()))
        label.Wrap(320)
        hvsizer.Add(label, flag=wx.BOTTOM, border=4)

        dependencies = self.updater.get_aborting_dependencies()
        deptext = []

        for addon in dependencies:
            dep = dependencies[addon]

            if addon is None:
                deptext.append(u"\u2022 core (version {}.x installed, {}.x "
                                    "required)".format(dep[0], dep[1]))
            elif dep[0] is None:
                deptext.append(u"\u2022 {} (not installed, version {}.x "
                                    "required)".format(addon, dep[1]))
            else:
                deptext.append(u"\u2022 {} (version {}.x installed, {}.x "
                                    "required)".format(addon, dep[0], dep[1]))

        label = wx.StaticText(self.dialog, label="\n".join(deptext))
        label.Wrap(320)
        hvsizer.Add(label)

        hsizer.Add(hvsizer, flag=wx.ALIGN_TOP)

        vsizer.Add(hsizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=12)

        buttons = self.dialog.CreateStdDialogButtonSizer(flags=wx.OK)
        vsizer.Add(buttons, flag=wx.EXPAND)

        self.dialog.Fit()
        self.dialog.ShowModal()


def create_db_ask():
    return wx.FileDialog(wx.GetApp().root, message="Create database",
                        wildcard="|".join(("Outspline database (*.{})|*.{}"
                                "".format(coreaux_api.get_standard_extension(),
                                coreaux_api.get_standard_extension()),
                                "All files (*)|*")),
                        style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)


def open_db_ask(defdir):
    return wx.FileDialog(wx.GetApp().root, message="Open database",
                        defaultDir=defdir,
                        wildcard="|".join(("Outspline database (*.{})|*.{}"
                                "".format(coreaux_api.get_standard_extension(),
                                coreaux_api.get_standard_extension()),
                                "All files (*)|*")),
                        style=wx.OPEN | wx.FD_FILE_MUST_EXIST)


def open_db_open(filename):
    return wx.MessageDialog(wx.GetApp().root, '{} seems to be already open.'
                            ''.format(filename), caption="Open database",
                            style=wx.OK | wx.ICON_EXCLAMATION)


def open_db_access(filename):
    return wx.MessageDialog(wx.GetApp().root, '{} does not exist or you do '
                            'not have the permissions to open it.'
                            ''.format(filename), caption="Open database",
                            style=wx.OK | wx.ICON_EXCLAMATION)


def open_db_invalid(filename):
    return wx.MessageDialog(wx.GetApp().root, '{} is not a valid Outspline '
                        'database.'.format(filename), caption="Open database",
                        style=wx.OK | wx.ICON_EXCLAMATION)


def open_db_locked(filename):
    return wx.MessageDialog(wx.GetApp().root, '{} seems to be open by another '
                            'instance of Outspline or a different application.'
                            ''.format(filename), caption="Open database",
                            style=wx.OK | wx.ICON_EXCLAMATION)


def create_db_open(filename):
    return wx.MessageDialog(wx.GetApp().root, '{} seems to be open. '
                           'You cannot overwrite an open database.'
                           ''.format(filename), caption="Create database",
                           style=wx.OK | wx.ICON_EXCLAMATION)


def create_db_access(filename):
    return wx.MessageDialog(wx.GetApp().root, 'You are not authorized to '
                            'create or overwrite {}.'.format(filename),
                            caption="Create database",
                            style=wx.OK | wx.ICON_EXCLAMATION)


def close_db_ask(filename):
    return wx.MessageDialog(wx.GetApp().root, 'Do you want to save {} before '
                            'closing?'.format(filename),
                            caption="Save database",
                            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)


def close_tab_ask():
    return wx.MessageDialog(wx.GetApp().root, 'Do you want to apply the '
                            'changes to the item before closing the editor?',
                            caption="Close editor",
                            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)


def close_tab_without_saving():
    return wx.MessageDialog(wx.GetApp().root, 'This editor must be closed '
                            'without saving in order to perform the requested '
                            'operation.', caption="Close editor",
                            style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)


def warn_aborted_save(message):
    return wx.MessageDialog(wx.GetApp().root, message, caption="Aborted save",
                                            style=wx.OK | wx.ICON_EXCLAMATION)


def warn_enable_dependency(missing_deps):
    return wx.MessageDialog(wx.GetApp().root, "Before enabling this "
                "dependency you have to enable the following ones:\n" +
                "".join([u"\n\u2022 {}".format(dep) for dep in missing_deps]),
                caption="Enable dependency",
                style=wx.OK | wx.ICON_EXCLAMATION)


def warn_disable_dependency(reverse_deps):
    return wx.MessageDialog(wx.GetApp().root, "Before disabling this "
                "dependency you have to disable the following ones:\n" +
                "".join([u"\n\u2022 {}".format(dep) for dep in reverse_deps]),
                caption="Disable dependency",
                style=wx.OK | wx.ICON_EXCLAMATION)


def blocked_databases():
    return wx.MessageDialog(wx.GetApp().root, "The databases are blocked by "
                "another ongoing operation, try again after its completion.",
                caption="Blocked databases",
                style=wx.OK | wx.ICON_EXCLAMATION)


def uncaught_exception(exc_info):
    return wx.MessageDialog(wx.GetApp().root,
                            ''.join(traceback.format_exception(*exc_info)),
                            caption="Uncaught exception",
                            style=wx.OK | wx.ICON_ERROR)
