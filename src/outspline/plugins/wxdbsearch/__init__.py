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

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api


class SearchView():
    panel = None
    box = None
    filters = None
    results = None

    def __init__(self, parent):
        self.panel = wx.Panel(parent)
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.box)

        self.filters = SearchFilters(self.panel)
        self.results = SearchResults(self.panel)

        self.box.Add(self.filters.box, flag=wx.EXPAND)
        self.box.Add(self.results.list_, 1, flag=wx.EXPAND)


class SearchFilters():
    # Search in all databases / in selected database / under selected items  ************
    # Regular expression ****************************************************************
    # Case sensitive ********************************************************************
    # List of words (OR) ****************************************************************
    # Whole words (not part of words) ***************************************************
    # Invert results ********************************************************************
    box = None
    text = None
    search = None

    def __init__(self, parent):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.text = wx.TextCtrl(parent)
        self.box.Add(self.text, 1, flag=wx.ALIGN_CENTER_VERTICAL)

        self.search = wx.Button(parent)
        self.box.Add(self.search, flag=wx.ALIGN_CENTER_VERTICAL)


class SearchResults():
    # Fields:            **************************************************************
    #   Database         **************************************************************
    #   Title            **************************************************************
    #   Matching line    **************************************************************
    list_ = None

    def __init__(self, parent):
        self.list_ = wx.ListView(parent)


class MainMenu(wx.Menu):
    # Search (refresh)      ***********************************************************
    # Find in database      ***********************************************************
    # Edit selected         ***********************************************************
    # Close                 ***********************************************************
    # Close all             ***********************************************************
    # Also item context menu **********************************************************
    # Also tab context menu ***********************************************************
    # Also close with tab X ***********************************************************
    ID_SEARCH = None
    search = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_SEARCH = wx.NewId()

        self.search = wx.MenuItem(self, self.ID_SEARCH,
                                            "New &search...\tCTRL+f",
                                            "Search text in the databases")

        self.search.SetBitmap(wx.ArtProvider.GetBitmap('@dbsearch',
                                                                wx.ART_MENU))

        self.AppendItem(self.search)

        wxgui_api.bind_to_menu(self.new_search, self.search)

        wxgui_api.bind_to_update_menu_items(self.update_items)
        wxgui_api.bind_to_reset_menu_items(self.reset_items)

        wxgui_api.insert_menu_main_item('&Search', 'View', self)

    def update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.search.Enable(False)

            if core_api.get_databases_count() > 0:
                self.search.Enable()

    def reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.search.Enable()

    def new_search(self, event):
        if core_api.get_databases_count() > 0:
            nb = wxgui_api.get_right_nb()
            wxgui_api.add_page_to_right_nb(SearchView(nb).panel, 'Search')


def main():
    MainMenu()
