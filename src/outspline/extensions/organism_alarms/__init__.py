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
import time as time_

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import queries
import alarmsmod

extension = None


class Main(object):
    def __init__(self):
        self._ADDON_NAME = ('Extensions', 'organism_alarms')

        self.cdbs = set()
        self.tempcdbs = set()
        self.databases = {}

        self._create_copy_table()

        core_api.bind_to_create_database(self._handle_create_database)
        core_api.bind_to_open_database_dirty(self._handle_open_database_dirty)
        core_api.bind_to_open_database(self._handle_open_database)
        core_api.bind_to_check_pending_changes(
                                            self._handle_check_pending_changes)
        core_api.bind_to_reset_modified_state(
                                            self._handle_reset_modified_state)
        core_api.bind_to_close_database(self._handle_close_database)
        core_api.bind_to_save_database_copy(self._handle_save_database_copy)
        core_api.bind_to_history_remove(self._handle_history_remove)
        core_api.bind_to_history_clean(self._handle_history_clean)

        # Do not bind directly to core_api.bind_to_delete_item because it would
        # create a race hazard with organism.items.delete_item_rules, which is
        # bound to the same event
        organism_api.bind_to_delete_item_rules(self._handle_delete_item_rules)
        organism_api.bind_to_get_alarms(self._handle_get_alarms)

        organism_timer_api.bind_to_get_next_occurrences(
                                    self._handle_get_next_occurrences)
        organism_timer_api.bind_to_activate_occurrences_range(
                                    self._handle_activate_occurrences_range)
        organism_timer_api.bind_to_activate_old_occurrences(
                                    self._handle_activate_old_occurrences)
        organism_timer_api.bind_to_activate_occurrences(
                                    self._handle_activate_occurrences)

        if copypaste_api:
            copypaste_api.bind_to_copy_items(self._handle_copy_items)
            copypaste_api.bind_to_copy_item(self._handle_copy_item)
            copypaste_api.bind_to_paste_item(self._handle_paste_item)
            copypaste_api.bind_to_safe_paste_check(
                                                self._handle_safe_paste_check)

    def _create_copy_table(self):
        mem = core_api.get_memory_connection()
        cur = mem.cursor()
        cur.execute(queries.copyalarms_create)
        core_api.give_memory_connection(mem)

    def _handle_create_database(self, kwargs):
        # Cannot use core_api.get_connection() here because the database isn't
        # open yet
        LIMIT = coreaux_api.get_extension_configuration('organism_alarms'
                                            ).get_int('default_log_soft_limit')

        conn = sqlite3.connect(kwargs['filename'])
        cur = conn.cursor()
        cur.execute(queries.alarmsproperties_create)
        cur.execute(queries.alarmsproperties_insert_init, (LIMIT, ))
        cur.execute(queries.alarms_create)
        cur.execute(queries.alarmsofflog_create)
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
            self.databases[filename] = alarmsmod.Database(filename)

            conf = coreaux_api.get_extension_configuration('organism_alarms')

            qconn = core_api.get_connection(filename)
            cursor = qconn.cursor()
            cursor.execute(queries.alarmsproperties_select_history)
            core_api.give_connection(filename, qconn)

            alarmsmod.log_limits[filename] = [cursor.fetchone()[0],
                                                conf.get_int('log_time_limit'),
                                                conf.get_int('log_hard_limit')]

    def _handle_close_database(self, kwargs):
        filename = kwargs['filename']

        try:
            del alarmsmod.modified_state[filename]
            del self.databases[filename]
        except KeyError:
            pass
        else:
            self.cdbs.discard(filename)
            self.tempcdbs.add(filename)
            alarmsmod.temp_log_limit[filename] = alarmsmod.log_limits[
                                                                filename][0]
            del alarmsmod.log_limits[filename]

    def _handle_check_pending_changes(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].check_pending_changes()

    def _handle_reset_modified_state(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].reset_modified_state()

    def _handle_save_database_copy(self, kwargs):
        origin = kwargs['origin']

        if origin in self.cdbs:
            qconn = core_api.get_connection(origin)
            qconnd = sqlite3.connect(kwargs['destination'])
            cur = qconn.cursor()
            curd = qconnd.cursor()

            curd.execute(queries.alarmsproperties_delete)
            cur.execute(queries.alarmsproperties_select)
            for row in cur:
                curd.execute(queries.alarmsproperties_insert_copy, tuple(row))

            cur.execute(queries.alarms_select)
            for row in cur:
                curd.execute(queries.alarms_insert_copy, tuple(row))

            cur.execute(queries.alarmsofflog_select)
            for row in cur:
                curd.execute(queries.alarmsofflog_insert_copy, tuple(row))

            core_api.give_connection(origin, qconn)

            qconnd.commit()
            qconnd.close()

    def _handle_copy_items(self, kwargs):
        # Do not check if kwargs['filename'] is in cdbs, always clear the table
        # as the other functions rely on the table to be clear
        mem = core_api.get_memory_connection()
        cur = mem.cursor()
        cur.execute(queries.copyalarms_delete)
        core_api.give_memory_connection(mem)

    def _handle_copy_item(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].copy_alarms(kwargs['id_'])

    def _handle_paste_item(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].paste_alarms(kwargs['id_'],
                                                            kwargs['oldid'])

    def _handle_safe_paste_check(self, kwargs):
        filename = kwargs['filename']

        self.databases[filename].can_paste_safely(kwargs['exception'],
                                                            filename in cdbs)

    def _handle_delete_item_rules(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].delete_alarms(kwargs['id_'],
                                                                kwargs['text'])

    def _handle_history_remove(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].delete_alarms(kwargs['id_'],
                                                                kwargs['text'])

    def _handle_history_clean(self, kwargs):
        filename = kwargs['filename']

        if filename in self.tempcdbs:
            self.databases[filename].clean_alarms_log()
            self.tempcdbs.discard(filename)

    def _handle_get_alarms(self, kwargs):
        filename = kwargs['filename']

        if filename in self.cdbs:
            self.databases[filename].get_alarms(kwargs['mint'], kwargs['maxt'],
                                                                kwargs['occs'])

    def _handle_get_next_occurrences(self, kwargs):
        filename = kwargs['filename']

        if self.filename in self.cdbs:
            self.databases[filename].get_snoozed_alarms(kwargs['base_time'],
                                                                kwargs['occs'])

    def _handle_activate_occurrences_range(self, kwargs):
        self.databases[kwargs['filename']].activate_alarms_range(
                            kwargs['mint'], kwargs['maxt'], kwargs['occsd'])

    def _handle_activate_old_occurrences(self, kwargs):
        occsd = kwargs['oldoccsd']

        for filename in occsd:
            self.databases[filename].activate_old_alarms(occsd[filename])

    def _handle_activate_occurrences(self, kwargs):
        occsd = kwargs['occsd']

        for filename in occsd:
            self.databases[filename].activate_alarms(kwargs['time'],
                                                            occsd[filename])

    def get_number_of_active_alarms(self):
        count = 0

        # cdbs may change size during the loop because of races with other
        # threads
        for filename in self.cdbs.copy():
            count += self.databases[filename].get_number_of_active_alarms()

        return count

    def snooze_alarms(self, alarmsd, stime):
        newalarm = ((int(time_.time()) + stime) // 60 + 1) * 60

        for filename in alarmsd:
            self.databases[filename].snooze_alarms(alarmsd[filename], stime,
                                                                    newalarm)

        # Do not search occurrences (thus restarting the timer) inside the for
        # loop, otherwise it messes up with the wx.CallAfter() that manages the
        # activated alarms in the interface
        organism_timer_api.search_next_occurrences()

    def dismiss_alarms(self, alarmsd):
        for filename in alarmsd:
            self.databases[filename].dismiss_alarms(alarmsd[filename])


def main():
    global extension
    extension = Main()
