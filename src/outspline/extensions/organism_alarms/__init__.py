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

import sqlite3

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import queries
import alarmsmod


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


def handle_close_database(kwargs):
    del alarmsmod.changes[kwargs['filename']]
    del alarmsmod.dismiss_state[kwargs['filename']]


def handle_check_pending_changes(kwargs):
    filename = kwargs['filename']

    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    change_state = alarmsmod.changes[filename] != [row for row in cur.execute(
                                                         queries.alarms_select)]
    core_api.give_connection(filename, conn)

    if change_state or alarmsmod.dismiss_state[filename]:
        core_api.set_modified(filename)


def handle_reset_modified_state(kwargs):
    filename = kwargs['filename']

    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    alarmsmod.changes[filename] = [row for row in cur.execute(
                                                         queries.alarms_select)]
    core_api.give_connection(filename, conn)

    alarmsmod.dismiss_state[filename] = False


def handle_save_database_copy(kwargs):
    qconn = core_api.get_connection(kwargs['origin'])
    qconnd = sqlite3.connect(kwargs['destination'])
    cur = qconn.cursor()
    curd = qconnd.cursor()

    cur.execute(queries.alarms_select)
    for row in cur:
        curd.execute(queries.alarms_insert_copy, tuple(row))

    core_api.give_connection(kwargs['origin'], qconn)

    qconnd.commit()
    qconnd.close()


def handle_copy_items(kwargs):
    mem = core_api.get_memory_connection()
    cur = mem.cursor()
    cur.execute(queries.copyalarms_delete)
    core_api.give_memory_connection(mem)


def handle_copy_item(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']

    alarmsmod.copy_alarms(filename, id_)


def handle_paste_item(kwargs):
    alarmsmod.paste_alarms(kwargs['filename'], kwargs['id_'], kwargs['oldid'])


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
    mint = kwargs['mint']
    maxt = kwargs['maxt']
    filename = kwargs['filename']
    occs = kwargs['occs']

    alarmsmod.get_alarms(mint, maxt, filename, occs)


def handle_get_next_occurrences(kwargs):
    last_search = kwargs['base_time']
    filename = kwargs['filename']
    occs = kwargs['occs']

    alarmsmod.get_snoozed_alarms(last_search, filename, occs)


def handle_activate_occurrences_range(kwargs):
    filename = kwargs['filename']
    mint = kwargs['mint']
    maxt = kwargs['maxt']
    occsd = kwargs['occsd']

    alarmsmod.activate_alarms_range(filename, mint, maxt, occsd)


def handle_activate_old_occurrences(kwargs):
    occsd = kwargs['oldoccsd']

    alarmsmod.activate_old_alarms(occsd)


def handle_activate_occurrences(kwargs):
    time = kwargs['time']
    occsd = kwargs['occsd']

    alarmsmod.activate_alarms(time, occsd)


def main():
    create_copy_table()

    core_api.bind_to_create_database(handle_create_database)
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
