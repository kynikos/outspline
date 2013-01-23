# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import wx

import organism.extensions.development_api as development_api
import organism.interfaces.wxgui_api as wxgui_api


class MenuDev(wx.Menu):
    ID_POPULATE = None
    populate = None
    ID_PRINT = None
    printtb = None
        
    def __init__(self):
        wx.Menu.__init__(self)
        
        self.ID_POPULATE = wx.NewId()
        self.ID_PRINT = wx.NewId()
        
        self.populate = self.Append(self.ID_POPULATE, "&Populate database")
        self.printtb = self.Append(self.ID_PRINT, "Print &tables")
        
        wxgui_api.insert_menu_main_item('Developmen&t', 'Help', self)

        wxgui_api.bind_to_menu(self.populate_tree, self.populate)
        wxgui_api.bind_to_menu(self.print_tables, self.printtb)
        
        development_api.bind_to_populate_tree(self.handle_populate_tree)
    
    def handle_populate_tree(self, kwargs):
        items = kwargs['treeitems']
        for item in items:
            if item['mode'] == 'child':
                wxgui_api.append_item(item['filename'], item['baseid'],
                                      item['id_'], item['text'])
            elif item['mode'] == 'sibling':
                wxgui_api.insert_item_after(item['filename'], item['baseid'],
                                            item['id_'], item['text'])
        
    def populate_tree(self, event):
        db = wxgui_api.get_active_database()
        if db:
            filename = db.get_filename()
            if filename:
                development_api.populate_tree(filename)
                wxgui_api.refresh_history(filename)
        
    def print_tables(self, event):
        development_api.print_tables()


def main():
    MenuDev()
