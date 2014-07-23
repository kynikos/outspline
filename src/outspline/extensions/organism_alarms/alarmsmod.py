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

from outspline.coreaux_api import Event
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_timer_api as organism_timer_api

import queries

alarm_event = Event()
alarm_off_event = Event()

changes = {}
modified_state = {}
cdbs = set()
tempcdbs = set()
log_limits = {}
temp_log_limit = {}


class Database(object):
    def __init__(self, filename):
        self.filename = filename

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

    def activate_alarms_range(self, mint, maxt, occsd):
        # Due to race conditions, filename could have been closed meanwhile
        # (e.g. if the modal dialog for closing the database was open in the
        # interface)
        if core_api.is_database_open(self.filename):
            for id_ in occsd:
                # Due to race conditions, id_ could have been deleted meanwhile
                # (e.g. if the modal dialog for deleting the item was open in
                # the interface)
                if core_api.is_item(self.filename, id_):
                    for occ in occsd[id_]:
                        # occ may have alarm == mint, or start or end in the
                        # interval, but none of those occurrences must be
                        # activated
                        if mint < occ['alarm'] <= maxt:
                            self._activate_alarm(occ)

    def activate_old_alarms(self, occsd):
        # Due to race conditions, filename could have been closed meanwhile
        # (e.g. if the modal dialog for closing the database was open in the
        # interface)
        if core_api.is_database_open(self.filename):
            for id_ in occsd:
                # Due to race conditions, id_ could have been deleted meanwhile
                # (e.g. if the modal dialog for deleting the item was open in
                # the interface)
                if core_api.is_item(self.filename, id_):
                    for occ in occsd[id_]:
                        self._activate_alarm(occ)

    def activate_alarms(self, time, occsd):
        # Due to race conditions, filename could have been closed meanwhile
        # (e.g. if the modal dialog for closing the database was open in the
        # interface)
        if core_api.is_database_open(self.filename):
            for id_ in occsd:
                # Due to race conditions, id_ could have been deleted meanwhile
                # (e.g. if the modal dialog for deleting the item was open in
                # the interface)
                if core_api.is_item(self.filename, id_):
                    for occ in occsd[id_]:
                        # occ may have start or end == time
                        if occ['alarm'] == time:
                            self._activate_alarm(occ)

    def _activate_alarm(self, alarm):
        if 'alarmid' not in alarm:
            alarmid = insert_alarm(filename=alarm['filename'],
                                   id_=alarm['id_'],
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

                insert_alarm_log(self.filename, id_, 0,
                                                    text.partition('\n')[0])

                # Signal the event after updating the database, so, for
                # example, the tasklist can be correctly updated
                alarm_off_event.signal(filename=self.filename, id_=id_,
                                                            alarmid=alarmid)


def dismiss_alarms(alarmsd):
    for filename in alarmsd:
        for id_ in alarmsd[filename]:
            for alarmid in alarmsd[filename][id_]:
                text = core_api.get_item_text(filename, id_)

                qconn = core_api.get_connection(filename)
                cursor = qconn.cursor()
                cursor.execute(queries.alarms_delete_id, (alarmid, ))
                core_api.give_connection(filename, qconn)

                insert_alarm_log(filename, id_, 1, text.partition('\n')[0])

                # It's necessary to change the dismiss status, otherwise it's
                # possible that a database is loaded and some of its alarms are
                # activated: if at that point those alarms are dismissed and
                # then the user tries to close the database, the database will
                # seem unmodified, and won't ask to be saved
                global modified_state
                modified_state[filename] = True

                # Signal the event after updating the database, so, for
                # example, the tasklist can be correctly updated
                alarm_off_event.signal(filename=filename, id_=id_,
                                                            alarmid=alarmid)


def insert_alarm(filename, id_, start, end, origalarm, snooze):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.alarms_insert, (id_, start, end, origalarm, snooze))
    core_api.give_connection(filename, conn)
    aid = cur.lastrowid
    return aid


def copy_alarms(filename, id_):
    if filename in cdbs:
        occs = []

        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_select_item, (id_, ))
        for row in cur:
            occs.append(row)
        core_api.give_connection(filename, conn)

        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        for o in occs:
            curm.execute(queries.copyalarms_insert, (o['A_id'], id_,
                        o['A_start'], o['A_end'], o['A_alarm'], o['A_snooze']))
        core_api.give_memory_connection(mem)


def can_paste_safely(filename, exception):
    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copyalarms_select)
    core_api.give_memory_connection(mem)

    # Warn if CopyAlarms table has alarms but filename doesn't support them
    if curm.fetchone() and filename not in cdbs:
        raise exception()


def paste_alarms(filename, id_, oldid):
    if filename in cdbs:
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyalarms_select_id, (oldid, ))
        core_api.give_memory_connection(mem)

        for occ in curm:
            insert_alarm(filename, id_, occ['CA_start'], occ['CA_end'],
                         occ['CA_alarm'], occ['CA_snooze'])


def delete_alarms(filename, id_, text):
    if filename in cdbs:
        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()
        cursor.execute(queries.alarms_delete_item, (id_, ))

        if cursor.rowcount > 0:
            core_api.give_connection(filename, qconn)

            insert_alarm_log(filename, id_, 2, text.partition('\n')[0])

            # Signal the event after updating the database, so, for example,
            # the tasklist can be correctly updated
            alarm_off_event.signal(filename=filename, id_=id_)
        else:
            core_api.give_connection(filename, qconn)


def insert_alarm_log(filename, id_, reason, text):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    # Also store the text, otherwise it won't be possible to retrieve it if the
    # item has been deleted meanwhile
    cursor.execute(queries.alarmsofflog_insert, (id_, reason, text))
    cursor.execute(queries.alarmsofflog_delete_clean, log_limits[filename])
    core_api.give_connection(filename, qconn)


def update_alarm_log_soft_limit(filename, limit):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.alarmsproperties_update, (limit, ))
    core_api.give_connection(filename, qconn)

    global modified_state
    modified_state[filename] = True

    global log_limits
    log_limits[filename][0] = limit


def select_alarms_log(filename):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.alarmsofflog_select_order)
    core_api.give_connection(filename, qconn)

    return cursor


def clean_alarms_log(filename):
    # filename has already been deleted from cdbs, use tempcdbs instead
    if filename in tempcdbs:
        qconn = sqlite3.connect(filename)
        cursor = qconn.cursor()

        # filename has already been deleted from log_limits, use
        # temp_log_limit instead
        global temp_log_limit
        cursor.execute(queries.alarmsofflog_delete_clean_close,
                                                (temp_log_limit[filename], ))
        qconn.commit()
        qconn.close()
        tempcdbs.discard(filename)
        del temp_log_limit[filename]
