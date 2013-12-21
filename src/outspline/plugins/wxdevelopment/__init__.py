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

import os as _os
import random
import wx

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.development_api as development_api
import outspline.interfaces.wxgui_api as wxgui_api
organism_api = coreaux_api.import_optional_extension_api('organism')
links_api = coreaux_api.import_optional_extension_api('links')
wxscheduler_basicrules_api = coreaux_api.import_optional_plugin_api(
                                                    'wxscheduler_basicrules')
wxlinks_api = coreaux_api.import_optional_plugin_api('wxlinks')

import simulator
import tests


class MenuDev(wx.Menu):
    populate = None
    simulator = None
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
        self.simulator = self.AppendCheckItem(wx.NewId(), "&Run simulator")

        wxgui_api.insert_menu_main_item('Develo&pment', 'Help', self)

        wxgui_api.bind_to_menu(self.populate_tree, self.populate)
        wxgui_api.bind_to_menu(self.toggle_simulator, self.simulator)

        wxgui_api.bind_to_update_menu_items(self.update_items)

    def update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.reset_print_menu()
            self.reset_simulator_item()

    def reset_print_menu(self):
        self.Delete(self.ID_PRINT)
        self.ID_PRINT = wx.NewId()
        self.printtb = wx.Menu()
        self.PrependMenu(self.ID_PRINT, "Print &databases", self.printtb)

        self.all_ = self.printtb.Append(wx.NewId(), 'All databases')
        wxgui_api.bind_to_menu(self.print_all_databases, self.all_)

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
            wxgui_api.bind_to_menu(self.print_all_tables_loop(filename),
                                   self.databases[filename]['all_'])

            self.databases[filename]['menu'].AppendSeparator()

            for table in core_api.select_all_table_names(filename):
                self.databases[filename]['tables'][table[0]] = \
                                    self.databases[filename]['menu'].Append(
                                    wx.NewId(), table[0])
                wxgui_api.bind_to_menu(self.print_table_loop(filename,
                                table[0]),
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
        wxgui_api.bind_to_menu(self.print_all_memory_tables,
                                                        self.memory['all_'])

        self.memory['menu'].AppendSeparator()

        for table in core_api.select_all_memory_table_names():
            self.memory['tables'][table[0]] = self.memory['menu'].Append(
                                                        wx.NewId(), table[0])
            wxgui_api.bind_to_menu(self.print_memory_table_loop(table[0]),
                                   self.memory['tables'][table[0]])

    def print_all_databases(self, event):
        core_api.block_databases()
        development_api.print_all_databases()
        core_api.release_databases()

    def print_all_memory_tables(self, event):
        core_api.block_databases()
        development_api.print_all_memory_tables()
        core_api.release_databases()

    def print_memory_table_loop(self, table):
        return lambda event: self.print_memory_table(table)

    def print_table_loop(self, filename, table):
        return lambda event: self.print_table(filename, table)

    def print_all_tables_loop(self, filename):
        return lambda event: self.print_all_tables(filename)

    def print_memory_table(self, table):
        core_api.block_databases()
        development_api.print_memory_table(table)
        core_api.release_databases()

    def print_table(self, filename, table):
        core_api.block_databases()
        development_api.print_table(filename, table)
        core_api.release_databases()

    def print_all_tables(self, filename):
        core_api.block_databases()
        development_api.print_all_tables(filename)
        core_api.release_databases()

    def populate_tree(self, event):
        core_api.block_databases()
        db = wxgui_api.get_active_database()
        if db:
            filename = db.get_filename()
            if filename:
                group = core_api.get_next_history_group(filename)
                description = 'Populate tree'

                i = 0
                while i < 10:
                    dbitems = core_api.get_items_ids(filename)

                    try:
                        itemid = random.choice(dbitems)
                    except IndexError:
                        # No items in the database yet
                        itemid = 0

                    mode = random.choice(('child', 'sibling'))

                    if mode == 'sibling' and itemid == 0:
                        continue

                    i += 1

                    text = self._populate_tree_text()

                    id_ = self._populate_tree_item(mode, filename, itemid,
                                                    group, text, description)

                    if organism_api and wxscheduler_basicrules_api and \
                            filename in \
                            organism_api.get_supported_open_databases():
                        self._populate_tree_rules(filename, id_, group,
                                                            description)

                    self._populate_tree_gui(mode, filename, itemid, id_, text)

                    # Links must be created *after* self._populate_tree_gui
                    if links_api and wxlinks_api and filename in \
                                    links_api.get_supported_open_databases():
                            self._populate_tree_link(filename, id_, dbitems,
                                                            group, description)

                wxgui_api.refresh_history(filename)
        core_api.release_databases()

    def _populate_tree_text(self):
        text = ''
        words = ('the quick brown fox jumps over the lazy dog ' * 6).split()
        seps = ' ' * 6 + '\n'

        for x in range(random.randint(10, 100)):
            words.append(str(random.randint(0, 100)))
            text = ''.join((text, random.choice(words), random.choice(seps)))

        return ''.join((text, random.choice(words))).capitalize()

    def _populate_tree_item(self, mode, filename, itemid, group, text,
                                                                description):
        if mode == 'child':
            return core_api.append_item(filename, itemid, group, text=text,
                                                    description=description)
        elif mode == 'sibling':
            return core_api.insert_item_after(filename, itemid, group,
                                            text=text, description=description)

    def _populate_tree_rules(self, filename, id_, group, description):
        rules = []

        for n in range(random.randint(0, 8)):
            r = random.randint(0, 16)

            if r == 0:
                rule = \
                      wxscheduler_basicrules_api.create_random_occur_once_rule()
            elif r == 1:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_interval_rule()
            elif r == 2:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_day_rule()
            elif r == 3:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_week_rule()
            elif r == 4:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_selected_weekdays_rule()
            elif r == 5:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_selected_months_rule()
            elif r == 6:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_selected_months_inverse_rule()
            elif r == 7:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_selected_months_weekday_rule()
            elif r == 8:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_selected_months_weekday_inverse_rule()
            elif r == 9:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_month_rule()
            elif r == 10:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_month_inverse_rule()
            elif r == 11:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_month_weekday_rule()
            elif r == 12:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_month_weekday_inverse_rule()
            elif r == 13:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_every_synodic_month_rule()
            elif r == 14:
                rule = \
                    wxscheduler_basicrules_api.create_random_occur_yearly_rule()
            elif r == 15:
                rule = \
                     wxscheduler_basicrules_api.create_random_except_once_rule()
            else:
                rule = \
                    wxscheduler_basicrules_api.create_random_except_every_interval_rule()

            rules.append(rule)

        organism_api.update_item_rules(filename, id_, rules, group,
                                                    description=description)

    def _populate_tree_link(self, filename, id_, dbitems, group, description):
        if random.randint(0, 8) == 0:
            # This gives a chance that target will be the same as id_, but it's
            # negligible, especially with large numbers of items
            target = random.choice(dbitems)
            links_api.make_link(filename, id_, target, group, description)
            wxlinks_api.update_items_formatting(filename)

    def _populate_tree_gui(self, mode, filename, itemid, id_, text):
        if mode == 'child':
            wxgui_api.append_item(filename, itemid, id_, text)
        elif mode == 'sibling':
            wxgui_api.insert_item_after(filename, itemid, id_, text)

    def reset_simulator_item(self):
        if simulator.is_active():
            self.simulator.Check(True)
        else:
            self.simulator.Check(False)

    def toggle_simulator(self, event):
        if simulator.is_active():
            simulator.stop()
        else:
            simulator.start()


def main():
    MenuDev()
    core_api.bind_to_exit_app_1(simulator.stop)
    tests.main()
