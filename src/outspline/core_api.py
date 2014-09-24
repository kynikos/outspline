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

from core import databases, items, history, queries
from core.exceptions import (AccessDeniedError, DatabaseAlreadyOpenError,
                            DatabaseNotAccessibleError, DatabaseLockedError,
                            CannotMoveItemError, NoLongerExistingItem)


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


def open_database(filename, check_new_extensions=True):
    return databases.Database.open(filename,
                                    check_new_extensions=check_new_extensions)


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
    group = databases.dbs[filename].dbhistory.get_next_history_group()
    return items.Item.insert(filename=filename, mode='child', baseid=baseid,
                             group=group, text=text, description=description)


def create_sibling(filename, baseid, text='New item',
                   description='Create sibling'):
    group = databases.dbs[filename].dbhistory.get_next_history_group()
    return items.Item.insert(filename=filename, mode='sibling', baseid=baseid,
                             group=group, text=text, description=description)


def append_item(filename, baseid, group=None, text='New item',
                description='Insert item'):
    if group == None:
        group = databases.dbs[filename].dbhistory.get_next_history_group()
    return items.Item.insert(filename=filename, mode='child', baseid=baseid,
                             group=group, text=text, description=description)


def insert_item_after(filename, baseid, group=None, text='New item',
                      description='Insert item'):
    if group == None:
        group = databases.dbs[filename].dbhistory.get_next_history_group()
    return items.Item.insert(filename=filename, mode='sibling', baseid=baseid,
                             group=group, text=text, description=description)


def move_item_up(filename, id_, description='Move item up'):
    group = databases.dbs[filename].dbhistory.get_next_history_group()
    try:
        return databases.dbs[filename].items[id_].shift(mode='up', group=group,
                                                    description=description)
    except CannotMoveItemError:
        return False


def move_item_down(filename, id_, description='Move item down'):
    group = databases.dbs[filename].dbhistory.get_next_history_group()
    try:
        return databases.dbs[filename].items[id_].shift(mode='down',
                                        group=group, description=description)
    except CannotMoveItemError:
        return False


def move_item_to_parent(filename, id_, description='Move item to parent'):
    group = databases.dbs[filename].dbhistory.get_next_history_group()
    try:
        return databases.dbs[filename].items[id_].shift(mode='parent',
                                        group=group, description=description)
    except CannotMoveItemError:
        return False


def update_item_text(filename, id_, text, group=None,
                     description='Update item text'):
    if group == None:
        group = databases.dbs[filename].dbhistory.get_next_history_group()
    return databases.dbs[filename].items[id_].update(group,
                                            description=description, text=text)


def update_item_text_no_event(filename, id_, text, group=None,
                                            description='Update item text'):
    if group == None:
        group = databases.dbs[filename].dbhistory.get_next_history_group()
    return databases.dbs[filename].items[id_].update_no_event(group,
                                            description=description, text=text)


def register_history_action_handlers(filename, name, redo_handler,
                                                                undo_handler):
    return databases.dbs[filename].dbhistory.register_action_handlers(name,
                                                    redo_handler, undo_handler)


def insert_history(filename, group, id_, type, description, query_redo,
                                                                query_undo):
    return databases.dbs[filename].dbhistory.insert_history(group, id_, type,
                                        description, query_redo, query_undo)


def preview_undo_tree(filename):
    read = databases.dbs[filename].dbhistory.read_history_undo()
    if read:
        items = set()
        for row in read['history']:
            items.add(row['H_item'])
        return items
    else:
        return False


def preview_redo_tree(filename):
    read = databases.dbs[filename].dbhistory.read_history_redo()
    if read:
        items = set()
        for row in read['history']:
            items.add(row['H_item'])
        return items
    else:
        return False


def undo_tree(filename):
    return databases.dbs[filename].dbhistory.undo_history()


def redo_tree(filename):
    return databases.dbs[filename].dbhistory.redo_history()


def delete_items(filename, ditems, group=None, description='Delete items'):
    if group == None:
        group = databases.dbs[filename].dbhistory.get_next_history_group()
    return databases.dbs[filename].delete_items(ditems, group=group,
                                               description=description)


def get_next_history_group(filename):
    return databases.dbs[filename].dbhistory.get_next_history_group()


def check_pending_changes(filename):
    return databases.dbs[filename].dbhistory.check_pending_changes()


def set_modified(filename):
    return databases.dbs[filename].dbhistory.set_modified()


def is_item(filename, id_):
    return id_ in databases.dbs[filename].items


def is_item_root(filename, id_):
    return databases.dbs[filename].items[id_].is_root()


def update_database_history_soft_limit(filename, limit):
    return databases.dbs[filename].dbhistory.update_soft_limit(limit)


def add_database_ignored_dependency(filename, extension):
    return databases.dbs[filename].add_ignored_dependency(extension)


def remove_database_ignored_dependency(filename, extension):
    return databases.dbs[filename].remove_ignored_dependency(extension)


def get_tree_item(filename, parent, previous):
    return items.Item.get_tree_item(filename, parent, previous)


def get_items_ids(filename):
    return databases.dbs[filename].items.keys()


def get_items_count(filename):
    return len(databases.dbs[filename].items)


def get_item_info(filename, id_):
    return databases.dbs[filename].items[id_].get_all_info()


def get_item_parent(filename, id_):
    return databases.dbs[filename].items[id_].get_parent()


def get_item_children(filename, id_):
    return databases.dbs[filename].items[id_].get_children()


def get_item_previous(filename, id_):
    return databases.dbs[filename].items[id_].get_previous()


def get_item_next(filename, id_):
    return databases.dbs[filename].items[id_].get_next()


def get_item_ancestors(filename, id_):
    # It's necessary to initialize ancestors=[] because otherwise for some
    # reason the ancestors list from the previous call would be used, thus
    # appending the ancestors again, multiplicating them at every call
    return databases.dbs[filename].items[id_].get_ancestors(ancestors=[])


def get_item_descendants(filename, id_):
    return databases.dbs[filename].items[id_].get_descendants()


def get_root_items(filename):
    return databases.dbs[filename].get_root_items()


def get_item_text(filename, id_):
    try:
        return databases.dbs[filename].items[id_].get_text()
    except KeyError:
        # KeyError is raised if the items[id_] has already been deleted
        raise NoLongerExistingItem()
    except TypeError:
        # TypeError is raised if the query in get_text returns no values
        raise NoLongerExistingItem()


def get_all_items(filename):
    return databases.dbs[filename].get_all_items()


def get_all_items_text(filename):
    return databases.dbs[filename].get_all_items_text()


def get_history_descriptions(filename):
    return databases.dbs[filename].dbhistory.get_history_descriptions()


def select_all_memory_table_names():
    qconn = databases.memory.get()
    cur = qconn.cursor()
    cur.execute(queries.master_select_tables)
    databases.memory.give(qconn)
    return cur


def get_database_dependencies(filename, ignored=False):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.compatibility_select)

    deps = {row['CM_extension']: row['CM_version'] for row in cur
                                if row['CM_version'] is not None or ignored}

    databases.dbs[filename].connection.give(qconn)
    return deps


def get_database_history_soft_limit(filename):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.properties_select_history)
    databases.dbs[filename].connection.give(qconn)
    return cur.fetchone()[0]


def select_all_table_names(filename):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.master_select_tables)
    databases.dbs[filename].connection.give(qconn)
    return cur


def select_memory_table(table):
    qconn = databases.memory.get()
    cur = qconn.cursor()
    cur.execute(queries.master_select_table.format(table))
    databases.memory.give(qconn)
    return cur


def select_table(filename, table):
    qconn = databases.dbs[filename].connection.get()
    cur = qconn.cursor()
    cur.execute(queries.master_select_table.format(table))
    databases.dbs[filename].connection.give(qconn)
    return cur


def block_databases(block=False, quiet=False):
    return databases.protection.block(block=block, quiet=quiet)


def release_databases():
    return databases.protection.release()


def get_open_databases():
    return tuple(databases.dbs.keys())


def is_database_open(filename):
    return filename in databases.dbs


def get_databases_count():
    return len(databases.dbs)


def bind_to_blocked_databases(handler, bind=True):
    return databases.blocked_databases_event.bind(handler, bind)


def bind_to_open_database_dirty(handler, bind=True):
    return databases.open_database_dirty_event.bind(handler, bind)


def bind_to_open_database(handler, bind=True):
    return databases.open_database_event.bind(handler, bind)


def bind_to_closing_database(handler, bind=True):
    return databases.closing_database_event.bind(handler, bind)


def bind_to_close_database(handler, bind=True):
    return databases.close_database_event.bind(handler, bind)


def bind_to_save_permission_check(handler, bind=True):
    return databases.save_permission_check_event.bind(handler, bind)


def bind_to_save_database(handler, bind=True):
    return databases.save_database_event.bind(handler, bind)


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
    return history.history_delete_event.bind(handler, bind)


def bind_to_check_pending_changes(handler, bind=True):
    return history.check_pending_changes_event.bind(handler, bind)


def bind_to_reset_modified_state(handler, bind=True):
    return history.reset_modified_state_event.bind(handler, bind)


def bind_to_history_clean(handler, bind=True):
    return history.history_clean_event.bind(handler, bind)


def bind_to_exit_app_1(handler, bind=True):
    return databases.exit_app_event_1.bind(handler, bind)


def bind_to_exit_app_2(handler, bind=True):
    return databases.exit_app_event_2.bind(handler, bind)


def bind_to_insert_item(handler, bind=True):
    return items.item_insert_event.bind(handler, bind)


def bind_to_update_item(handler, bind=True):
    return items.item_update_event.bind(handler, bind)


def bind_to_delete_item(handler, bind=True):
    return items.item_delete_event.bind(handler, bind)
