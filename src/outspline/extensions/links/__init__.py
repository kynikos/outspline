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

import links
import queries

_ADDON_NAME = ('Extensions', 'links')


def create_copy_table():
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copylinks_create)
    core_api.give_memory_connection(mem)


def handle_open_database_dirty(kwargs):
    info = coreaux_api.get_addons_info()
    dependencies = info(_ADDON_NAME[0])(_ADDON_NAME[1]
                                    )['database_dependency_group_1'].split(' ')

    if not set(dependencies) - set(kwargs['dependencies']):
        links.cdbs.add(kwargs['filename'])


def handle_open_database(kwargs):
    filename = kwargs['filename']

    if filename in links.cdbs:
        links.last_known_links[filename] = {}

        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()
        cursor.execute(queries.links_select)
        core_api.give_connection(filename, qconn)

        for row in cursor:
            links.last_known_links[filename][row['L_id']] = row['L_target']

        core_api.register_history_action_handlers(filename, 'link_insert',
                    links.handle_history_insert, links.handle_history_delete)
        core_api.register_history_action_handlers(filename, 'link_update',
                    links.handle_history_update, links.handle_history_update)
        core_api.register_history_action_handlers(filename, 'link_delete',
                    links.handle_history_delete, links.handle_history_insert)


def handle_save_database_copy(kwargs):
    if kwargs['origin'] in links.cdbs:
        qconn = core_api.get_connection(kwargs['origin'])
        qconnd = sqlite3.connect(kwargs['destination'])
        cur = qconn.cursor()
        curd = qconnd.cursor()

        cur.execute(queries.links_select)
        for row in cur:
            # Don't use links.do_insert_link here, as the destination database
            # is not really open
            curd.execute(queries.links_insert, tuple(row))

        core_api.give_connection(kwargs['origin'], qconn)

        qconnd.commit()
        qconnd.close()


def handle_close_database(kwargs):
    try:
        del links.last_known_links[kwargs['filename']]
    except KeyError:
        pass

    links.cdbs.discard(kwargs['filename'])


def handle_update_item(kwargs):
    # kwargs['text'] could be None if the query updated the position of the
    # item and not its text
    if kwargs['text'] is not None:
        links.synchronize_links_text(kwargs['filename'], kwargs['id_'],
                        kwargs['text'], kwargs['group'], kwargs['description'])


def handle_delete_item(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']
    group = kwargs['group']
    description = kwargs['description']

    if filename in links.cdbs:
        links.delete_link(filename, id_, group, description)
        links.break_links(filename, id_, group, description)

        if copypaste_api:
            # Breaking links in the CopyLinks table will not be stored in the
            # history, so this is useful only if undoing/redoing changes will
            # warn the user and break all the copied links
            links.break_copied_links(filename, id_)


def handle_history(kwargs):
    # Break all the links in the CopyLinks table because it cannot be kept up
    # to date with history changes
    if kwargs['filename'] in links.cdbs:
        links.break_all_copied_links(kwargs['filename'])


def handle_copy_items(kwargs):
    # Do not check if kwargs['filename'] is in links.cdbs, always clear the
    # table as the other functions rely on the table to be clear
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copylinks_delete)
    core_api.give_memory_connection(mem)


def handle_copy_item(kwargs):
    links.copy_link(kwargs['filename'], kwargs['id_'])


def handle_paste_item(kwargs):
    links.paste_link(kwargs['filename'], kwargs['id_'], kwargs['oldid'],
                                        kwargs['group'], kwargs['description'])


def handle_safe_paste_check(kwargs):
    links.can_paste_safely(kwargs['filename'], kwargs['exception'])


def main():
    create_copy_table()

    core_api.bind_to_open_database_dirty(handle_open_database_dirty)
    core_api.bind_to_open_database(handle_open_database)
    core_api.bind_to_save_database_copy(handle_save_database_copy)
    core_api.bind_to_close_database(handle_close_database)
    core_api.bind_to_deleted_item(handle_delete_item)
    core_api.bind_to_history(handle_history)

    if coreaux_api.get_extension_configuration('links').get_bool('sync_text'):
        core_api.bind_to_update_item(handle_update_item)

    if copypaste_api:
        copypaste_api.bind_to_copy_items(handle_copy_items)
        copypaste_api.bind_to_copy_item(handle_copy_item)
        copypaste_api.bind_to_paste_item(handle_paste_item)
        copypaste_api.bind_to_safe_paste_check(handle_safe_paste_check)
