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


def bad_regular_expression():
    return wx.MessageDialog(wxgui_api.get_main_frame(),
                        'Bad regular expression.',
                        caption="Search", style=wx.OK | wx.ICON_EXCLAMATION)


def some_items_not_found():
    return wx.MessageDialog(wxgui_api.get_main_frame(),
                    'Some selected search result items do not exist '
                    'anymore. Re-execute the search for up-to-date results.',
                    caption="Search", style=wx.OK | wx.ICON_EXCLAMATION)


def all_items_not_found():
    return wx.MessageDialog(wxgui_api.get_main_frame(),
                    'All the selected search result items do not exist '
                    'anymore. Re-execute the search for up-to-date results.',
                    caption="Search", style=wx.OK | wx.ICON_EXCLAMATION)
