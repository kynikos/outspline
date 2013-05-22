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

import sqlite3
import time as _time

import organism.coreaux_api as coreaux_api
import organism.core_api as core_api
import organism.extensions.organizer_api as organizer_api
copypaste_api = coreaux_api.import_extension_api('copypaste')

import queries
import timer


def handle_create_database(kwargs):
    # Cannot use core_api.get_connection() here because the database isn't
    # open yet
    conn = sqlite3.connect(kwargs['filename'])
    cur = conn.cursor()
    cur.execute(queries.timerproperties_create)
    cur.execute(queries.timerproperties_insert, (int(_time.time()), ))
    conn.commit()
    conn.close()


def handle_save_database_copy(kwargs):
    qconn = core_api.get_connection(kwargs['origin'])
    qconnd = sqlite3.connect(kwargs['destination'])
    cur = qconn.cursor()
    curd = qconnd.cursor()

    cur.execute(queries.timerproperties_select)
    for row in cur:
        curd.execute(queries.timerproperties_update_copy, tuple(row))

    core_api.give_connection(kwargs['origin'], qconn)

    qconnd.commit()
    qconnd.close()


def handle_search_occurrences(kwargs):
    timer.search_occurrences()


def main():
    core_api.bind_to_create_database(handle_create_database)
    core_api.bind_to_open_database(handle_search_occurrences)
    core_api.bind_to_close_database(handle_search_occurrences)
    core_api.bind_to_save_database_copy(handle_save_database_copy)
    core_api.bind_to_delete_items(handle_search_occurrences)
    core_api.bind_to_history(handle_search_occurrences)
    core_api.bind_to_exit_app_1(timer.cancel_timer)

    organizer_api.bind_to_update_item_rules(handle_search_occurrences)

    if copypaste_api:
        copypaste_api.bind_to_items_pasted(handle_search_occurrences)
