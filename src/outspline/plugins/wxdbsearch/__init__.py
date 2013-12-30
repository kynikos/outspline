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


class SearchViewPanel(wx.Panel):
    # Having a special class name for this panel lets recognize when a search
    # notebook tab is selected
    mainview = None

    def __init__(self, parent, mainview):
        wx.Panel.__init__(self, parent)
        self.mainview = mainview


class SearchView():
    # Unrelated: Add wxpython<=2.8 to the depends in the PKGBUILD? **************************
    panel = None
    box = None
    filters = None
    results = None

    def __init__(self, parent):
        self.panel = SearchViewPanel(parent, self)
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.box)

        self.filters = SearchFilters(self)
        self.results = SearchResults(self)

        self.box.Add(self.filters.box, flag=wx.EXPAND | wx.BOTTOM, border=4)
        self.box.Add(self.results.listview, 1, flag=wx.EXPAND)

    def search(self, event=None):
        # Stop the current search, if ongoing ******************************************
        # Add (part of) the search string to the title of the notebook tab ******************
        # Show when the search is ongoing and when it's finished ****************************
        # Close all open searches if no databases are left open after closing them **********************************
        string = self.filters.text.GetValue()
        string = re.escape(string)  # Escape only if needed **********************************

        self.results.reset()

        try:
            regexp = re.compile(string, re.IGNORECASE)  # Add flags as needed **************
        except re.error:
            pass  # Show error dialog *******************************************************
        else:
            # Note that the databases are released *before* the threads are
            # terminated: this is safe as no more calls to the databases are
            # made after core_api.get_all_items_text
            core_api.block_databases()

            for filename in core_api.get_open_databases():
                # It's not easy to benchmark the search for all the databases
                # at once, as the searches are done in separate threads
                search_start = (time.time(), time.clock())

                rows = core_api.get_all_items_text(filename)

                # A thread for each database is instantiated and started
                thread = threading.Thread(target=self._search_threaded,
                                args=(regexp, filename, rows, search_start))
                thread.start()

            # Note that the databases are released *before* the threads are
            # terminated: this is safe as no more calls to the databases are
            # made after core_api.get_all_items_text
            core_api.release_databases()

    def _search_threaded(self, regexp, filename, rows, search_start):
        fname = os.path.basename(filename)
        results = []

        for row in rows:
            id_ = row['I_id']
            text = row['I_text']

            results = self._find_match_lines(regexp, id_, text, results)

        log.debug('Search in {} completed in {} (time) / {} (clock) s'.format(
                                            filename,
                                            time.time() - search_start[0],
                                            time.clock() - search_start[1]))

        # The gui must be updated in the main thread, so do it only once when
        # the search is *finished* instead of calling CallAfter every time a
        # match is found
        wx.CallAfter(self.results.display, filename, fname, results)

    def _find_match_lines(self, regexp, id_, text, results):
        heading = text.partition('\n')[0]

        # I can't use a simple for loop because previous_line_index must be
        # initialized at the first iteration
        iterator = regexp.finditer(text)

        try:
            match = iterator.next()
        except StopIteration:
            pass
        else:
            line, previous_line_end_index = self._find_match_line(text, 0,
                                                                match.start())
            results.append((id_, heading, line))

            # break if one result per item ***************************************************

            while True:
                try:
                    match = iterator.next()
                except StopIteration:
                    break
                else:
                    # Don't use >= because if looking for an expression that
                    # starts with '\n', the one starting at
                    # previous_line_end_index (which is always a '\n'
                    # character except at the last iteration) will have been
                    # found at the previous iteration
                    if match.start() > previous_line_end_index:
                        line, previous_line_end_index = self._find_match_line(
                                text, previous_line_end_index, match.start())
                        results.append((id_, heading, line))

        return results

    def _find_match_line(self, text, previous_line_end_index, match_start):
        # Add 1 so that the line doesn't start with the '\n'
        # If the first match is in the first line, rfind will return -1, so
        # adding 1 will give 0 which is still the expected index
        # For the matches after the first one (which are already filtered for
        # being all on different lines) rfind will always find an index (and
        # never return -1) because previous_line_end_index is always the index
        # of a '\n' character
        # If match_start is the index of a '\n' character, line_start will be
        # the *previous* '\n' character, which is expected, as '\n' characters
        # are considered to be part of the previous line (specifically its
        # final character)
        line_start = text.rfind('\n', previous_line_end_index, match_start) + 1

        try:
            line_end = text.index('\n', line_start)
        except ValueError:
            # The match is in the last line
            line_end = len(text)

        line = text[line_start:line_end]

        return (line, line_end)


class SearchFilters():
    # Search in all databases / in selected database / under selected items  **********
    # Regular expression **************************************************************
    # Case sensitive ******************************************************************
    # List of words (OR) **************************************************************
    # Whole words (not part of words) *************************************************
    # Invert results ******************************************************************
    # Show only one result per item ***************************************************
    # Search only in headings *********************************************************
    # Ignore links ********************************************************************
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
    itemdatamap = None

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

        self.itemdatamap = {}

        self.listview.DeleteAllItems()

    def display(self, filename, fname, results):
        # Even though this method is called with wx.CallAfter from
        # self.listview._search_threaded, which is running in a different
        # thread, there's no need to check that the databases and items still
        # exist, because they're not queried any more. Doing it wouldn't make
        # sense because then the search should be also refreshed when closing
        # a database, deleting items etc... Instead, perform those checks when
        # acting on the search results, e.g. with context-menu actions
        # Note that this method is called as many times as the open databases,
        # because self.listview._search_threaded is run separately for every
        # database
        for result in results:
            id_, heading, line = result

            index = self.listview.InsertStringItem(sys.maxint, fname)
            self.listview.SetStringItem(index, 1, heading)
            self.listview.SetStringItem(index, 2, line)

            # In order for ColumnSorterMixin to work, all items must have a
            # unique data value
            self.listview.SetItemData(index, index)

            self.itemdatamap[index] = (filename, id_)

            # Both the key and the values of self.datamap must comply with the
            # requirements of ColumnSorterMixin
            self.datamap[index] = (fname, heading, line)


class MainMenu(wx.Menu):
    # Close (and stop the search, if ongoing) *****************************************
    # Close all (and stop any ongoing searches) ***************************************
    # Also item context menu **********************************************************
    # Also tab context menu ***********************************************************
    # Also close with tab X ***********************************************************
    ID_NEW_SEARCH = None
    search = None
    ID_REFRESH_SEARCH = None
    refresh = None
    ID_FIND = None
    find = None
    ID_EDIT = None
    edit = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_NEW_SEARCH = wx.NewId()
        self.ID_REFRESH_SEARCH = wx.NewId()
        self.ID_FIND = wx.NewId()
        self.ID_EDIT = wx.NewId()

        self.search = wx.MenuItem(self, self.ID_NEW_SEARCH,
                                    "&New search...\tCTRL+f",
                                    "Open a new text search in the databases")
        self.refresh = wx.MenuItem(self, self.ID_REFRESH_SEARCH,
                                                "&Start search\tCTRL+r",
                                                "Start the selected search")
        self.find = wx.MenuItem(self, self.ID_FIND,
                "&Find in database\tF9",
                "Select the database items associated to the selected results")
        self.edit = wx.MenuItem(self, self.ID_EDIT,
                            "&Edit selected\tF12",
                            "Open in the editor the database items associated "
                            "to the selected results")

        self.search.SetBitmap(wx.ArtProvider.GetBitmap('@dbsearch',
                                                                wx.ART_MENU))
        self.refresh.SetBitmap(wx.ArtProvider.GetBitmap('@dbsearch',
                                                                wx.ART_MENU))
        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
        self.edit.SetBitmap(wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU))

        self.AppendItem(self.search)
        self.AppendItem(self.refresh)
        self.AppendSeparator()
        self.AppendItem(self.find)
        self.AppendItem(self.edit)

        wxgui_api.bind_to_menu(self.new_search, self.search)
        wxgui_api.bind_to_menu(self.refresh_search, self.refresh)
        wxgui_api.bind_to_menu(self.find_in_tree, self.find)
        wxgui_api.bind_to_menu(self.edit_items, self.edit)

        wxgui_api.bind_to_update_menu_items(self.update_items)
        wxgui_api.bind_to_reset_menu_items(self.reset_items)

        wxgui_api.insert_menu_main_item('&Search', 'View', self)

    def update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.search.Enable(False)
            self.refresh.Enable(False)
            self.find.Enable(False)
            self.edit.Enable(False)

            if core_api.get_databases_count() > 0:
                self.search.Enable()

            tab = wx.GetApp().nb_right.get_selected_tab()

            if tab.__class__ is SearchViewPanel:
                self.refresh.Enable()

                sel = tab.mainview.results.listview.GetFirstSelected()

                if sel > -1:
                    self.find.Enable()
                    self.edit.Enable()

    def reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.search.Enable()
        self.refresh.Enable()
        self.find.Enable()
        self.edit.Enable()

    def new_search(self, event):
        if core_api.get_databases_count() > 0:
            nb = wxgui_api.get_right_nb()
            wxgui_api.add_page_to_right_nb(SearchView(nb).panel, 'Search')

    def refresh_search(self, event):
        tab = wx.GetApp().nb_right.get_selected_tab()

        if tab.__class__ is SearchViewPanel:
            tab.mainview.search()

    def find_in_tree(self, event):
        tab = wx.GetApp().nb_right.get_selected_tab()

        if tab.__class__ is SearchViewPanel:
            results = tab.mainview.results
            listview = results.listview

            sel = listview.GetFirstSelected()

            if sel > -1:
                for filename in core_api.get_open_databases():
                    wxgui_api.unselect_all_items(filename)

                # [1]: line repeated in the loop because of
                # wxgui_api.select_database_tab
                filename, id_ = results.itemdatamap[listview.GetItemData(sel)]

                # Check database still exists *********************************************
                wxgui_api.select_database_tab(filename)

                while True:
                    # It's necessary to repeat this line (see [1]) because
                    # wxgui_api.select_database_tab must be executed only once
                    # for the first selected item
                    filename, id_ = results.itemdatamap[listview.GetItemData(
                                                                        sel)]

                    # Check item still exists *******************************************************
                    wxgui_api.add_item_to_selection(filename, id_)

                    sel = listview.GetNextSelected(sel)

                    if sel < 0:
                        break

    def edit_items(self, event):
        tab = wx.GetApp().nb_right.get_selected_tab()

        if tab.__class__ is SearchViewPanel:
            results = tab.mainview.results
            listview = results.listview

            sel = listview.GetFirstSelected()

            while sel > -1:
                filename, id_ = results.itemdatamap[listview.GetItemData(sel)]

                # Check item still exists *******************************************************
                wxgui_api.open_editor(filename, id_)

                sel = listview.GetNextSelected(sel)


def main():
    MainMenu()
