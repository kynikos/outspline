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
import time
import os.path
import sys
import threading
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin

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

        self.box.Add(self.filters.box, flag=wx.EXPAND | wx.BOTTOM, border=4)
        self.box.Add(self.results.listview, 1, flag=wx.EXPAND)

    def search(self, event):
        # Add (part of) the search string to the title of the notebook tab ******************
        # Show when the search is ongoing and when it's finished ****************************
        # Note that the databases are *not* blocked, because searching should *******************************
        # never alter the database **************************************************************
        string = self.filters.text.GetValue()
        string = re.escape(string)  # Escape only if needed **********************************

        self.results.reset()

        try:
            regexp = re.compile(string, re.IGNORECASE)  # Add flags as needed **************
        except re.error:
            pass  # Show error dialog *******************************************************
        else:
            thread = threading.Thread(target=self._search_threaded,
                                                            args=(regexp, ))
            thread.start()

    def _search_threaded(self, regexp):
        # Test race conditions with long searches *****************************************
        # Note that the databases are *not* blocked, because searching should *******************************
        # never alter the database *********************************************************
        search_start = (time.time(), time.clock())

        results = []

        for filename in core_api.get_open_databases():
            rows = core_api.get_all_items_text(filename)

            for row in rows:
                id_ = row['I_id']
                text = row['I_text']

                results = self.find_match_lines(regexp, filename, id_,
                                                            text, results)

        log.debug('Search completed in {} (time) / {} (clock) s'.format(
                                          time.time() - search_start[0],
                                          time.clock() - search_start[1]))

        # The gui must be updated in the main thread, so do it only once when
        # the search is *finished* instead of calling CallAfter every time a
        # match is found
        wx.CallAfter(self.results.display, results)

    def find_match_lines(self, regexp, filename, id_, text, results):
        fname = os.path.basename(filename)
        heading = text.partition('\n')[0]

        # I can't use a simple for loop because previous_line_index must be
        # initialized at the first iteration
        iterator = regexp.finditer(text)

        try:
            match = iterator.next()
        except StopIteration:
            pass
        else:
            previous_line_index, line = self._find_first_match_line(text,
                                                                match.start())
            results.append((filename, id_, fname, heading, line))

            # break if one result per item ***************************************************

            while True:
                try:
                    match = iterator.next()
                except StopIteration:
                    break
                else:
                    try:
                        previous_line_index, line = self._find_match_line(text,
                                            previous_line_index, match.start())
                    except exceptions.MatchIsInSameLineError:
                        pass
                    else:
                        results.append((filename, id_, fname, heading, line))

        return results

    def _find_first_match_line(self, text, match_start):
        try:
            # Add 1 so that the line doesn't start with the '\n'
            line_start = text.rindex('\n', 0, match_start) + 1
        except ValueError:
            # The match is in the first line
            line_start = 0

        return self._find_match_line_end(text, line_start)

    def _find_match_line(self, text, previous_line_index, match_start):
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

        self.text = wx.TextCtrl(mainview.panel, size=(-1, 24))
        self.box.Add(self.text, 1, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.search = wx.Button(mainview.panel, label='Search', size=(-1, 24))
        self.box.Add(self.search, flag=wx.ALIGN_CENTER_VERTICAL)

        mainview.panel.Bind(wx.EVT_BUTTON, mainview.search, self.search)


class ListView(wx.ListView, ListCtrlAutoWidthMixin, ColumnSorterMixin):
    imagelistsmall = None
    imagemap = None

    def __init__(self, parent, columns):
        # Note that this makes use of ListView, which is an interface for
        # ListCtrl
        wx.ListView.__init__(self, parent, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)
        ColumnSorterMixin.__init__(self, columns)

        self.set_image_lists()

    def GetListCtrl(self):
        return self

    def set_image_lists(self):
        self.imagelistsmall = wx.ImageList(16, 16)
        self.imagemap = {
            'small': {}
        }

        # Remember to find better icons (add to existing bug report) ***************************
        self.imagemap['small']['sortup'] = self.imagelistsmall.Add(
                 wx.ArtProvider.GetBitmap('@sortup', wx.ART_TOOLBAR, (16, 16)))
        self.imagemap['small']['sortdown'] = self.imagelistsmall.Add(
               wx.ArtProvider.GetBitmap('@sortdown', wx.ART_TOOLBAR, (16, 16)))

        self.SetImageList(self.imagelistsmall, wx.IMAGE_LIST_SMALL)

    def GetSortImages(self):
        return (self.imagemap['small']['sortup'],
                                            self.imagemap['small']['sortdown'])


class SearchResults():
    listview = None
    datamap = None

    def __init__(self, mainview):
        self.listview = ListView(mainview.panel, 3)

        self.listview.InsertColumn(0, 'Database', width=120)
        self.listview.InsertColumn(1, 'Heading', width=300)
        self.listview.InsertColumn(2, 'Match line', width=120)

    def reset(self):
        # Defining an itemDataMap dictionary is required by ColumnSorterMixin
        self.listview.itemDataMap = {}

        # Create an alias for self.itemDataMap to save it from any future
        # attribute renaming
        self.datamap = self.listview.itemDataMap

        self.listview.DeleteAllItems()

    def display(self, results):
        for result in results:
            filename, id_, fname, heading, line = result

            index = self.listview.InsertStringItem(sys.maxint, fname)
            self.listview.SetStringItem(index, 1, heading)
            self.listview.SetStringItem(index, 2, line)

            # In order for ColumnSorterMixin to work, all items must have a
            # unique data value
            self.listview.SetItemData(index, index)

            # Both the key and the values of self.datamap must comply with the
            # requirements of ColumnSorterMixin
            self.datamap[index] = (fname, heading, line)


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
