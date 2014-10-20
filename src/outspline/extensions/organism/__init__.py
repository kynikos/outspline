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

from outspline.coreaux_api import Event
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import queries
import items

database_open_event = Event()

extension = None


class Main(object):
    def __init__(self):
        self._ADDON_NAME = ('Extensions', 'organism')

        self.rules = items.Rules()
        self.databases = {}

        self._create_copy_table()

        core_api.bind_to_open_database_dirty(self._handle_open_database_dirty)
        core_api.bind_to_open_database(self._handle_open_database)
        core_api.bind_to_save_database_copy(self._handle_save_database_copy)
        core_api.bind_to_close_database(self._handle_close_database)
        core_api.bind_to_insert_item(self._handle_insert_item)
        core_api.bind_to_deleting_item(self._handle_delete_item)

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

    def _handle_open_database_dirty(self, kwargs):
        info = coreaux_api.get_addons_info()
        dependencies = info(self._ADDON_NAME[0])(self._ADDON_NAME[1]
                                    )['database_dependency_group_1'].split(' ')

        if not set(dependencies) - set(kwargs['dependencies']):
            filename = kwargs['filename']
            self.databases[filename] = items.Database(filename)

    def _handle_open_database(self, kwargs):
        filename = kwargs['filename']

        try:
            self.databases[filename].post_init()
        except KeyError:
            pass
        else:
            database_open_event.signal(filename=filename)

    def _handle_save_database_copy(self, kwargs):
        origin = kwargs['origin']

        if origin in self.databases:
            qconn = core_api.get_connection(origin)
            qconnd = sqlite3.connect(kwargs['destination'])
            cur = qconn.cursor()
            curd = qconnd.cursor()

            cur.execute(queries.rules_select)
            for row in cur:
                curd.execute(queries.rules_insert, tuple(row))

            core_api.give_connection(origin, qconn)

            qconnd.commit()
            qconnd.close()

    def _handle_close_database(self, kwargs):
        try:
            del self.databases[kwargs['filename']]
        except KeyError:
            pass

    def _handle_insert_item(self, kwargs):
        try:
            self.databases[kwargs['filename']].insert_item(kwargs['id_'],
                                        kwargs['group'], kwargs['description'])
        except KeyError:
            pass

    def _handle_delete_item(self, kwargs):
        try:
            self.databases[kwargs['filename']].delete_item_rules(kwargs['id_'],
                        kwargs['text'], kwargs['group'], kwargs['description'])
        except KeyError:
            pass

    def _handle_copy_items(self, kwargs):
        # Do not check if kwargs['filename'] is in self.databases, always clear
        # the table as the other functions rely on the table to be clear
        mem = core_api.get_memory_connection()
        cur = mem.cursor()
        cur.execute(queries.copyrules_delete)
        core_api.give_memory_connection(mem)

    def _handle_copy_item(self, kwargs):
        filename = kwargs['filename']
        id_ = kwargs['id_']
        record = [id_, ]

        try:
            db = self.databases[filename]
        except KeyError:
            # Even if the database doesn't support rules, create a correct
            # table that can be safely used when pasting
            record.append(items.Database.rules_to_string([]))
        else:
            record.extend(db.copy_item_rules(id_))

        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyrules_insert, record)
        core_api.give_memory_connection(mem)

    def _handle_paste_item(self, kwargs):
        try:
            self.databases[kwargs['filename']].paste_item_rules(kwargs['id_'],
                    kwargs['oldid'], kwargs['group'], kwargs['description'])
        except KeyError:
            pass

    def _handle_safe_paste_check(self, kwargs):
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyrules_select,
                                        (items.Database.rules_to_string([]), ))
        core_api.give_memory_connection(mem)

        # Warn if CopyRules table has rules but filename doesn't support them
        if curm.fetchone() and kwargs['filename'] not in self.databases:
            raise kwargs['exception']()


def main():
    global extension
    extension = Main()
