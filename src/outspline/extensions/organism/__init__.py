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

import sqlite3

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import queries
import items

extension = None


class Main(object):
    def __init__(self):
        self._ADDON_NAME = ('Extensions', 'organism')

        self.rules = items.Rules()
        self.cdbs = set()
        self.databases = {}

        self._create_copy_table()

        core_api.bind_to_create_database(self._handle_create_database)
        core_api.bind_to_open_database_dirty(self._handle_open_database_dirty)
        core_api.bind_to_open_database(self._handle_open_database)
        core_api.bind_to_save_database_copy(self._handle_save_database_copy)
        core_api.bind_to_close_database(self._handle_close_database)
        core_api.bind_to_insert_item(self._handle_insert_item)
        core_api.bind_to_delete_item(self._handle_delete_item)

        if copypaste_api:
            copypaste_api.bind_to_copy_items(self._handle_copy_items)
            copypaste_api.bind_to_copy_item(self._handle_copy_item)
            copypaste_api.bind_to_paste_item(self._handle_paste_item)
            copypaste_api.bind_to_safe_paste_check(
                                                self._handle_safe_paste_check)

    def _create_copy_table(self):
        mem = core_api.get_memory_connection()
        cur = mem.cursor()
        cur.execute(queries.copyrules_create)
        core_api.give_memory_connection(mem)

    def _handle_create_database(self, kwargs):
        # Cannot use core_api.get_connection() here because the database isn't
        # open yet
        conn = sqlite3.connect(kwargs['filename'])
        cur = conn.cursor()
        cur.execute(queries.rules_create)
        conn.commit()
        conn.close()

    def _handle_open_database_dirty(self, kwargs):
        info = coreaux_api.get_addons_info()
        dependencies = info(self._ADDON_NAME[0])(self._ADDON_NAME[1]
                                    )['database_dependency_group_1'].split(' ')

        if not set(dependencies) - set(kwargs['dependencies']):
            self.cdbs.add(kwargs['filename'])

    def _handle_open_database(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename] = items.Database(filename)

    def _handle_save_database_copy(self, kwargs):
        if kwargs['origin'] in self.cdbs:
            qconn = core_api.get_connection(kwargs['origin'])
            qconnd = sqlite3.connect(kwargs['destination'])
            cur = qconn.cursor()
            curd = qconnd.cursor()

            cur.execute(queries.rules_select)
            for row in cur:
                curd.execute(queries.rules_insert, tuple(row))

            core_api.give_connection(kwargs['origin'], qconn)

            qconnd.commit()
            qconnd.close()

    def _handle_close_database(self, kwargs):
        filename = kwargs['filename']
        self.cdbs.discard(filename)
        del self.databases[filename]

    def _handle_insert_item(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].insert_item(kwargs['id_'],
                                        kwargs['group'], kwargs['description'])

    def _handle_delete_item(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].delete_item_rules(kwargs['id_'],
                        kwargs['text'], kwargs['group'], kwargs['description'])

    def _handle_copy_items(self, kwargs):
        # Do not check if kwargs['filename'] is in self.cdbs, always clear the
        # table as the other functions rely on the table to be clear
        mem = core_api.get_memory_connection()
        cur = mem.cursor()
        cur.execute(queries.copyrules_delete)
        core_api.give_memory_connection(mem)

    def _handle_copy_item(self, kwargs):
        filename = kwargs['filename']
        self.databases[filename].copy_item_rules(kwargs['id_'],
                                                        filename in self.cdbs)

    def _handle_paste_item(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].paste_item_rules(kwargs['id_'],
                    kwargs['oldid'], kwargs['group'], kwargs['description'])

    def _handle_safe_paste_check(self, kwargs):
        filename = kwargs['filename']
        self.databases[filename].can_paste_safely(kwargs['exception'],
                                                        filename in self.cdbs)


def main():
    global extension
    extension = Main()
