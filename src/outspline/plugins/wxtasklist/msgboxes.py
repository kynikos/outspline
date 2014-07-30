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

import outspline.interfaces.wxgui_api as wxgui_api


def save_to_json():
    return wx.FileDialog(wxgui_api.get_main_frame(), "Export tasklist view",
                                    "", 'outspline_events.json',
                                    'JSON (*.json)|*.json|All files (*)|*',
                                    style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)


def save_to_tsv():
    return wx.FileDialog(wxgui_api.get_main_frame(), "Export tasklist view",
                                    "", 'outspline_events.tsv',
                                    'TSV (*.tsv)|*.tsv|All files (*)|*',
                                    style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)


def save_to_xml():
    return wx.FileDialog(wxgui_api.get_main_frame(), "Export tasklist view",
                                    "", 'outspline_events.xml',
                                    'XML (*.xml)|*.xml|All files (*)|*',
                                    style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)


def warn_user_rights(filename):
    return wx.MessageDialog(wxgui_api.get_main_frame(), 'You are not '
                            'authorized to '
                            'create or overwrite {}.'.format(filename),
                            caption="Export tasklist view",
                            style=wx.OK | wx.ICON_EXCLAMATION)
