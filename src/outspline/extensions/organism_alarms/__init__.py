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
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import queries
import alarmsmod

_ADDON_NAME = ('Extensions', 'organism_alarms')


def create_copy_table():
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copyalarms_create)
    core_api.give_memory_connection(mem)


def handle_create_database(kwargs):
    # Cannot use core_api.get_connection() here because the database isn't open
    # yet
    conn = sqlite3.connect(kwargs['filename'])
    cur = conn.cursor()
    cur.execute(queries.alarms_create)
    conn.commit()
    conn.close()


def handle_open_database_dirty(kwargs):
    info = coreaux_api.get_addons_info()
    dependencies = info(_ADDON_NAME[0])(_ADDON_NAME[1]
                                     )['database_dependency_group_1'].split(' ')

    if not set(dependencies) - set(kwargs['dependencies']):
        alarmsmod.cdbs.add(kwargs['filename'])


def handle_close_database(kwargs):
    try:
        del alarmsmod.changes[kwargs['filename']]
        del alarmsmod.dismiss_state[kwargs['filename']]
    except KeyError:
        pass
    else:
        alarmsmod.cdbs.discard(kwargs['filename'])


def handle_check_pending_changes(kwargs):
    filename = kwargs['filename']

    if filename in alarmsmod.cdbs:
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        change_state = alarmsmod.changes[filename] != [row for row in
                                             cur.execute(queries.alarms_select)]
        core_api.give_connection(filename, conn)

        if change_state or alarmsmod.dismiss_state[filename]:
            core_api.set_modified(filename)


def handle_reset_modified_state(kwargs):
    filename = kwargs['filename']

    if filename in alarmsmod.cdbs:
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        alarmsmod.changes[filename] = [row for row in cur.execute(
                                                         queries.alarms_select)]
        core_api.give_connection(filename, conn)

        alarmsmod.dismiss_state[filename] = False


def handle_save_database_copy(kwargs):
    origin = kwargs['origin']

    if origin in alarmsmod.cdbs:
        qconn = core_api.get_connection(origin)
        qconnd = sqlite3.connect(kwargs['destination'])
        cur = qconn.cursor()
        curd = qconnd.cursor()

        cur.execute(queries.alarms_select)
        for row in cur:
            curd.execute(queries.alarms_insert_copy, tuple(row))

        core_api.give_connection(origin, qconn)

        qconnd.commit()
        qconnd.close()


def handle_copy_items(kwargs):
    # Do not check if kwargs['filename'] is in cdbs, always clear the table as
    # the other functions rely on the table to be clear
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copyalarms_delete)
    core_api.give_memory_connection(mem)


def handle_copy_item(kwargs):
    alarmsmod.copy_alarms(kwargs['filename'], kwargs['id_'])


def handle_paste_item(kwargs):
    alarmsmod.paste_alarms(kwargs['filename'], kwargs['id_'], kwargs['oldid'])


def handle_safe_paste_check(kwargs):
    alarmsmod.can_paste_safely(kwargs['filename'], kwargs['exception'])


def handle_delete_item(kwargs):
    alarmsmod.delete_alarms(kwargs['filename'], kwargs['id_'], kwargs['hid'])


def handle_history_insert(kwargs):
    alarmsmod.undelete_alarms(kwargs['filename'], kwargs['id_'], kwargs['hid'])


def handle_history_remove(kwargs):
    alarmsmod.delete_alarms(kwargs['filename'], kwargs['id_'], kwargs['hid'])


def handle_history_clean_groups(kwargs):
    alarmsmod.clean_deleted_alarms(kwargs['filename'])


def handle_history_clean(kwargs):
    alarmsmod.clean_old_history_alarms(kwargs['filename'], kwargs['hids'])


def handle_get_alarms(kwargs):
    alarmsmod.get_alarms(kwargs['mint'], kwargs['maxt'], kwargs['filename'],
                                                                 kwargs['occs'])


def handle_get_next_occurrences(kwargs):
    alarmsmod.get_snoozed_alarms(kwargs['base_time'], kwargs['filename'],
                                                                 kwargs['occs'])


def handle_activate_occurrences_range(kwargs):
    alarmsmod.activate_alarms_range(kwargs['filename'], kwargs['mint'],
                                                kwargs['maxt'], kwargs['occsd'])


def handle_activate_old_occurrences(kwargs):
    alarmsmod.activate_old_alarms(kwargs['oldoccsd'])


def handle_activate_occurrences(kwargs):
    alarmsmod.activate_alarms(kwargs['time'], kwargs['occsd'])


def main():
    create_copy_table()

    core_api.bind_to_create_database(handle_create_database)
    core_api.bind_to_open_database_dirty(handle_open_database_dirty)
    core_api.bind_to_check_pending_changes(handle_check_pending_changes)
    core_api.bind_to_reset_modified_state(handle_reset_modified_state)
    core_api.bind_to_close_database(handle_close_database)
    core_api.bind_to_save_database_copy(handle_save_database_copy)
    core_api.bind_to_delete_item(handle_delete_item)
    core_api.bind_to_history_insert(handle_history_insert)
    core_api.bind_to_history_remove(handle_history_remove)
    core_api.bind_to_history_clean_groups(handle_history_clean_groups)
    core_api.bind_to_history_clean(handle_history_clean)

    organism_api.bind_to_get_alarms(handle_get_alarms)

    organism_timer_api.bind_to_get_next_occurrences(handle_get_next_occurrences)
    organism_timer_api.bind_to_activate_occurrences_range(
                                              handle_activate_occurrences_range)
    organism_timer_api.bind_to_activate_old_occurrences(
                                                handle_activate_old_occurrences)
    organism_timer_api.bind_to_activate_occurrences(handle_activate_occurrences)

    if copypaste_api:
        copypaste_api.bind_to_copy_items(handle_copy_items)
        copypaste_api.bind_to_copy_item(handle_copy_item)
        copypaste_api.bind_to_paste_item(handle_paste_item)
        copypaste_api.bind_to_safe_paste_check(handle_safe_paste_check)
