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

import os.path
import wx

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import Event
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api

reset_menu_event = Event()
create_menu_event = Event()

trayicon = None


class TrayIcon(wx.TaskBarIcon):
    ID_MINIMIZE = None
    icon = None
    menu = None

    def __init__(self):
        wx.TaskBarIcon.__init__(self)
        self.ID_MINIMIZE = wx.NewId()

        config = coreaux_api.get_plugin_configuration('wxtrayicon')

        self.icon = BlinkingIcon(self)

        menumin = wx.MenuItem(wxgui_api.get_menu_file(), self.ID_MINIMIZE,
                                    '&Minimize to tray\tCTRL+m',
                                    'Minimize the main window to tray icon')

        menumin.SetBitmap(wx.ArtProvider.GetBitmap('@tray', wx.ART_MENU))

        wxgui_api.add_menu_file_item(menumin)

        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self._handle_left_click)
        self.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self._handle_right_click)
        wxgui_api.bind_to_close_window(self.hide_main_window)
        wxgui_api.bind_to_menu(self.hide_main_window, menumin)
        core_api.bind_to_exit_app_2(self.remove)

    def _handle_left_click(self, event):
        # If the icon is blinking, a left click shouldn't toggle the main
        # window's shown state
        if self.icon.is_blinking():
            self.icon.force_stop()
        else:
            wxgui_api.toggle_main_window()

    def _handle_right_click(self, event):
        self.icon.force_stop()

        # Skipping the event will let the click also popup the context menu
        event.Skip()

    def hide_main_window(self, event):
        wxgui_api.hide_main_window()

    def CreatePopupMenu(self):
        # TrayMenu must be instantiated here, everytime CreatePopupMenu is
        # called
        self.menu = TrayMenu(self)

        create_menu_event.signal(menu=self.menu)

        self.menu.update_items()

        return self.menu

    def remove(self, kwargs):
        self.icon.force_stop()
        self.RemoveIcon()


class BlinkingIcon():
    TOOLTIP = None
    DELAY = None
    trayicon = None
    main_icon = None
    default_alternative_icon = None
    current_icon = None
    current_tooltip = None
    timer = None
    start_id = None
    blinking_icons = None
    tooltips = None

    def __init__(self, trayicon):
        self.DELAY = 1000

        self.trayicon = trayicon

        self.main_icon = wx.ArtProvider.GetIcon('text-editor', wx.ART_OTHER)
        self.default_alternative_icon = wx.ArtProvider.GetIcon('@blinkicon',
                                                                wx.ART_OTHER)

        self.current_tooltip = 'Outspline'
        self.tooltips = {}
        self._reset(self.main_icon)

        # Initialize self.timer with a dummy function (int)
        self.timer = wx.CallLater(1, int)

    def _reset(self, icon):
        # Don't set self.current_tooltip here, in order to avoid race
        # conditions with the blinking timer
        self.current_icon = icon
        self.trayicon.SetIcon(icon, tooltip=self.current_tooltip)

    def start(self, start_id, alt_icon=None):
        self.timer.Stop()
        self.start_id = start_id

        if not alt_icon:
            alt_icon = self.default_alternative_icon

        self.blinking_icons = [self.main_icon, alt_icon]
        self._reset(alt_icon)
        self.timer = wx.CallLater(self.DELAY, self._restart)

    def _restart(self):
        self._reset(self.blinking_icons[0])
        self.blinking_icons.reverse()
        self.timer.Restart()

    def stop(self, start_id):
        if start_id == self.start_id:
            self.force_stop()

    def force_stop(self):
        self.timer.Stop()
        self._reset(self.main_icon)

    def is_blinking(self):
        return self.timer.IsRunning()

    def set_tooltip_value(self, tooltip_id, value):
        self.tooltips[tooltip_id] = value
        self._refresh_tooltip()

    def unset_tooltip_value(self, tooltip_id):
        del self.tooltips[tooltip_id]
        self._refresh_tooltip()

    def _refresh_tooltip(self):
        tooltip = "Outspline"

        for id_ in self.tooltips:
            tooltip += "\n" + self.tooltips[id_]

        # Set self.current_tooltip here, in order to avoid race conditions with
        # the blinking timer
        self.current_tooltip = tooltip

        self._reset(self.current_icon)


class TrayMenu(wx.Menu):
    ID_RESTORE = None
    restore = None
    exit_ = None

    def __init__(self, parent):
        wx.Menu.__init__(self)

        # Let self.restore have a different ID from menumin in the main menu,
        # in fact this is a check item, while the other is a normal item
        self.ID_RESTORE = wx.NewId()

        self.restore = self.AppendCheckItem(self.ID_RESTORE, "&Show Outspline")
        self.AppendSeparator()
        self.exit_ = self.Append(wx.ID_EXIT, "E&xit\tCTRL+q")

        parent.Bind(wx.EVT_MENU, self.toggle_main_window, self.restore)
        parent.Bind(wx.EVT_MENU, self.exit_application, self.exit_)

    def toggle_main_window(self, event):
        wxgui_api.toggle_main_window()

    def exit_application(self, event):
        wxgui_api.exit_application()

    def reset_items(self):
        self.restore.Check(check=wxgui_api.is_shown())

        reset_menu_event.signal()

    def update_items(self):
        self.reset_items()


def main():
    global trayicon
    trayicon = TrayIcon()
