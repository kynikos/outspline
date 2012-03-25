# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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
import traceback

import plural

import organism.coreaux_api as coreaux_api


def create_db_ask():
    return wx.FileDialog(wx.GetApp().root, "Create database", '', "",
                        'Organism database (*.{})'.format(
                                        coreaux_api.get_standard_extension()) +
                        '|*.' + coreaux_api.get_standard_extension() +
                        "|All files (*)|*",
                        style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)


def open_db_ask():
    return wx.FileDialog(wx.GetApp().root, "Open database", '', "",
                        'Organism database (*.{})'.format(
                                        coreaux_api.get_standard_extension()) +
                        '|*.' + coreaux_api.get_standard_extension() +
                        "|All files (*)|*",
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


def open_db_incompatible(filename):
    return wx.MessageDialog(wx.GetApp().root, '{} is not a valid Organism '
                            'database, or it was created with a different '
                            'addon configuration than the current one.'
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


def delete_items_confirm(n):
    return wx.MessageDialog(wx.GetApp().root, '{} item{P0s} {P0is} going to '
                            'be deleted.'.format(n, **plural.set((n, ), )),
                            caption="Delete items",
                            style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)


def close_tab_ask():
    return wx.MessageDialog(wx.GetApp().root, 'Do you want to apply the '
                            'changes to the item before closing the editor?',
                            caption="Close editor",
                            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)


def close_tab_without_saving():
    return wx.MessageDialog(wx.GetApp().root, 'This editor must be closed '
                            'without saving in order to perform the requested '
                            'oepration.', caption="Close editor",
                            style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)


def uncaught_exception(exc_info):
    return wx.MessageDialog(wx.GetApp().root,
                            ''.join(traceback.format_exception(*exc_info)),
                            caption="Uncaught exception",
                            style=wx.OK | wx.ICON_ERROR)
