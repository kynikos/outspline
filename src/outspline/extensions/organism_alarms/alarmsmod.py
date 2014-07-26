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
import threading

from outspline.coreaux_api import Event
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_timer_api as organism_timer_api

import queries

alarm_event = Event()
alarm_off_event = Event()
activate_alarms_range_event = Event()
activate_alarms_range_end_event = Event()


class Database(object):
    def __init__(self, filename, choose_unique_old_alarms):
        self.filename = filename
        self.choose_unique_old_alarms = choose_unique_old_alarms
        self.changes = None
        self.modified_state = False
        self.old_alarms_lock = threading.Lock()
        # A first call to acquire is needed to set the state to unlocked
        self.old_alarms_lock.acquire()

    def post_init(self):
        conf = coreaux_api.get_extension_configuration('organism_alarms')

        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.alarmsproperties_select_history)
        core_api.give_connection(self.filename, qconn)

        self.log_limits = [cursor.fetchone()[0],
                                            conf.get_int('log_time_limit'),
                                            conf.get_int('log_hard_limit')]

    def get_snoozed_alarms(self, last_search, occs):
        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_select)
        core_api.give_connection(self.filename, conn)

        for row in cur:
            itemid = row['A_item']
            start = row['A_start']
            end = row['A_end']
            # Do not assign None here so that it's possible to distinguish
            # between occurrences without alarm and occurrences with active
            # alarm when they're mixed together
            # Storing False ensures consistent behaviour with None when doing
            # generic boolean tests
            snooze = False if row['A_snooze'] is None else row['A_snooze']

            # Check whether the snoozed alarm has a duplicate among the
            # alarms found using the alarm rules, and in that case delete
            # the latter; the creation of duplicates is possible especially
            # when alarm searches are performed in rapid succession, for
            # example when launching outspline with multiple databases
            # automatically opened and many new alarms to be immediately
            # activated
            occs.try_delete_one(self.filename, itemid, start, end,
                                                                row['A_alarm'])

            alarmd = {'filename': self.filename,
                      'id_': itemid,
                      'alarmid': row['A_id'],
                      'start': start,
                      'end': end,
                      'alarm': snooze}

            # For safety, also check that there aren't any alarms with
            # snooze <= last_search left (for example this may happen if an
            # alarm is temporarily undone together with its item, and then it's
            # restored with a redo)
            # Note that whatever the value of last_search is, it doesn't really
            # have the possibility to prevent the activation of a snoozed
            # alarm, be it immediately or later (last_search can't be set on a
            # future time)
            if snooze and snooze > last_search:
                occs.add_safe(last_search, alarmd)
            else:
                occs.add_old(alarmd)

    def activate_alarms_range(self, mint, maxt, occsd, threshold):
        # Note that as long as this function remains on the same thread as
        # organism_timer's OldOccurrencesSearch search thread, it's under the
        # protection of its _handle_save_permission_check method
        activate_alarms_range_event.signal(filename=self.filename)

        count = 0

        for id_ in occsd.keys():
            for occ in occsd[id_][:]:
                # occ may have alarm == mint, or start or end in the
                #  interval, but none of those occurrences must be activated
                # In particular, the alarm == mint case should have already
                #  been activated the previous time Outspline was run
                if mint < occ['alarm'] <= maxt:
                    count += 1
                else:
                    # Do not use 'del' with an index taken by enumerating on
                    # occsd[id_][:], because after deleting one item all the
                    # indices wouldn't correspond anymore
                    occsd[id_].remove(occ)

        if count > threshold and \
                        self.choose_unique_old_alarms is not None:
            self.choose_unique_old_alarms(self.filename, count)
            self.old_alarms_lock.acquire()

            if self.old_alarms_unique is True:
                self._activate_alarms_unique(occsd)
            elif self.old_alarms_unique is False:
                self._activate_alarms_all(occsd)
            # self.old_alarms_unique could be None, and in that case it means
            # that the alarms must not be activated
        else:
            self._activate_alarms_all(occsd)

        activate_alarms_range_end_event.signal(filename=self.filename)

    def activate_alarms_range_continue(self, unique):
        # This method is run on the main thread
        self.old_alarms_unique = unique
        self.old_alarms_lock.release()

    def activate_old_alarms(self, occsd):
        self._activate_alarms_all(occsd)

    def _activate_alarms_all(self, occsd):
        for id_ in occsd:
            # Due to race conditions, id_ could have been deleted meanwhile
            # (e.g. if the modal dialog for deleting the item was open in the
            # interface)
            if core_api.is_item(self.filename, id_):
                for occ in occsd[id_]:
                    self._activate_alarm(occ)

    def _activate_alarms_unique(self, occsd):
        for id_ in occsd:
            # Due to race conditions, id_ could have been deleted meanwhile
            # (e.g. if the modal dialog for deleting the item was open in the
            # interface)
            if core_api.is_item(self.filename, id_):
                try:
                    occ = max(occsd[id_], key=lambda occ: occ['alarm'])
                except ValueError:
                    # occsd[id_] may be have been emptied in
                    # self.activate_alarms_range
                    pass
                else:
                    self._activate_alarm(occ)

    def activate_alarms(self, time, occsd):
        for id_ in occsd:
            # Due to race conditions, id_ could have been deleted meanwhile
            # (e.g. if the modal dialog for deleting the item was open in the
            # interface)
            if core_api.is_item(self.filename, id_):
                for occ in occsd[id_]:
                    # occ may have start or end == time
                    if occ['alarm'] == time:
                        self._activate_alarm(occ)

    def _activate_alarm(self, alarm):
        # If one of the loops that call this method lasts long enough (and
        # the're not run on the main thread), the database may be closed
        # meanwhile; however this function seems to terminate safely without
        # the need of further tests here
        if 'alarmid' not in alarm:
            alarmid = self._insert_alarm(id_=alarm['id_'],
                                   start=alarm['start'],
                                   end=alarm['end'],
                                   origalarm=alarm['alarm'],
                                   # Note that here passing None is correct (do
                                   # not pass False)
                                   snooze=None)
        else:
            alarmid = alarm['alarmid']
            # Occurrence dictionaries store active alarms with False, not None
            if alarm['alarm']:
                filename = alarm['filename']
                qconn = core_api.get_connection(filename)
                cursor = qconn.cursor()
                # Note that here using None is correct (do not use False)
                cursor.execute(queries.alarms_update_id, (None, alarmid))
                core_api.give_connection(filename, qconn)

        alarm_event.signal(filename=alarm['filename'],
                           id_=alarm['id_'],
                           alarmid=alarmid,
                           start=alarm['start'],
                           end=alarm['end'],
                           alarm=alarm['alarm'])

    def get_alarms(self, mint, maxt, occs):
        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_select)
        core_api.give_connection(self.filename, conn)

        for row in cur:
            origalarm = row['A_alarm']
            # Do not assign None here so that it's possible to distinguish
            # between occurrences without alarm and occurrences with active
            # alarm when they're mixed together
            # Storing False ensures consistent behaviour with None when doing
            # generic boolean tests
            snooze = False if row['A_snooze'] is None else row['A_snooze']

            alarmd = {'filename': self.filename,
                      'id_': row['A_item'],
                      'alarmid': row['A_id'],
                      'start': row['A_start'],
                      'end': row['A_end'],
                      'alarm': snooze}

            # If the alarm is not added to occs, add it to the active
            # dictionary if it's active (but not snoozed)
            # Note that if the alarm is active but its time values are included
            # between mint and maxt, the alarm is added to the main dictionary,
            # not the active one
            # Also note that the second argument must be origalarm, not snooze,
            # in fact it's used to *update* the occurrence (if present) using
            # the new snooze time stored in alarmd
            if not occs.update(alarmd, origalarm) and snooze is False:
                occs.move_active(alarmd, origalarm)

    def get_number_of_active_alarms(self):
        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_select_count)
        core_api.give_connection(self.filename, conn)
        row = cur.fetchone()
        return row['A_active_alarms']

    def snooze_alarms(self, alarmsd, stime, newalarm):
        for id_ in alarmsd:
            for alarmid in alarmsd[id_]:
                text = core_api.get_item_text(self.filename, id_)

                qconn = core_api.get_connection(self.filename)
                cursor = qconn.cursor()
                cursor.execute(queries.alarms_update_id, (newalarm, alarmid))
                core_api.give_connection(self.filename, qconn)

                self._insert_alarm_log(id_, 0, text.partition('\n')[0])

                # Signal the event after updating the database, so, for
                # example, the tasklist can be correctly updated
                alarm_off_event.signal(filename=self.filename, id_=id_,
                                                            alarmid=alarmid)

    def dismiss_alarms(self, alarmsd):
        for id_ in alarmsd:
            for alarmid in alarmsd[id_]:
                text = core_api.get_item_text(self.filename, id_)

                qconn = core_api.get_connection(self.filename)
                cursor = qconn.cursor()
                cursor.execute(queries.alarms_delete_id, (alarmid, ))
                core_api.give_connection(self.filename, qconn)

                self._insert_alarm_log(id_, 1, text.partition('\n')[0])

                # It's necessary to change the dismiss status, otherwise it's
                # possible that a database is loaded and some of its alarms are
                # activated: if at that point those alarms are dismissed and
                # then the user tries to close the database, the database will
                # seem unmodified, and won't ask to be saved
                self.modified_state = True

                # Signal the event after updating the database, so, for
                # example, the tasklist can be correctly updated
                alarm_off_event.signal(filename=self.filename, id_=id_,
                                                            alarmid=alarmid)

    def _insert_alarm(self, id_, start, end, origalarm, snooze):
        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_insert, (id_, start, end, origalarm,
                                                                    snooze))
        core_api.give_connection(self.filename, conn)
        aid = cur.lastrowid
        return aid

    def copy_alarms(self, id_):
        occs = []

        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_select_item, (id_, ))

        for row in cur:
            occs.append(row)

        core_api.give_connection(self.filename, conn)

        mem = core_api.get_memory_connection()
        curm = mem.cursor()

        for o in occs:
            curm.execute(queries.copyalarms_insert, (o['A_id'], id_,
                        o['A_start'], o['A_end'], o['A_alarm'], o['A_snooze']))

        core_api.give_memory_connection(mem)

    def paste_alarms(self, id_, oldid):
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyalarms_select_id, (oldid, ))
        core_api.give_memory_connection(mem)

        for occ in curm:
            self._insert_alarm(id_, occ['CA_start'], occ['CA_end'],
                                            occ['CA_alarm'], occ['CA_snooze'])

    def delete_alarms(self, id_, text):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.alarms_delete_item, (id_, ))

        if cursor.rowcount > 0:
            core_api.give_connection(self.filename, qconn)

            self._insert_alarm_log(id_, 2, text.partition('\n')[0])

            # Signal the event after updating the database, so, for example,
            # the tasklist can be correctly updated
            alarm_off_event.signal(filename=self.filename, id_=id_)
        else:
            core_api.give_connection(self.filename, qconn)

    def save_copy(self, destination):
        qconn = core_api.get_connection(self.filename)
        qconnd = sqlite3.connect(destination)
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

        core_api.give_connection(self.filename, qconn)

        qconnd.commit()
        qconnd.close()

    def _insert_alarm_log(self, id_, reason, text):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        # Also store the text, otherwise it won't be possible to retrieve it if
        # the item has been deleted meanwhile
        cursor.execute(queries.alarmsofflog_insert, (id_, reason, text))
        cursor.execute(queries.alarmsofflog_delete_clean, self.log_limits)
        core_api.give_connection(self.filename, qconn)

    def update_alarm_log_soft_limit(self, limit):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.alarmsproperties_update, (limit, ))
        core_api.give_connection(self.filename, qconn)

        self.modified_state = True

        self.log_limits[0] = limit

    def select_alarms_log(self):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.alarmsofflog_select_order)
        core_api.give_connection(self.filename, qconn)

        return cursor

    def clean_alarms_log(self):
        # The normal database connection has already been closed here
        qconn = sqlite3.connect(self.filename)
        cursor = qconn.cursor()

        cursor.execute(queries.alarmsofflog_delete_clean_close,
                                                        (self.log_limits[0], ))
        qconn.commit()
        qconn.close()

    def check_pending_changes(self):
        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        change_state = self.changes != [row for row in
                                            cur.execute(queries.alarms_select)]
        core_api.give_connection(self.filename, conn)

        if change_state or self.modified_state:
            core_api.set_modified(self.filename)

    def reset_modified_state(self):
        conn = core_api.get_connection(self.filename)
        cur = conn.cursor()
        self.changes = [row for row in cur.execute(queries.alarms_select)]
        core_api.give_connection(self.filename, conn)

        self.modified_state = False
