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

import time as _time
import sqlite3

from organism.coreaux_api import Event
import organism.core_api as core_api
import organism.extensions.organizer_timer_api as organizer_timer_api

import queries

alarm_event = Event()
alarms_event = Event()
alarm_off_event = Event()

changes = {}
dismiss_state = {}


def get_snoozed_alarms(last_search, filename, occs):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.alarms_select_alarms)
    core_api.give_connection(filename, conn)

    for row in cur:
        itemid = row['A_item']
        start = row['A_start']
        end = row['A_end']
        snooze = row['A_snooze']

        # Check whether the snoozed alarm has a duplicate among the alarms found
        # using the alarm rules, and in that case delete the latter; the
        # creation of duplicates is possible especially when alarm searches are
        # performed in rapid succession, for example when launching organism
        # with multiple databases automatically opened and many new alarms to be
        # immediately activated
        occs.try_delete_one(filename, itemid, start, end, row['A_alarm'])

        alarmd = {'filename': filename,
                  'id_': itemid,
                  'alarmid': row['A_id'],
                  'start': start,
                  'end': end,
                  'alarm': snooze}

        # For safety, also check that there aren't any alarms with snooze <=
        # last_search left (for example this may happen if an alarm is
        # temporarily undone together with its item, and then it's restored with
        # a redo)
        # Note that whatever the value of last_search is, it doesn't really have
        # the possibility to prevent the activation of a snoozed alarm, be it
        # immediately or later (last_search can't be set on a future time)
        if snooze and snooze > last_search:
            occs.add(last_search, alarmd)
        else:
            occs.add_old(alarmd)


def activate_old_alarms(occsd):
    for filename in occsd:
        for id_ in occsd[filename]:
            for occ in occsd[filename][id_]:
                activate_alarm(occ)


def activate_alarms(time, occsd):
    for filename in occsd:
        for id_ in occsd[filename]:
            for occ in occsd[filename][id_]:
                # occ may have start or end == time
                if occ['alarm'] == time:
                    activate_alarm(occ)

    alarms_event.signal()


def activate_alarm(alarm):
    if 'alarmid' not in alarm:
        alarmid = insert_alarm(filename=alarm['filename'],
                               id_=alarm['id_'],
                               start=alarm['start'],
                               end=alarm['end'],
                               origalarm=alarm['alarm'],
                               snooze=None)
    else:
        alarmid = alarm['alarmid']
        if alarm['alarm'] != None:
            update_alarm(filename=alarm['filename'],
                         alarmid=alarmid,
                         newalarm=None)

    alarm_event.signal(filename=alarm['filename'],
                       id_=alarm['id_'],
                       alarmid=alarmid,
                       start=alarm['start'],
                       end=alarm['end'],
                       alarm=alarm['alarm'])


def get_alarms(mint, maxt, filename, occs):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.alarms_select_alarms)
    core_api.give_connection(filename, conn)

    for row in cur:
        origalarm = row['A_alarm']
        snooze = row['A_snooze']

        alarmd = {'filename': filename,
                  'id_': row['A_item'],
                  'alarmid': row['A_id'],
                  'start': row['A_start'],
                  'end': row['A_end'],
                  'alarm': snooze}

        # Always add active (but not snoozed) alarms if time interval includes
        # current time
        if snooze == None and mint <= int(_time.time()) <= maxt:
            occs.update(alarmd, origalarm, force=True)
        else:
            # Note that the second argument must be origalarm, not snooze, in
            # fact it's used to *update* the occurrence (if present) using the
            # new snooze time stored in alarmd
            occs.update(alarmd, origalarm)


def snooze_alarms(alarmst, stime):
    newalarm = ((int(_time.time()) + stime) // 60 + 1) * 60

    alarmsd = divide_alarms(alarmst)
    for filename in alarmsd:
        for alarmid in alarmsd[filename]:
            update_alarm(filename, alarmid, newalarm)

            # Signal the event after updating the database, so, for example,
            # the tasklist can be correctly updated
            alarm_off_event.signal(filename=filename, alarmid=alarmid)

    # Do not search occurrences (thus restarting the timer) inside the for loop,
    # otherwise it messes up with the wx.CallAfter() that manages the activated
    # alarms in the interface
    organizer_timer_api.search_next_occurrences()


def dismiss_alarms(alarmst):
    alarmsd = divide_alarms(alarmst)
    for filename in alarmsd:
        for alarmid in alarmsd[filename]:
            qconn = core_api.get_connection(filename)
            cursor = qconn.cursor()
            cursor.execute(queries.alarms_delete_id, (alarmid, ))
            core_api.give_connection(filename, qconn)

            # It's necessary to change the dismiss status, otherwise it's
            # possible that a database is loaded and some of its alarms are
            # activated: if at that point those alarms are dismissed and then
            # the user tries to close the database, the database will seem
            # unmodified, and won't ask to be saved
            global dismiss_state
            dismiss_state[filename] = True

            # Signal the event after updating the database, so, for example,
            # the tasklist can be correctly updated
            alarm_off_event.signal(filename=filename, alarmid=alarmid)


def insert_alarm(filename, id_, start, end, origalarm, snooze):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.alarms_insert, (id_, start, end, origalarm, snooze))
    core_api.give_connection(filename, conn)
    aid = cur.lastrowid
    return aid


def update_alarm(filename, alarmid, newalarm):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.alarms_update_id, (newalarm, alarmid))
    core_api.give_connection(filename, qconn)


def copy_alarms(filename, id_):
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
        curm.execute(queries.copyalarms_insert, (o['A_id'], id_, o['A_start'],
                                                 o['A_end'], o['A_alarm'],
                                                 o['A_snooze']))
    core_api.give_memory_connection(mem)


def paste_alarms(filename, id_, oldid):
    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copyalarms_select_id, (oldid, ))
    core_api.give_memory_connection(mem)

    for occ in curm:
        insert_alarm(filename, id_, occ['CA_start'], occ['CA_end'],
                     occ['CA_alarm'], occ['CA_snooze'])


def delete_alarms(filename, id_, hid):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.alarms_update_id_delete, (hid, id_))
    core_api.give_connection(filename, qconn)

    # Signal the event after updating the database, so, for example,
    # the tasklist can be correctly updated
    alarm_off_event.signal(filename=filename, id_=id_)


def undelete_alarms(filename, id_, hid):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.alarms_update_id_undelete, (id_, hid))
    core_api.give_connection(filename, qconn)


def clean_deleted_alarms(filename):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.alarms_delete_clean)
    core_api.give_connection(filename, qconn)


def clean_old_history_alarms(filename, hids):
    qconn = sqlite3.connect(filename)
    cursor = qconn.cursor()
    for hid in hids:
        cursor.execute(queries.alarms_delete_clean_soft, (hid[0], ))
    qconn.commit()
    qconn.close()


def divide_alarms(alarmsl):
    alarmsd = {}

    for alarm in alarmsl:
        filename = alarm[0]
        alarmid = alarm[1]

        if filename not in alarmsd:
            alarmsd[filename] = []

        alarmsd[filename].append(alarmid)

    return alarmsd
