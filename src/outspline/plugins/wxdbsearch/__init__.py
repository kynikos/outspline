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

import re
import wx
import time

from outspline.coreaux_api import log
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api

import exceptions


class SearchView():
    panel = None
    box = None
    filters = None
    results = None

    def __init__(self, parent):
        self.panel = wx.Panel(parent)
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.box)

        self.filters = SearchFilters(self)
        self.results = SearchResults(self)

        self.box.Add(self.filters.box, flag=wx.EXPAND)
        self.box.Add(self.results.list_, 1, flag=wx.EXPAND)

    def search(self, event):
        # Search must be threaded ***********************************************************
        core_api.block_databases()

        string = self.filters.text.GetValue()
        string = re.escape(string)  # Escape only if needed **********************************

        try:
            regexp = re.compile(string, re.IGNORECASE)  # Add flags as needed **************
        except re.error:
            pass  # Show error dialog *******************************************************
        else:
            search_start = (time.time(), time.clock())

            for filename in core_api.get_open_databases():
                rows = core_api.get_all_items_text(filename)

                for row in rows:
                    id_ = row['I_id']
                    text = row['I_text']

                    matches = []

                    for match in regexp.finditer(text):
                        matches.append(match)
                        # break if one result per item **********************************

                    # It's necessary to aggregate the matches first because
                    # only one match per line should be shown
                    if matches:
                        self.results.add(filename, id_, text, matches)

            log.debug('Search completed in {} (time) / {} (clock) s'.format(
                                              time.time() - search_start[0],
                                              time.clock() - search_start[1]))

        core_api.release_databases()


class SearchFilters():
    # Search in all databases / in selected database / under selected items  **********
    # Regular expression **************************************************************
    # Case sensitive ******************************************************************
    # List of words (OR) **************************************************************
    # Whole words (not part of words) *************************************************
    # Invert results ******************************************************************
    # Show only one result per item ***************************************************
    box = None
    text = None
    search = None

    def __init__(self, mainview):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.text = wx.TextCtrl(mainview.panel)
        self.box.Add(self.text, 1, flag=wx.ALIGN_CENTER_VERTICAL)

        self.search = wx.Button(mainview.panel, label='Search')
        self.box.Add(self.search, flag=wx.ALIGN_CENTER_VERTICAL)

        mainview.panel.Bind(wx.EVT_BUTTON, mainview.search, self.search)


class SearchResults():
    # Fields:            **************************************************************
    #   Database         **************************************************************
    #   Title            **************************************************************
    #   Matching line    **************************************************************
    list_ = None

    def __init__(self, mainview):
        self.list_ = wx.ListView(mainview.panel)

    def add(self, filename, id_, text, matches):
        heading = self.get_heading(filename, id_)

        # I have to use an iterator because previous_line_index must be
        # initialized at the first iteration
        iterator = iter(matches)

        match = iterator.next()
        previous_line_index, line = self.find_first_match_line(text,
                                                                match.start())
        self.show(filename, heading, line)

        while True:
            try:
                match = iterator.next()
            except StopIteration:
                break
            else:
                try:
                    previous_line_index, line = self.find_match_line(text,
                                            previous_line_index, match.start())
                except exceptions.MatchIsInSameLineError:
                    pass
                else:
                    self.show(filename, heading, line)

    def find_first_match_line(self, text, match_start):
        try:
            # Add 1 so that the line doesn't start with the '\n'
            line_start = text.rindex('\n', 0, match_start) + 1
        except ValueError:
            # The match is in the first line
            line_start = 0

        return self._find_match_line_end(text, line_start)

    def find_match_line(self, text, previous_line_index, match_start):
        try:
            # Add 1 so that the line doesn't start with the '\n'
            line_start = text.rindex('\n', previous_line_index, match_start) \
                                                                            + 1
        except ValueError:
            # The match is in the line of the previous match
            raise exceptions.MatchIsInSameLineError()
        else:
            return self._find_match_line_end(text, line_start)

    def _find_match_line_end(self, text, line_start):
        try:
            line_end = text.index('\n', line_start)
        except ValueError:
            # The match is in the last line
            line_end = len(text)

        line = text[line_start:line_end]

        return (line_start, line)

    def get_heading(self, filename, id_):
        text = core_api.get_item_text(filename, id_)
        return text.partition('\n')[0]

    def show(self, filename, heading, line):
        print('ZZZ', filename, heading, line)  # *******************************************************************


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
