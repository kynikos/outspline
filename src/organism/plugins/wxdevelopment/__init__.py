# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import os as _os
import wx

import organism.core_api as core_api
import organism.extensions.development_api as development_api
import organism.interfaces.wxgui_api as wxgui_api


class MenuDev(wx.Menu):
    populate = None
    ID_PRINT = None
    printtb = None
    all_ = None
    databases = None
    memory = None

    def __init__(self):
        wx.Menu.__init__(self)

        # Initialize self.ID_PRINT so it can be deleted at the beginning of
        # self.handle_reset_menu_items
        self.ID_PRINT = wx.NewId()

        self.populate = self.Append(wx.NewId(), "&Populate database")

        wxgui_api.insert_menu_main_item('Developmen&t', 'Help', self)

        wxgui_api.bind_to_menu(self.populate_tree, self.populate)

        wxgui_api.bind_to_reset_menu_items(self.handle_reset_menu_items)
        development_api.bind_to_populate_tree(self.handle_populate_tree)


    def handle_reset_menu_items(self, kwargs):
        if kwargs['menu'] is self:
            self.Delete(self.ID_PRINT)
            self.ID_PRINT = wx.NewId()
            self.printtb = wx.Menu()
            self.PrependMenu(self.ID_PRINT, "Print &databases", self.printtb)

            self.all_ = self.printtb.Append(wx.NewId(), 'All databases')
            wxgui_api.bind_to_menu(lambda event:
                               development_api.print_all_databases(), self.all_)

            self.printtb.AppendSeparator()

            self.databases = {}

            for filename in core_api.get_open_databases():
                self.databases[filename] = {
                    'menu': wx.Menu(),
                    'all_': None,
                    'tables': {}
                }

                self.printtb.AppendMenu(wx.NewId(), _os.path.basename(filename),
                                        self.databases[filename]['menu'])

                self.databases[filename]['all_'] = self.databases[filename][
                                        'menu'].Append(wx.NewId(), 'All tables')
                wxgui_api.bind_to_menu(self.print_all_tables(filename),
                                       self.databases[filename]['all_'])

                self.databases[filename]['menu'].AppendSeparator()

                for table in core_api.select_all_table_names(filename):
                    self.databases[filename]['tables'][table[0]] = \
                                        self.databases[filename]['menu'].Append(
                                                           wx.NewId(), table[0])
                    wxgui_api.bind_to_menu(self.print_table(filename, table[0]),
                                   self.databases[filename]['tables'][table[0]])

            if self.databases:
                self.printtb.AppendSeparator()

            self.memory = {
                'menu': wx.Menu(),
                'all_': None,
                'tables': {}
            }

            self.printtb.AppendMenu(wx.NewId(), ':memory:', self.memory['menu'])

            self.memory['all_'] = self.memory['menu'].Append(wx.NewId(),
                                                             'All tables')
            wxgui_api.bind_to_menu(lambda event:
                                   development_api.print_all_memory_tables(),
                                   self.memory['all_'])

            self.memory['menu'].AppendSeparator()

            for table in core_api.select_all_memory_table_names():
                self.memory['tables'][table[0]] = self.memory['menu'].Append(
                                                           wx.NewId(), table[0])
                wxgui_api.bind_to_menu(self.print_memory_table(table[0]),
                                       self.memory['tables'][table[0]])

    def print_memory_table(self, table):
        return lambda event: development_api.print_memory_table(table)

    def print_table(self, filename, table):
        return lambda event: development_api.print_table(filename, table)

    def print_all_tables(self, filename):
        return lambda event: development_api.print_all_tables(filename)

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


def main():
    MenuDev()
