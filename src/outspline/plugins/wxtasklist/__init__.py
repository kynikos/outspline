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
import outspline.interfaces.wxgui_api as wxgui_api

import list as list_
import filters


class TaskListPanel(wx.Panel):
    ctabmenu = None

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)

    def _init_tab_menu(self, tasklist):
        self.ctabmenu = TabContextMenu(tasklist)

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu


class TaskList():
    CAPTION = None
    panel = None
    pbox = None
    config = None
    list_ = None
    filters = None
    ID_SHOW = None
    menushow = None

    def __init__(self, parent):
        # Note that the remaining border is due to the SplitterWindow, whose
        # border cannot be removed because it's used to highlight the sash
        # See also http://trac.wxwidgets.org/ticket/12413
        # and http://trac.wxwidgets.org/changeset/66230
        self.panel = TaskListPanel(parent)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

        self.CAPTION = 'Occurrences'

        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

        self.list_ = list_.OccurrencesView(self.panel)
        self.filters = filters.Filters(self.panel, self.list_)

        self.panel._init_tab_menu(self)

        self._init_view_menu()

        self.pbox.Add(self.filters.panel, flag=wx.EXPAND | wx.ALL, border=2)
        self.pbox.Add(self.list_.listview, 1, flag=wx.EXPAND | wx.ALL,
                                                                      border=2)

        wxgui_api.bind_to_plugin_close_event(self.handle_tab_hide)
        wxgui_api.bind_to_menu_view_update(self.update_menu_items)
        wxgui_api.bind_to_show_main_window(self.handle_show_main_window)
        wxgui_api.bind_to_hide_main_window(self.handle_hide_main_window)

    def _init_view_menu(self):
        self.ID_SHOW = wx.NewId()
        self.menushow = wxgui_api.insert_menu_item('View',
                                       self.config.get_int('show_menu_pos'),
                                       'Show &occurrences\tCTRL+SHIFT+F5',
                                       id_=self.ID_SHOW,
                                       help='Show the occurrences window',
                                       kind='check',
                                       sep=self.config['show_menu_sep'])

        wxgui_api.bind_to_menu(self.toggle_shown, self.menushow)

    def update_menu_items(self, event):
        self.menushow.Check(check=self.is_shown())

    def handle_tab_hide(self, kwargs):
        if kwargs['page'] is self.panel:
            self.hide()

    def is_shown(self):
        return wxgui_api.is_page_in_right_nb(self.panel)

    def handle_show_main_window(self, event):
        if self.is_shown():
            self._enable()

    def handle_hide_main_window(self, event):
        if self.is_shown():
            self._disable()

    def toggle_shown(self, event):
        if self.is_shown():
            self.hide()
        else:
            self.show()

    def show(self):
        wxgui_api.add_plugin_to_right_nb(self.panel, self.CAPTION)
        self._enable()

    def hide(self):
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


class TabContextMenu(wx.Menu):
    tasklist = None
    snooze_all = None
    dismiss_all = None

    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.snooze_all = wx.MenuItem(self,
                     self.tasklist.list_.mainmenu.ID_SNOOZE_ALL, "S&nooze all",
                        subMenu=list_.SnoozeAllConfigMenu(self.tasklist.list_))
        self.dismiss_all = wx.MenuItem(self,
                   self.tasklist.list_.mainmenu.ID_DISMISS_ALL, "&Dismiss all")

        self.snooze_all.SetBitmap(wx.ArtProvider.GetBitmap('@alarms',
                                                                  wx.ART_MENU))
        self.dismiss_all.SetBitmap(wx.ArtProvider.GetBitmap('@alarmoff',
                                                                  wx.ART_MENU))

        self.AppendItem(self.snooze_all)
        self.AppendItem(self.dismiss_all)

    def update(self):
        if len(self.tasklist.list_.activealarms) > 0:
            self.snooze_all.Enable()
            self.dismiss_all.Enable()
        else:
            self.snooze_all.Enable(False)
            self.dismiss_all.Enable(False)


def main():
    nb = wxgui_api.get_right_nb()
    tasklist = TaskList(nb)
    wxgui_api.add_plugin_to_right_nb(tasklist.panel, tasklist.CAPTION)
