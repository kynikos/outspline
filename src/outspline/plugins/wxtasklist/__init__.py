# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import list as list_
import filters


class TaskList():
    panel = None
    pbox = None
    list_ = None
    filters = None

    def __init__(self, parent):
        # Note that the remaining border is due to the SplitterWindow, whose
        # border cannot be removed because it's used to highlight the sash
        # See also http://trac.wxwidgets.org/ticket/12413
        # and http://trac.wxwidgets.org/changeset/66230
        self.panel = wx.Panel(parent, style=wx.BORDER_NONE)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

        self.list_ = list_.OccurrencesView(self.panel)
        self.filters = filters.Filters(self.panel, self.list_)

        self.pbox.Add(self.filters.panel, flag=wx.EXPAND | wx.ALL, border=2)
        self.pbox.Add(self.list_.listview, 1, flag=wx.EXPAND | wx.ALL,
                                                                      border=2)


def main():
    nb = wxgui_api.get_right_nb()
    wxgui_api.add_plugin_to_right_nb(TaskList(nb).panel, 'List view',
                                                                   close=False)
