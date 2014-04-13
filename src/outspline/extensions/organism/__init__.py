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

_ADDON_NAME = ('Extensions', 'organism')


def create_copy_table():
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copyrules_create)
    core_api.give_memory_connection(mem)


def handle_create_database(kwargs):
    # Cannot use core_api.get_connection() here because the database isn't
    # open yet
    conn = sqlite3.connect(kwargs['filename'])
    cur = conn.cursor()
    cur.execute(queries.rules_create)
    conn.commit()
    conn.close()


def handle_open_database_dirty(kwargs):
    info = coreaux_api.get_addons_info()
    dependencies = info(_ADDON_NAME[0])(_ADDON_NAME[1]
                                    )['database_dependency_group_1'].split(' ')

    if not set(dependencies) - set(kwargs['dependencies']):
        items.cdbs.add(kwargs['filename'])


def handle_open_database(kwargs):
    filename = kwargs['filename']

    if filename in items.cdbs:
        core_api.register_history_action_handlers(filename, 'rules_insert',
                    items.handle_history_insert, items.handle_history_delete)
        core_api.register_history_action_handlers(filename, 'rules_update',
                    items.handle_history_update, items.handle_history_update)
        core_api.register_history_action_handlers(filename, 'rules_delete',
                    items.handle_history_delete, items.handle_history_insert)


def handle_save_database_copy(kwargs):
    if kwargs['origin'] in items.cdbs:
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


def handle_close_database(kwargs):
    items.cdbs.discard(kwargs['filename'])


def handle_insert_item(kwargs):
    items.insert_item(kwargs['filename'], kwargs['id_'], kwargs['group'],
                                                        kwargs['description'])


def handle_delete_item(kwargs):
    items.delete_item_rules(kwargs['filename'], kwargs['id_'], kwargs['text'],
                                        kwargs['group'], kwargs['description'])


def handle_copy_items(kwargs):
    # Do not check if kwargs['filename'] is in cdbs, always clear the table as
    # the other functions rely on the table to be clear
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copyrules_delete)
    core_api.give_memory_connection(mem)


def handle_copy_item(kwargs):
    items.copy_item_rules(kwargs['filename'], kwargs['id_'])


def handle_paste_item(kwargs):
    items.paste_item_rules(kwargs['filename'], kwargs['id_'], kwargs['oldid'],
                                        kwargs['group'], kwargs['description'])


def handle_safe_paste_check(kwargs):
    items.can_paste_safely(kwargs['filename'], kwargs['exception'])


def main():
    create_copy_table()

    core_api.bind_to_create_database(handle_create_database)
    core_api.bind_to_open_database_dirty(handle_open_database_dirty)
    core_api.bind_to_open_database(handle_open_database)
    core_api.bind_to_save_database_copy(handle_save_database_copy)
    core_api.bind_to_close_database(handle_close_database)
    core_api.bind_to_insert_item(handle_insert_item)
    core_api.bind_to_delete_item(handle_delete_item)
    if copypaste_api:
        copypaste_api.bind_to_copy_items(handle_copy_items)
        copypaste_api.bind_to_copy_item(handle_copy_item)
        copypaste_api.bind_to_paste_item(handle_paste_item)
        copypaste_api.bind_to_safe_paste_check(handle_safe_paste_check)
