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

import re
import time
import os.path
import sys
import threading
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin

from outspline.static.activestate.tco import tail_call_optimized

from outspline.coreaux_api import log
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api

import msgboxes

mainmenu = None
searches = []
nb_icon_index = None


class SearchViewPanel(wx.Panel):
    ctabmenu = None

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

    def _init_tab_menu(self):
        self.ctabmenu = TabContextMenu()

    def get_tab_context_menu(self):
        return self.ctabmenu


class SearchView():
    panel = None
    box = None
    filters = None
    results = None
    threads = None
    search_threaded_action = None
    finish_search_action = None

    def __init__(self, parent):
        self.panel = SearchViewPanel(parent)
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.box)

        self.filters = SearchFilters(self)
        self.results = SearchResults(self)

        self.panel._init_tab_menu()

        self.threads = 0
        self.search_threaded_action = self._search_threaded_stop
        self.finish_search_action = self._finish_search_dummy

        self.box.Add(self.filters.box, flag=wx.EXPAND | wx.BOTTOM, border=4)
        self.box.Add(self.results.listview, 1, flag=wx.EXPAND)

        wxgui_api.bind_to_close_database(self.handle_close_database)
        wxgui_api.bind_to_plugin_close_event(self.handle_tab_hide)

    @classmethod
    def open_(cls):
        nb = wxgui_api.get_right_nb()
        searchview = cls(nb)

        global searches
        searches.append(searchview)

        wxgui_api.add_page_to_right_nb(searchview.panel, 'Search',
                                                        imageId=nb_icon_index)

    def close_(self):
        self.finish_search_action = self._finish_search_close
        self.stop_search()

    def handle_tab_hide(self, kwargs):
        if kwargs['page'] is self.panel:
            self.close_()

    def handle_close_database(self, kwargs):
        if core_api.get_databases_count() < 1:
            self.close_()

    def set_title(self, title):
        if len(title) > 20:
            title = title[:17] + '...'

        wxgui_api.set_right_nb_page_title(self.panel, title)

    def search(self):
        self.finish_search_action = self._finish_search_restart
        self.stop_search()

    def stop_search(self):
        if self.threads > 0:
            self.search_threaded_action = self._search_threaded_stop
        else:
            self.finish_search_action()

    def finish_search(self):
        self.threads -= 1

        # Perform the action only when the last thread terminates
        if self.threads == 0:
            self.finish_search_action()

    def _finish_search_dummy(self):
        pass

    def _finish_search_close(self):
        wxgui_api.close_right_nb_page(self.panel)

        global searches
        searches.remove(self)

        # Unbind the handlers, otherwise they would be called also for closed
        # searches when closing all databases (e.g. when quitting the
        # application) raising an exception when trying to remove self from
        # the searches list
        wxgui_api.bind_to_close_database(self.handle_close_database, False)
        wxgui_api.bind_to_plugin_close_event(self.handle_tab_hide, False)

        self.finish_search_action = self._finish_search_dummy

    def _finish_search_restart(self):
        string = self.filters.text.GetValue()
        self.set_title(string)

        if not self.filters.option4.GetValue():
            string = re.escape(string)

        self.results.reset()
        self.search_threaded_action = self._search_threaded_continue
        self.finish_search_action = self._finish_search_dummy

        flags = re.MULTILINE

        if not self.filters.option5.GetValue():
            flags |= re.IGNORECASE

        try:
            regexp = re.compile(string, flags)
        except re.error:
            msgboxes.bad_regular_expression().ShowModal()
        else:
            # Note that the databases are released *before* the threads are
            # terminated: this is safe as no more calls to the databases are
            # made after core_api.get_all_items_text in
            # self._finish_search_restart_database
            core_api.block_databases()

            if self.filters.option1.GetValue():
                filename = wxgui_api.get_selected_database_filename()
                self._finish_search_restart_database(filename, regexp)
            else:
                for filename in core_api.get_open_databases():
                    self._finish_search_restart_database(filename, regexp)

            # Note that the databases are released *before* the threads are
            # terminated: this is safe as no more calls to the databases are
            # made after core_api.get_all_items_text in
            # self._finish_search_restart_database
            core_api.release_databases()

    def _finish_search_restart_database(self, filename, regexp):
        # It's not easy to benchmark the search for all the databases
        # at once, as the searches are done in separate threads
        search_start = (time.time(), time.clock())

        # Retrieve all the rows immediately (based on fetchall()):
        # retrieving row by row (based on fetchone()) would need
        # querying the database in the thread, which would be faster
        # but exposed to race conditions
        rows = core_api.get_all_items_text(filename)
        iterator = iter(rows)

        # A thread for each database is instantiated and started
        thread = threading.Thread(
                target=self._search_threaded_continue,
                args=(regexp, filename, iterator, [], search_start))
        thread.name = "wxdbsearch_{}".format(filename)
        thread.start()
        self.threads += 1

    # use tail call optimization to avoid Python's limit to recursions
    # (sys.getrecursionlimit()), which would lead to an exception in case of
    # databases with more items than such limit
    @tail_call_optimized
    def _search_threaded_continue(self, regexp, filename, iterator, results,
                                                                search_start):
        try:
            row = iterator.next()
        except StopIteration:
            log.debug('Search in {} completed in {} (time) / {} (clock) s'
                                            ''.format(filename,
                                            time.time() - search_start[0],
                                            time.clock() - search_start[1]))

            fname = os.path.basename(filename)

            # The gui must be updated in the main thread, so do it only once
            # when the search is *finished* instead of calling CallAfter every
            # time a match is found
            wx.CallAfter(self.results.display, filename, fname, results)
        else:
            id_ = row['I_id']
            text = row['I_text']

            heading = text.partition('\n')[0]

            try:
                if self.filters.option2.GetValue():
                    text = heading
            except wx.PyDeadObjectError:
                # If the application is closed while the search is ongoing,
                #  this is where it would crash
                # If there were more problems, consider running this thread as
                #  a daemon
                pass
            else:
                results = self._find_match_lines(regexp, id_, heading, text,
                                                                    results)

                # Use a recursion instead of a simple for loop, so that it will
                # be easy to stop the search from the main thread if needed
                self.search_threaded_action(regexp, filename, iterator,
                                                        results, search_start)

    def _search_threaded_stop(self, regexp, filename, iterator, results,
                                                                search_start):
        log.debug('Search in {} stopped after {} (time) / {} (clock) s'
                                            ''.format(filename,
                                            time.time() - search_start[0],
                                            time.clock() - search_start[1]))

        # The number of ongoing threads must be updated in the main thread
        wx.CallAfter(self.finish_search)

    def _find_match_lines(self, regexp, id_, heading, text, results):
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

            if not self.filters.option3.GetValue():
                while True:
                    try:
                        match = iterator.next()
                    except StopIteration:
                        break
                    else:
                        # Don't use >= because if looking for an expression
                        # that starts with '\n', the one starting at
                        # previous_line_end_index (which is always a '\n'
                        # character except at the last iteration) will have
                        # been found at the previous iteration
                        if match.start() > previous_line_end_index:
                            line, previous_line_end_index = \
                                        self._find_match_line(text,
                                        previous_line_end_index, match.start())
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
    mainview = None
    box = None
    text = None
    search = None
    ogrid = None
    option1 = None
    option2 = None
    option3 = None
    option4 = None
    option5 = None

    def __init__(self, mainview):
        self.mainview = mainview

        self.box = wx.BoxSizer(wx.VERTICAL)
        sbox = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(mainview.panel, label='Search for:')
        sbox.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.text = wx.TextCtrl(mainview.panel)
        sbox.Add(self.text, 1, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.search = wx.Button(mainview.panel, label='Search')
        sbox.Add(self.search, flag=wx.ALIGN_CENTER_VERTICAL)

        self.box.Add(sbox, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.ogrid = wx.GridSizer(3, 2, 4, 4)
        self.box.Add(self.ogrid, flag=wx.EXPAND)

        # The order of creation affects the placement in the GridSizer
        self.option1 = self.make_option('Only in selected database')
        self.option4 = self.make_option('Regular expression')
        self.option2 = self.make_option('Only in headings')
        self.option5 = self.make_option('Case sensitive')
        self.option3 = self.make_option('Only one result per item')

        mainview.panel.Bind(wx.EVT_BUTTON, self._search, self.search)

    def _search(self, event):
        self.mainview.search()

    def make_option(self, label):
        obox = wx.BoxSizer(wx.HORIZONTAL)
        check = wx.CheckBox(self.mainview.panel)
        obox.Add(check, flag=wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self.mainview.panel, label=label)
        obox.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        self.ogrid.Add(obox)

        return check


class ListView(wx.ListView, ListCtrlAutoWidthMixin, ColumnSorterMixin):
    imagelistsmall = None
    imagemap = None

    def __init__(self, parent, columns):
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

        self.imagemap['small']['sortup'] = self.imagelistsmall.Add(
                 wx.ArtProvider.GetBitmap('@sortup', wx.ART_TOOLBAR, (16, 16)))
        self.imagemap['small']['sortdown'] = self.imagelistsmall.Add(
               wx.ArtProvider.GetBitmap('@sortdown', wx.ART_TOOLBAR, (16, 16)))

        self.AssignImageList(self.imagelistsmall, wx.IMAGE_LIST_SMALL)

    def GetSortImages(self):
        return (self.imagemap['small']['sortup'],
                                            self.imagemap['small']['sortdown'])


class SearchResults():
    mainview = None
    listview = None
    cmenu = None
    datamap = None
    itemdatamap = None

    def __init__(self, mainview):
        self.mainview = mainview
        self.listview = ListView(mainview.panel, 3)

        self.listview.InsertColumn(0, 'Database', width=120)
        self.listview.InsertColumn(1, 'Heading', width=300)
        self.listview.InsertColumn(2, 'Match line', width=120)

        self.cmenu = ContextMenu()

        self.listview.Bind(wx.EVT_CONTEXT_MENU, self.popup_context_menu)

    def popup_context_menu(self, event):
        self.listview.PopupMenu(self.cmenu)

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
        # self.listview._search_threaded_continue, which is running in a
        # different thread, there's no need to check that the databases and
        # items still exist, because they're not queried any more. Doing it
        # wouldn't make sense because then the search should be also refreshed
        # when closing a database, deleting items etc... Instead, perform those
        # checks when acting on the search results, e.g. with context-menu
        # actions
        # Note that this method is called as many times as the open databases,
        # because self.listview._search_threaded_continue is run separately for
        # every database
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

        self.mainview.finish_search()


class MainMenu(wx.Menu):
    ID_NEW_SEARCH = None
    search = None
    ID_REFRESH_SEARCH = None
    refresh = None
    ID_FIND = None
    find = None
    ID_EDIT = None
    edit = None
    ID_CLOSE = None
    close_ = None
    ID_CLOSE_ALL = None
    closeall = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_NEW_SEARCH = wx.NewId()
        self.ID_REFRESH_SEARCH = wx.NewId()
        self.ID_FIND = wx.NewId()
        self.ID_EDIT = wx.NewId()
        self.ID_CLOSE = wx.NewId()
        self.ID_CLOSE_ALL = wx.NewId()

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
                            "&Edit selected\tCTRL+F9",
                            "Open in the editor the database items associated "
                            "to the selected results")
        self.close_ = wx.MenuItem(self, self.ID_CLOSE, "Cl&ose\tCTRL+t",
                                                "Close the selected search")
        self.closeall = wx.MenuItem(self, self.ID_CLOSE_ALL,
                        "Clos&e all\tCTRL+SHIFT+t", "Close all open searches")

        self.search.SetBitmap(wx.ArtProvider.GetBitmap('@dbsearch',
                                                                wx.ART_MENU))
        self.refresh.SetBitmap(wx.ArtProvider.GetBitmap('@dbsearch',
                                                                wx.ART_MENU))
        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
        self.edit.SetBitmap(wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU))
        self.close_.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))
        self.closeall.SetBitmap(wx.ArtProvider.GetBitmap('@closeall',
                                                                wx.ART_MENU))

        self.AppendItem(self.search)
        self.AppendItem(self.refresh)
        self.AppendSeparator()
        self.AppendItem(self.find)
        self.AppendItem(self.edit)
        self.AppendSeparator()
        self.AppendItem(self.close_)
        self.AppendItem(self.closeall)

        wxgui_api.bind_to_menu(self.new_search, self.search)
        wxgui_api.bind_to_menu(self.refresh_search, self.refresh)
        wxgui_api.bind_to_menu(self.find_in_tree, self.find)
        wxgui_api.bind_to_menu(self.edit_items, self.edit)
        wxgui_api.bind_to_menu(self.close_tab, self.close_)
        wxgui_api.bind_to_menu(self.close_all_tabs, self.closeall)

        wxgui_api.bind_to_update_menu_items(self.update_items)
        wxgui_api.bind_to_reset_menu_items(self.reset_items)

        wxgui_api.insert_menu_main_item('&Search',
                                    wxgui_api.get_menu_logs_position(), self)

    @staticmethod
    def get_selected_search():
        tab = wxgui_api.get_selected_right_nb_tab()

        for search in searches:
            if search.panel is tab:
                return search
        else:
            return False

    def update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.search.Enable(False)
            self.refresh.Enable(False)
            self.find.Enable(False)
            self.edit.Enable(False)
            self.close_.Enable(False)
            self.closeall.Enable(False)

            if core_api.get_databases_count() > 0:
                self.search.Enable()

            mainview = self.get_selected_search()

            if mainview:
                self.refresh.Enable()
                self.close_.Enable()

                sel = mainview.results.listview.GetFirstSelected()

                if sel > -1:
                    self.find.Enable()
                    self.edit.Enable()

            if len(searches) > 0:
                self.closeall.Enable()

    def reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.search.Enable()
        self.refresh.Enable()
        self.find.Enable()
        self.edit.Enable()
        self.close_.Enable()
        self.closeall.Enable()

    def new_search(self, event):
        if core_api.get_databases_count() > 0:
            SearchView.open_()

    def refresh_search(self, event):
        mainview = self.get_selected_search()

        if mainview:
            mainview.search()

    def find_in_tree(self, event):
        mainview = self.get_selected_search()

        if mainview:
            results = mainview.results
            listview = results.listview

            sel = listview.GetFirstSelected()

            if sel > -1:
                for filename in core_api.get_open_databases():
                    wxgui_api.unselect_all_items(filename)

                seldb = None
                warning = False

                # [1]: line repeated in the loop because of
                # wxgui_api.select_database_tab
                filename, id_ = results.itemdatamap[listview.GetItemData(sel)]

                while True:
                    # It's necessary to repeat this line (see [1]) because
                    # wxgui_api.select_database_tab must be executed only once
                    # for the first selected item
                    filename, id_ = results.itemdatamap[listview.GetItemData(
                                                                        sel)]

                    # Check whether the database is still open and the item
                    # still exists because the search results are retrieved in
                    # a separate thread and are not updated together with the
                    # database
                    if core_api.is_database_open(filename) and \
                                            core_api.is_item(filename, id_):
                        wxgui_api.add_item_to_selection(filename, id_)

                        if seldb is None:
                            seldb = filename
                    else:
                        warning = True

                    sel = listview.GetNextSelected(sel)

                    if sel < 0:
                        break

                if seldb:
                    wxgui_api.select_database_tab(seldb)

                    if warning:
                        msgboxes.some_items_not_found().ShowModal()
                elif warning:
                    msgboxes.all_items_not_found().ShowModal()

    def edit_items(self, event):
        mainview = self.get_selected_search()

        if mainview:
            results = mainview.results
            listview = results.listview

            sel = listview.GetFirstSelected()

            exists = False
            warning = False

            while sel > -1:
                filename, id_ = results.itemdatamap[listview.GetItemData(sel)]

                # Check whether the database is still open and the item
                # still exists because the search results are retrieved in
                # a separate thread and are not updated together with the
                # database
                if core_api.is_database_open(filename) and \
                                            core_api.is_item(filename, id_):
                    wxgui_api.open_editor(filename, id_)

                    exists = True
                else:
                    warning = True

                sel = listview.GetNextSelected(sel)

            if warning:
                if exists:
                    msgboxes.some_items_not_found().ShowModal()
                else:
                    msgboxes.all_items_not_found().ShowModal()

    def close_tab(self, event):
        mainview = self.get_selected_search()

        if mainview:
            mainview.close_()

    def close_all_tabs(self, event):
        # Use a copy of searches because close_ is modifying it
        for mainview in searches[:]:
            mainview.close_()


class ContextMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        find = wx.MenuItem(self, mainmenu.ID_FIND, "&Find in database")
        edit = wx.MenuItem(self, mainmenu.ID_EDIT, "&Edit selected")

        find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
        edit.SetBitmap(wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU))

        self.AppendItem(find)
        self.AppendItem(edit)


class TabContextMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        refresh = wx.MenuItem(self, mainmenu.ID_REFRESH_SEARCH,
                                                "&Start search\tCTRL+r",
                                                "Start the selected search")
        close_ = wx.MenuItem(self, mainmenu.ID_CLOSE, "Cl&ose\tCTRL+t",
                                                "Close the selected search")

        refresh.SetBitmap(wx.ArtProvider.GetBitmap('@dbsearch', wx.ART_MENU))
        close_.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))

        self.AppendItem(refresh)
        self.AppendItem(close_)


def main():
    global mainmenu
    mainmenu = MainMenu()

    global nb_icon_index
    nb_icon_index = wxgui_api.add_right_nb_image(
                                    wx.ArtProvider.GetBitmap('@find',
                                    wx.ART_TOOLBAR, (16, 16)))
