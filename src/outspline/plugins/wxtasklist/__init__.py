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

import outspline.coreaux_api as coreaux_api
import outspline.interfaces.wxgui_api as wxgui_api

import list as list_
import filters
import menus


class TaskListPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

    def init_tab_menu(self, tasklist):
        self.ctabmenu = menus.TabContextMenu(tasklist)

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu


class TaskList(object):
    def __init__(self, parent):
        self.TAB_TITLE = "Occurrences"
        # Note that the remaining border is due to the SplitterWindow, whose
        # border cannot be removed because it's used to highlight the sash
        # See also http://trac.wxwidgets.org/ticket/12413
        # and http://trac.wxwidgets.org/changeset/66230
        self.panel = TaskListPanel(parent)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

        # filters.Navigator must be instantiated *before*
        # list_.OccurrencesView, because the former sets the filter for the
        # latter; note that inverting the order would work anyway because of a
        # usually favorable race condition (the list is refreshed after an
        # asynchronous delay), but of course that shouldn't be relied on
        self.navigator = filters.Navigator(self)
        self.list_ = list_.OccurrencesView(self, self.navigator)

        self.mainmenu = menus.MainMenu(self)
        self.panel.init_tab_menu(self)
        self.list_._init_context_menu(self.mainmenu)

        self.pbox.Add(self.list_.listview, 1, flag=wx.EXPAND)

        wxgui_api.bind_to_plugin_close_event(self._handle_tab_hide)
        wxgui_api.bind_to_show_main_window(self._handle_show_main_window)
        wxgui_api.bind_to_hide_main_window(self._handle_hide_main_window)
        wxgui_api.bind_to_open_database(self._handle_open_database)
        wxgui_api.bind_to_exit_application(self._handle_exit_application)

    def _handle_tab_hide(self, kwargs):
        if kwargs['page'] is self.panel:
            self._hide()

    def _handle_show_main_window(self, kwargs):
        if self.is_shown():
            self._enable()

    def _handle_hide_main_window(self, kwargs):
        if self.is_shown():
            self._disable()

    def _handle_open_database(self, kwargs):
        # Do not add the plugin if there's no database open, otherwise strange
        # bugs will happen, like the keyboard menu shortcuts not working until
        # a database is opened. Add the plugin only when the first database is
        # opened.
        wxgui_api.add_plugin_to_right_nb(self.panel, self.TAB_TITLE)
        wxgui_api.bind_to_open_database(self._handle_open_database, False)

    def is_shown(self):
        return wxgui_api.is_page_in_right_nb(self.panel)

    def toggle_shown(self, event):
        if self.is_shown():
            self._hide()
        else:
            self._show()

    def _show(self):
        wxgui_api.add_plugin_to_right_nb(self.panel, self.TAB_TITLE)
        self._enable()

    def _hide(self):
        # Showing/hiding is the correct behaviour: allowing multiple instances
        # of tasklist notebook tabs would need finding a way to refresh only
        # one at a time, probably only the selected one, thus requiring to
        # update it every time it gets selected, which would in turn make
        # everything more sluggish
        wxgui_api.hide_right_nb_page(self.panel)
        self._disable()

    def _enable(self):
        self.list_.enable_refresh()
        self.list_.delay_restart()

    def _disable(self):
        self.list_.disable_refresh()

    def _handle_exit_application(self, kwargs):
        configfile = coreaux_api.get_user_config_file()
        self.list_.save_configuration()
        self.navigator.save_configuration()
        self.config.export_upgrade(configfile)


def main():
    TaskList(wxgui_api.get_right_nb())
