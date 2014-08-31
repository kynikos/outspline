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
import wx.lib.agw.flatnotebook as flatnotebook
from wx.lib.agw.flatnotebook import FlatNotebook

from outspline.coreaux_api import Event
import outspline.core_api as core_api

import editor
import databases

plugin_close_event = Event()


class Notebook(FlatNotebook):
    def __init__(self, parent):
        FlatNotebook.__init__(self, parent, agwStyle=
                                        flatnotebook.FNB_FANCY_TABS |
                                        flatnotebook.FNB_NO_X_BUTTON |
                                        flatnotebook.FNB_NO_NAV_BUTTONS |
                                        flatnotebook.FNB_X_ON_TAB |
                                        flatnotebook.FNB_DROPDOWN_TABS_LIST |
                                        flatnotebook.FNB_NO_TAB_FOCUS)
        self.parent = parent
        self._set_colours(parent)

        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CONTEXT_MENU,
                                                        self._popup_tab_menu)

    def _set_colours(self, parent):
        bgcolour = parent.GetBackgroundColour()
        avg = (bgcolour.Red() + bgcolour.Green() + bgcolour.Blue()) // 3

        if avg > 127:
            DIFF = 24
            tabcolour = wx.Colour(max((bgcolour.Red() - DIFF, 0)),
                                          max((bgcolour.Green() - DIFF, 0)),
                                          max((bgcolour.Blue() - DIFF, 0)))
        else:
            DIFF = 48
            tabcolour = wx.Colour(min((bgcolour.Red() + DIFF, 255)),
                                        min((bgcolour.Green() + DIFF, 255)),
                                        min((bgcolour.Blue() + DIFF, 255)))

        self.SetTabAreaColour(bgcolour)

        # This is probably ineffective with the used style
        self.SetActiveTabColour(tabcolour)

        # Top gradient colour of the active tab
        self.SetGradientColourTo(tabcolour)

        # Border on top of the active tab
        self.SetGradientColourBorder(self.GetBorderColour())

        # Bottom gradient colour of the active tab AND colour of the top border
        # of the whole page
        self.SetGradientColourFrom(bgcolour)

        self.SetActiveTabTextColour(self.GetForegroundColour())

    def _popup_tab_menu(self, event):
        # Select the clicked tab, as many actions are executed on the
        # "selected" tab, which may not be the "right-clicked" one
        # Of course the selection must be set *before* enabling/disabling the
        # actions in the context menu
        self.SetSelection(event.GetSelection())

        try:
            cmenu = self.GetCurrentPage().get_tab_context_menu()
        except AttributeError:
            pass
        else:
            self.SetRightClickMenu(cmenu)

    def select_page(self, index):
        self.SetSelection(index)

    def get_selected_tab_index(self):
        # Returns -1 if there's no tab
        return self.GetSelection()

    def get_selected_tab(self):
        return self.GetCurrentPage()

    def get_page_count(self):
        return self.GetPageCount()


class LeftNotebook(Notebook):
    def __init__(self, parent):
        Notebook.__init__(self, parent)

        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                                    self._handle_page_closing)
        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSED,
                                                    self._handle_page_closed)

    def _handle_page_closing(self, event):
        # Veto the event, page deletion is managed explicitly later
        event.Veto()

        if core_api.block_databases():
            page = self.GetCurrentPage()
            databases.close_database(page.get_filename())
            core_api.release_databases()

    def _handle_page_closed(self, event):
        if self.GetPageCount() == 0:
            self.parent.unsplit_window()
            self.Show(False)

    def add_page(self, window, caption, select=True):
        self.AddPage(window, caption, select=select)
        self.parent.split_window()

    def close_page(self, pageid):
        # self.DeletePage signals EVT_FLATNOTEBOOK_PAGE_CLOSING, so it's
        # necessary to unbind self._handle_page_closing, otherwise this would
        # enter an infinite recursion
        self.Unbind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                            handler=self._handle_page_closing)
        self.DeletePage(pageid)
        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                                    self._handle_page_closing)


class RightNotebook(Notebook):
    def __init__(self, parent):
        Notebook.__init__(self, parent)
        self.close_functions = {}

        self.imagelist = wx.ImageList(16, 16)
        self.AssignImageList(self.imagelist)

        self.editors = editor.Editors(self)

        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                                    self._handle_page_closing)
        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSED,
                                                    self._handle_page_closed)

    def _handle_page_closing(self, event):
        # Veto the event, page deletion is managed explicitly later
        event.Veto()

        if core_api.block_databases():
            page = self.GetCurrentPage()

            # This also prevents closing a plugin window
            for item in tuple(editor.tabs.keys()):
                if editor.tabs[item].panel is page:
                    editor.tabs[item].close()
                    break
            else:
                # Note that this event is also bound directly by the dbprops
                # module
                plugin_close_event.signal(page=page)

            core_api.release_databases()

    def _handle_page_closed(self, event):
        self._unsplit()

    def _split(self):
        if self.parent.nb_left.GetPageCount() > 0:
            self.parent.split_window()

    def _unsplit(self):
        if self.GetPageCount() == 0:
            self.parent.unsplit_window()

    # wx.NO_IMAGE, which is used in the docs, seems not to exist...
    def add_page(self, window, caption, close, closeArgs=(), select=True,
                                                        imageId=wx.NOT_FOUND):
        self.AddPage(window, text=caption, select=select, imageId=imageId)
        self.close_functions[window] = (close, closeArgs)
        self._split()

    # wx.NO_IMAGE, which is used in the docs, seems not to exist...
    def add_plugin(self, window, caption, close, closeArgs=(), select=True,
                                                        imageId=wx.NOT_FOUND):
        self.InsertPage(0, window, text=caption, select=select,
                                                            imageId=imageId)
        self.close_functions[window] = (close, closeArgs)
        self._split()

    def add_image(self, image):
        return self.imagelist.Add(image)

    def set_page_image(self, page, index):
        return self.SetPageImage(self.GetPageIndex(page), index)

    def set_editor_title(self, item, title):
        self.SetPageText(self.GetPageIndex(editor.tabs[item].panel),
                         text=title)

    def set_page_title(self, window, title):
        self.SetPageText(self.GetPageIndex(window), text=title)

    def get_selected_editor(self):
        tab = self.get_selected_tab()

        for item in editor.tabs:
            if editor.tabs[item].panel is tab:
                return item
        else:
            return False

    def get_open_editors(self):
        return [self.GetPageIndex(editor.tabs[item].panel)
                                                       for item in editor.tabs]

    def hide_page(self, pageid):
        # self.RemovePage signals EVT_FLATNOTEBOOK_PAGE_CLOSING, so it's
        # necessary to unbind self._handle_page_closing, otherwise this would
        # enter an infinite recursion
        self.Unbind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                            handler=self._handle_page_closing)
        self.RemovePage(pageid)

        # EVT_FLATNOTEBOOK_PAGE_CLOSED is not called after self.RemovePage
        self._unsplit()

        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                                    self._handle_page_closing)

    def close_tab(self, tab):
        fn, args = self.close_functions[tab]
        fn(*args)

    def close_page(self, pageid):
        # self.DeletePage signals EVT_FLATNOTEBOOK_PAGE_CLOSING, so it's
        # necessary to unbind self._handle_page_closing, otherwise this would
        # enter an infinite recursion
        self.Unbind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                            handler=self._handle_page_closing)
        self.DeletePage(pageid)
        self.Bind(flatnotebook.EVT_FLATNOTEBOOK_PAGE_CLOSING,
                                                    self._handle_page_closing)
