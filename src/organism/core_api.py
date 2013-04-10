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

from core import databases, items, history, queries
from core.exceptions import (AccessDeniedError, DatabaseAlreadyOpenError,
                             DatabaseNotAccessibleError, DatabaseNotValidError)


def get_memory_connection():
    return databases.memory.get()


def give_memory_connection(conn):
    return databases.memory.give(conn)


def get_connection(filename):
    return databases.dbs[filename].connection.get()


def give_connection(filename, conn):
    return databases.dbs[filename].connection.give(conn)


def create_database(filename):
    return databases.Database.create(filename)


def open_database(filename):
    return databases.Database.open(filename)


def save_database(filename):
    return databases.dbs[filename].save()


def save_database_copy(origin, destination):
    return databases.dbs[origin].save_copy(destination)


def close_database(filename):
    return databases.dbs[filename].close()


def exit_():
    databases.memory.exit_()


def create_child(filename, baseid, text='New item',
                 description='Create child'):
    base = items.Item.make_itemid(filename, baseid)
    group = databases.dbs[filename].get_next_history_group()
    return items.Item.insert(mode='child', base=base, group=group, text=text,
                             description=description)


def create_sibling(filename, baseid, text='New item',
                   description='Create sibling'):
    base = items.Item.make_itemid(filename, baseid)
    group = databases.dbs[filename].get_next_history_group()
    return items.Item.insert(mode='sibling', base=base, group=group, text=text,
                             description=description)


def append_item(filename, baseid, group=None, text='New item',
                description='Insert item'):
    base = items.Item.make_itemid(filename, baseid)
    if group == None:
        group = databases.dbs[filename].get_next_history_group()
    return items.Item.insert(mode='child', base=base, group=group, text=text,
                            description=description)


def insert_item_after(filename, baseid, group=None, text='New item',
                      description='Insert item'):
    base = items.Item.make_itemid(filename, baseid)
    if group == None:
        group = databases.dbs[filename].get_next_history_group()
    return items.Item.insert(mode='sibling', base=base, group=group, text=text,
                            description=description)


def move_item_up(filename, id_, description='Move item up'):
    group = databases.dbs[filename].get_next_history_group()
    return items.items[items.Item.make_itemid(filename, id_)
                      ].shift(mode='up', group=group, description=description)


def move_item_down(filename, id_, description='Move item down'):
    group = databases.dbs[filename].get_next_history_group()
    return items.items[items.Item.make_itemid(filename, id_)
                      ].shift(mode='down', group=group,
                              description=description)


def move_item_to_parent(filename, id_, description='Move item to parent'):
    group = databases.dbs[filename].get_next_history_group()
    return items.items[items.Item.make_itemid(filename, id_)
                      ].shift(mode='parent', group=group,
                              description=description)


def update_item_text(filename, id_, text, group=None,
                     description='Update item text'):
    if group == None:
        group = databases.dbs[filename].get_next_history_group()
    return items.items[items.Item.make_itemid(filename, id_)
                      ].update(group, description=description, text=text)


def insert_history(filename, group, id_, type, description, query_redo,
                   text_redo, query_undo, text_undo):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.history_insert, (group, id_, type, description,
                                         query_redo, text_redo,
                                         query_undo, text_undo))
    databases.dbs[filename].connection.give(qconn)
    return cur.lastrowid


def preview_undo_tree(filename):
    read = databases.dbs[filename].read_history('undo')
    if read:
        items = []
        for row in read['history']:
            items.append(row['H_item'])
        return items
    else:
        return False


def preview_redo_tree(filename):
    read = databases.dbs[filename].read_history('redo')
    if read:
        items = []
        for row in read['history']:
            items.append(row['H_item'])
        return items
    else:
        return False


def undo_tree(filename):
    return databases.dbs[filename].do_history('undo')


def redo_tree(filename):
    return databases.dbs[filename].do_history('redo')


def delete_items(filename, ditems, group=None, description='Delete items'):
    if group == None:
        group = databases.dbs[filename].get_next_history_group()
    return databases.dbs[filename].delete_items(ditems, group=group,
                                               description=description)


def get_next_history_group(filename):
    return databases.dbs[filename].get_next_history_group()


def check_pending_changes(filename):
    return databases.dbs[filename].check_pending_changes()


def set_modified(filename):
    return databases.dbs[filename].set_modified()


def get_tree_item(filename, parent, previous):
    item = items.items[items.Item.make_itemid(filename, parent
                                              )].get_tree_item(previous)
    return item


def get_items(filename):
    itemsl = []
    for i in items.items:
        if items.items[i].get_filename() == filename:
            itemsl.append(int(items.items[i].get_id()))
    return itemsl


def get_items_count():
    return len(items.items)


def get_item_info(filename, id_):
    return items.items[items.Item.make_itemid(filename, id_)].get_all()


def get_item_text(filename, id_):
    return items.items[items.Item.make_itemid(filename, id_)].get_text()


def get_history_descriptions(filename):
    return databases.dbs[filename].get_history_descriptions()


def select_properties_table(filename):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.properties_select)
    databases.dbs[filename].connection.give(qconn)
    return cur


def select_compatibility_table(filename):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.compatibility_select)
    databases.dbs[filename].connection.give(qconn)
    return cur


def select_items_table(filename):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.items_select)
    databases.dbs[filename].connection.give(qconn)
    return cur


def select_history_table(filename):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.history_select)
    databases.dbs[filename].connection.give(qconn)
    return cur


def block_databases():
    return databases.protection.block()


def release_databases():
    return databases.protection.release()


def get_open_databases():
    return tuple(databases.dbs.keys())


def is_database_open(filename):
    return filename in databases.dbs


def get_databases_count():
    return len(databases.dbs)


def bind_to_create_database(handler, bind=True):
    return databases.create_database_event.bind(handler, bind)


def bind_to_open_database(handler, bind=True):
    return databases.open_database_event.bind(handler, bind)


def bind_to_close_database(handler, bind=True):
    return databases.close_database_event.bind(handler, bind)


def bind_to_save_database_copy(handler, bind=True):
    return databases.save_database_copy_event.bind(handler, bind)


def bind_to_delete_items(handler, bind=True):
    return databases.delete_items_event.bind(handler, bind)


def bind_to_history(handler, bind=True):
    return history.history_event.bind(handler, bind)


def bind_to_history_insert(handler, bind=True):
    return history.history_insert_event.bind(handler, bind)


def bind_to_history_update(handler, bind=True):
    return history.history_update_event.bind(handler, bind)


def bind_to_history_remove(handler, bind=True):
    return history.history_remove_event.bind(handler, bind)


def bind_to_history_other(handler, bind=True):
    return history.history_other_event.bind(handler, bind)


def bind_to_check_pending_changes(handler, bind=True):
    return history.check_pending_changes_event.bind(handler, bind)


def bind_to_reset_modified_state(handler, bind=True):
    return history.reset_modified_state_event.bind(handler, bind)


def bind_to_history_clean(handler, bind=True):
    return history.history_clean_event.bind(handler, bind)


def bind_to_history_clean_groups(handler, bind=True):
    return history.history_clean_groups_event.bind(handler, bind)


def bind_to_exit_app_1(handler, bind=True):
    return databases.exit_app_event_1.bind(handler, bind)


def bind_to_exit_app_2(handler, bind=True):
    return databases.exit_app_event_2.bind(handler, bind)


def bind_to_insert_item(handler, bind=True):
    return items.item_insert_event.bind(handler, bind)


def bind_to_delete_item(handler, bind=True):
    return items.item_delete_event.bind(handler, bind)
