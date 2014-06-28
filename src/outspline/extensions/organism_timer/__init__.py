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
import time as _time

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import queries
import timer

extension = None


class Main(object):
    def __init__(self):
        self._ADDON_NAME = ('Extensions', 'organism_timer')

        self.rules = timer.Rules()
        self.cdbs = set()
        self.databases = timer.Databases(self.cdbs)

        core_api.bind_to_create_database(self._handle_create_database)
        core_api.bind_to_open_database_dirty(self._handle_open_database_dirty)
        core_api.bind_to_open_database(self._handle_open_database)
        core_api.bind_to_close_database(self._handle_close_database)
        core_api.bind_to_save_database_copy(self._handle_save_database_copy)
        core_api.bind_to_delete_items(
                                self._handle_search_next_occurrences_request)
        core_api.bind_to_history(self._handle_search_next_occurrences_request)
        core_api.bind_to_exit_app_1(
                        self._handle_search_next_occurrences_cancel_request)

        organism_api.bind_to_update_item_rules_conditional(
                                self._handle_search_next_occurrences_request)

        if copypaste_api:
            copypaste_api.bind_to_items_pasted(
                                self._handle_search_next_occurrences_request)

    def _handle_create_database(self, kwargs):
        # Cannot use core_api.get_connection() here because the database isn't
        # open yet
        conn = sqlite3.connect(kwargs['filename'])
        cur = conn.cursor()
        cur.execute(queries.timerproperties_create)
        cur.execute(queries.timerproperties_insert, (int(_time.time()), ))
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
            timer.search_old_occurrences(filename)
            timer.search_next_occurrences()

    def _handle_save_database_copy(self, kwargs):
        origin = kwargs['origin']

        if origin in self.cdbs:
            qconn = core_api.get_connection(origin)
            qconnd = sqlite3.connect(kwargs['destination'])
            cur = qconn.cursor()
            curd = qconnd.cursor()

            cur.execute(queries.timerproperties_select)
            for row in cur:
                curd.execute(queries.timerproperties_update_copy, tuple(row))

            core_api.give_connection(origin, qconn)

            qconnd.commit()
            qconnd.close()

    def _handle_search_next_occurrences_request(self, kwargs):
         timer.search_next_occurrences()

    def _handle_search_next_occurrences_cancel_request(self, kwargs):
         timer.cancel_search_next_occurrences()

    def _handle_close_database(self, kwargs):
        self.cdbs.discard(kwargs['filename'])
        timer.search_next_occurrences()


def main():
    global extension
    extension = Main()
