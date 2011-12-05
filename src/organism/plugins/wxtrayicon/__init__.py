# Organism - Organism, a simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import wx

import organism.coreaux_api as coreaux_api
from organism.coreaux_api import Event
import organism.core_api as core_api
import organism.interfaces.wxgui_api as wxgui_api

reset_menu_event = Event()
create_menu_event = Event()

trayicon = None


class TrayIcon(wx.TaskBarIcon):
    rootw = None
    ID_MINIMIZE = None
    menu = None
    
    def __init__(self, rootw):
        wx.TaskBarIcon.__init__(self)
        self.rootw = rootw
        self.ID_MINIMIZE = wx.NewId()
        
        self.SetIcon(wx.ArtProvider.GetIcon('text-editor', wx.ART_FRAME_ICON),
                     tooltip='Organism')
        
        config = coreaux_api.get_plugin_configuration('wxtrayicon')
        
        menumin = wxgui_api.insert_menu_item('File',
                                  config.get_int('menu_pos'),
                                  '&Minimize to tray\tCtrl+M',
                                  id_=self.ID_MINIMIZE,
                                  help='Minimize the main window to tray icon',
                                  sep=config['menu_sep'], icon='@tray')
        
        self.rootw.Bind(wx.EVT_CLOSE, self.rootw.hide)
        wxgui_api.bind_to_menu(self.rootw.hide, menumin)
        self.Bind(wx.EVT_TASKBAR_LEFT_UP, self.rootw.toggle_shown)
        core_api.bind_to_exit_app_2(self.remove)
    
    def CreatePopupMenu(self):
        # TrayMenu must be instantiated here, everytime CreatePopupMenu is
        # called
        self.menu = TrayMenu(self)
        
        create_menu_event.signal()
        
        self.menu.update_items()
        
        return self.menu
    
    def remove(self, kwargs):
        self.RemoveIcon()


class TrayMenu(wx.Menu):
    ID_RESTORE = None
    restore = None
    exit_ = None
    
    def __init__(self, parent):
        wx.Menu.__init__(self)
        
        # Let self.restore have a different ID from menumin in the main menu,
        # in fact this is a check item, while the other is a normal item
        self.ID_RESTORE = wx.NewId()
        
        self.restore = self.AppendCheckItem(self.ID_RESTORE, "&Show Organism")
        self.AppendSeparator()
        self.exit_ = self.Append(wx.ID_EXIT, "E&xit\tCtrl+Q")
        
        parent.Bind(wx.EVT_MENU, parent.rootw.toggle_shown, self.restore)
        parent.Bind(wx.EVT_MENU, wx.GetApp().exit_app, self.exit_)
    
    def insert_item(self, pos, text, id_=wx.ID_ANY, help='', sep='none',
                    kind='normal', sub=None, icon=None):
        kinds = {'normal': wx.ITEM_NORMAL,
                 'check': wx.ITEM_CHECK,
                 'radio': wx.ITEM_RADIO}
        
        item = wx.MenuItem(parentMenu=self, id=id_, text=text, help=help,
                           kind=kinds[kind], subMenu=sub)
        
        if icon is not None:
            item.SetBitmap(wx.ArtProvider.GetBitmap(icon, wx.ART_MENU))
        
        if pos == -1:
            if sep in ('up', 'both'):
                self.AppendSeparator()
            self.AppendItem(item)
            if sep in ('down', 'both'):
                self.AppendSeparator()
        else:
            # Start from bottom, so that it's always possible to use pos
            if sep in ('down', 'both'):
                self.InsertSeparator(pos)
            self.InsertItem(pos, item)
            if sep in ('up', 'both'):
                self.InsertSeparator(pos)
        return item
    
    def reset_items(self):
        self.restore.Check(check=wxgui_api.is_shown())
        
        reset_menu_event.signal()
        
    def update_items(self):
        self.reset_items()


def main():
    global trayicon
    trayicon = TrayIcon(wxgui_api.get_main_frame())
