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

import sqlite3

import organism.coreaux_api as coreaux_api
import organism.core_api as core_api
copypaste_api = coreaux_api.import_extension_api('copypaste')

import queries
import items


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


def handle_save_database_copy(kwargs):
    qconn = core_api.get_connection(kwargs['origin'])
    qconnd = sqlite3.connect(kwargs['destination'])
    cur = qconn.cursor()
    curd = qconnd.cursor()
    
    cur.execute(queries.rules_select)
    for row in cur:
        curd.execute(queries.rules_insert_copy, tuple(row))
        
    core_api.give_connection(kwargs['origin'], qconn)
    
    qconnd.commit()
    qconnd.close()


def handle_insert_item(kwargs):
    items.insert_item(kwargs['filename'], kwargs['id_'], kwargs['group'],
                      kwargs['description'])


def handle_delete_item(kwargs):
    items.delete_item_rules(kwargs['filename'], kwargs['id_'], kwargs['group'],
                            kwargs['description'])


def handle_copy_items(kwargs):
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copyrules_delete)
    core_api.give_memory_connection(mem)


def handle_copy_item(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']
    
    items.copy_item_rules(filename, id_)


def handle_paste_item(kwargs):
    items.paste_item_rules(kwargs['filename'], kwargs['id_'], kwargs['oldid'],
                           kwargs['group'], kwargs['description'])


def main():
    create_copy_table()
    
    core_api.bind_to_create_database(handle_create_database)
    core_api.bind_to_save_database_copy(handle_save_database_copy)
    core_api.bind_to_insert_item(handle_insert_item)
    core_api.bind_to_delete_item(handle_delete_item)
    if copypaste_api:
        copypaste_api.bind_to_copy_items(handle_copy_items)
        copypaste_api.bind_to_copy_item(handle_copy_item)
        copypaste_api.bind_to_paste_item(handle_paste_item)
