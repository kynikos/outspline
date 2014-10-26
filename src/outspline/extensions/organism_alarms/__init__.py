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
        self.choose_unique_old_alarms = None
        self.OLD_THRESHOLD = coreaux_api.get_extension_configuration(
                            'organism_alarms').get_int('old_alarms_threshold')

        self.databases = {}

        self._create_copy_table()

        core_api.bind_to_open_database_dirty(self._handle_open_database_dirty)
        core_api.bind_to_open_database(self._handle_open_database)
        core_api.bind_to_check_pending_changes(
                                            self._handle_check_pending_changes)
        core_api.bind_to_reset_modified_state(
                                            self._handle_reset_modified_state)
        # No need to bind to close_database, as specific filenames will be
        # deleted from self.databases in self._handle_history_clean
        core_api.bind_to_history_remove(self._handle_history_remove)
        core_api.bind_to_history_clean(self._handle_history_clean)

        # Do not bind directly to core_api.bind_to_deleted_item because it
        # would create a race hazard with organism.items.delete_item_rules,
        # which is bound to the same event
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

    def _handle_open_database_dirty(self, kwargs):
        info = coreaux_api.get_addons_info()
        dependencies = info(self._ADDON_NAME[0])(self._ADDON_NAME[1]
                                    )['database_dependency_group_1'].split(' ')

        if not set(dependencies) - set(kwargs['dependencies']):
            filename = kwargs['filename']
            self.databases[filename] = alarmsmod.Database(filename,
                                                self.choose_unique_old_alarms)

    def _handle_open_database(self, kwargs):
        try:
            self.databases[kwargs['filename']].post_init()
        except KeyError:
            pass

    def _handle_check_pending_changes(self, kwargs):
        try:
            self.databases[kwargs['filename']].check_pending_changes()
        except KeyError:
            pass

    def _handle_reset_modified_state(self, kwargs):
        try:
            self.databases[kwargs['filename']].reset_modified_state()
        except KeyError:
            pass

    def _handle_copy_items(self, kwargs):
        # Do not check if kwargs['filename'] is in self.databases, always clear
        # the table as the other functions rely on the table to be clear
        mem = core_api.get_memory_connection()
        cur = mem.cursor()
        cur.execute(queries.copyalarms_delete)
        core_api.give_memory_connection(mem)

    def _handle_copy_item(self, kwargs):
        try:
            self.databases[kwargs['filename']].copy_alarms(kwargs['id_'])
        except KeyError:
            pass

    def _handle_paste_item(self, kwargs):
        try:
            self.databases[kwargs['filename']].paste_alarms(kwargs['id_'],
                                                            kwargs['oldid'])
        except KeyError:
            pass

    def _handle_safe_paste_check(self, kwargs):
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyalarms_select)
        core_api.give_memory_connection(mem)

        # Warn if CopyAlarms table has alarms but filename doesn't support them
        if curm.fetchone() and kwargs['filename'] not in self.databases:
            raise kwargs['exception']()

    def _handle_delete_item_rules(self, kwargs):
        try:
            self.databases[kwargs['filename']].delete_alarms(kwargs['id_'],
                                                                kwargs['text'])
        except KeyError:
            pass

    def _handle_history_remove(self, kwargs):
        try:
            self.databases[kwargs['filename']].delete_alarms(kwargs['id_'],
                                                                kwargs['text'])
        except KeyError:
            pass

    def _handle_history_clean(self, kwargs):
        filename = kwargs['filename']

        try:
            self.databases[filename].clean_alarms_log(kwargs["dbcursor"])
        except KeyError:
            pass
        else:
            del self.databases[filename]

    def _handle_get_alarms(self, kwargs):
        try:
            self.databases[kwargs['filename']].get_alarms(kwargs['mint'],
                                                kwargs['maxt'], kwargs['occs'])
        except KeyError:
            pass

    def _handle_get_next_occurrences(self, kwargs):
        try:
            self.databases[kwargs['filename']].get_snoozed_alarms(
                                        kwargs['base_time'], kwargs['occs'])
        except KeyError:
            pass

    def _handle_activate_occurrences_range(self, kwargs):
        try:
            self.databases[kwargs['filename']].activate_alarms_range(
                                        kwargs['mint'], kwargs['maxt'],
                                        kwargs['occsd'], self.OLD_THRESHOLD)
        except KeyError:
            # Due to race conditions, filename could have been closed meanwhile
            # (e.g. if the modal dialog for closing the database was open in
            # the interface)
            pass

    def _handle_activate_old_occurrences(self, kwargs):
        occsd = kwargs['oldoccsd']

        for filename in occsd:
            try:
                self.databases[filename].activate_old_alarms(occsd[filename])
            except KeyError:
                # Due to race conditions, filename could have been closed
                # meanwhile (e.g. if the modal dialog for closing the database
                # was open in the interface)
                pass

    def _handle_activate_occurrences(self, kwargs):
        occsd = kwargs['occsd']

        for filename in occsd:
            try:
                self.databases[filename].activate_alarms(kwargs['time'],
                                                            occsd[filename])
            except KeyError:
                # Due to race conditions, filename could have been closed
                # meanwhile (e.g. if the modal dialog for closing the database
                # was open in the interface)
                pass

    def install_unique_old_alarms_interface(self, interface):
        self.choose_unique_old_alarms = interface

    def get_number_of_active_alarms(self):
        count = 0

        # self.databases may change size during the loop because of races with
        # other threads
        for filename in self.databases.keys():
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
