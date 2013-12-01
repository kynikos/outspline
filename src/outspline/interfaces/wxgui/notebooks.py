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

import wx.lib.agw.aui as aui

import outspline.core_api as core_api

import editor
import databases


class Notebook(aui.AuiNotebook):
    parent = None

    def __init__(self, parent, agwStyle):
        aui.AuiNotebook.__init__(self, parent, agwStyle=agwStyle)

        self.parent = parent

        # aui.FF2TabArt seems to be the best compromise to support both
        # dark-on-light and light-on-dark GTK themes
        self.SetArtProvider(aui.FF2TabArt())

        self.Bind(aui.EVT_AUINOTEBOOK_END_DRAG, self.reset_focus)
        self.Bind(aui.EVT_AUINOTEBOOK_TAB_RIGHT_DOWN, self.popup_tab_menu)

    def reset_focus(self, event):
        # This workaround is necessary for a bug in moving tabs
        self.SetSelection(event.GetSelection())

        # Also reset focus, otherwise for example the menus will be disabled
        # after dragging
        self.GetPage(event.GetSelection()).SetFocus()

    def popup_tab_menu(self, event):
        # Select the clicked tab, as many actions are executed on the
        # "selected" tab, which may not be the "right-clicked" one
        # Of course the selection must be set *before* enabling/disabling the
        # actions in the context menu
        self.SetSelection(event.GetSelection())

        try:
            cmenu = self.GetPage(event.GetSelection()).get_tab_context_menu()
        except AttributeError:
            pass
        else:
            self.PopupMenu(cmenu)

    def add_page(self, window, caption, select=True):
        self.AddPage(window, caption, select=select)
        self.parent.split_window()

    def close_page(self, pageid):
        self.DeletePage(pageid)

        if self.GetPageCount() == 0:
            self.parent.unsplit_window()

    def select_page(self, index):
        self.SetSelection(index)

    def get_selected_tab_index(self):
        # Returns -1 if there's no tab
        return self.GetSelection()

    def get_selected_tab(self):
        try:
            return self.GetPage(self.GetSelection())
        except IndexError:
            return False

    def get_tabs(self):
        tabs = []
        for idx in range(self.GetPageCount()):
            tabs.append(self.GetPage(idx))
        return tabs


class LeftNotebook(Notebook):
    def __init__(self, parent):
        Notebook.__init__(self, parent, agwStyle=aui.AUI_NB_TOP |
                          aui.AUI_NB_SCROLL_BUTTONS | aui.AUI_NB_TAB_MOVE |
                          aui.AUI_NB_CLOSE_ON_ACTIVE_TAB |
                          aui.AUI_NB_NO_TAB_FOCUS |
                          aui.AUI_NB_WINDOWLIST_BUTTON)

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.handle_page_close)

    def handle_page_close(self, event):
        core_api.block_databases()
        # Veto the event, page deletion is managed explicitly later
        event.Veto()
        page = self.GetPage(event.GetSelection())
        databases.close_database(page.get_filename())
        core_api.release_databases()


class RightNotebook(Notebook):
    def __init__(self, parent):
        Notebook.__init__(self, parent, agwStyle=aui.AUI_NB_TOP |
                          aui.AUI_NB_SCROLL_BUTTONS | aui.AUI_NB_TAB_MOVE |
                          aui.AUI_NB_CLOSE_ON_ALL_TABS |
                          aui.AUI_NB_NO_TAB_FOCUS)

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.handle_page_close)

    def handle_page_close(self, event):
        core_api.block_databases()
        # Veto the event, page deletion is managed explicitly later
        event.Veto()
        page = self.GetPage(event.GetSelection())
        for item in tuple(editor.tabs.keys()):
            if editor.tabs[item].panel is page:
                editor.tabs[item].close()
        core_api.release_databases()

    def add_plugin(self, window, caption, close=True):
        self.AddPage(window, caption=caption)
        if not close:
            self.SetCloseButton(self.GetPageIndex(window), False)

    def set_editor_title(self, item, title):
        self.SetPageText(self.GetPageIndex(editor.tabs[item].panel),
                         text=title)

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
