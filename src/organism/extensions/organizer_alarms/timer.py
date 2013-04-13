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

from threading import Timer
import time as _time

from organism.coreaux_api import log, Event
import organism.core_api as core_api
import organism.extensions.organizer_api as organizer_api

import occurrences
import queries

search_alarms_event = Event()

timer = None


class Alarms():
    # Note that here "alarm" can also mean one of "alarm", "start", or "end" if
    # it's the next "reminder": this is because originally this function did
    # get only "alarm"s indeed...
    def __init__(self):
        self.alarms = {}
        self.next = None

    def add(self, last_search, alarm):
        filename = alarm['filename']
        id_ = alarm['id_']

        tl = [alarm['start'], alarm['end'], alarm['alarm']]
        # Sort alarm, start, end (None values are always put first)
        tl.sort()

        if self.next:
            if alarm['alarm'] == self.next or alarm['start'] == self.next or \
                                                     alarm['end'] == self.next:
                if filename not in self.alarms:
                    self.alarms[filename] = {}
                if id_ not in self.alarms[filename]:
                    self.alarms[filename][id_] = []
                self.alarms[filename][id_].append(alarm)
                return True
            else:
                for t in tl:
                    if last_search < t < self.next:
                        self.next = t
                        self.alarms = {filename: {id_: [alarm]}}
                        return True
                else:
                    return False
        else:
            for t in tl:
                if last_search < t:
                    self.next = t
                    self.alarms = {filename: {id_: [alarm]}}
                    return True
            else:
                return False

    def except_(self, filename, id_, start, end, inclusive):
        # Test if the item has some rules, for safety, also for coherence with
        # organizer.items.TempOccurrences.except_
        try:
            alarmsc = self.alarms[filename][id_][:]
        except KeyError:
            pass
        else:
            for alarm in alarmsc:
                if start <= alarm['start'] <= end or \
                       (inclusive and alarm['start'] <= start <= alarm['end']):
                    self.alarms[filename][id_].remove(alarm)
        # Do not reset self.next to None in case there are no alarms left: this
        # lets restart_timer, and consequently search_alarms, ignore the
        # excepted alarms at the following search

    def try_delete_one(self, filename, id_, start, end, alarm):
        if filename in self.alarms and id_ in self.alarms[filename]:
            for alarmd in self.alarms[filename][id_][:]:
                if start == alarmd['start'] and end == alarmd['end'] and \
                                                       alarm == alarmd['alarm']:
                    self.alarms[filename][id_].remove(alarmd)
                    if not self.alarms[filename][id_]:
                        del self.alarms[filename][id_]
                    if not self.alarms[filename]:
                        del self.alarms[filename]
                    # Delete only one occurrence, hence the name try_delete_one
                    return True
        return False

    def get_dict(self):
        return self.alarms

    def get_next_alarm(self):
        return self.next

    def get_time_span(self):
        minstart = None
        maxend = None
        for filename in self.alarms:
            for id_ in self.alarms[filename]:
                for alarm in self.alarms[filename][id_]:
                    # This assumes that start <= end
                    if minstart is None or alarm['start'] < minstart:
                        minstart = alarm['start']
                    if maxend is None or alarm['end'] > maxend:
                        maxend = alarm['end']
        return (minstart, maxend)


def search_alarms():
    # Currently this function should always be called without arguments
    #def search_alarms(filename=None, id_=None):
    filename = None
    id_ = None

    log.debug('Search alarms')

    alarms = Alarms()

    if filename is None:
        for filename in core_api.get_open_databases():
            last_search = get_last_search(filename)
            for id_ in core_api.get_items(filename):
                search_item_alarms(last_search, filename, id_, alarms)
    elif id_ is None:
        last_search = get_last_search(filename)
        for id_ in core_api.get_items(filename):
            search_item_alarms(last_search, filename, id_, alarms)
    else:
        last_search = get_last_search(filename)
        search_item_alarms(last_search, filename, id_, alarms)

    oldalarms = get_snoozed_alarms(alarms)

    restart_timer(oldalarms, alarms.get_next_alarm(), alarms.get_dict())


def search_item_alarms(last_search, filename, id_, alarms):
    rules = organizer_api.get_item_rules(filename, id_)
    for rule in rules:
        search_alarms_event.signal(last_search=last_search, filename=filename,
                                   id_=id_, rule=rule, alarms=alarms)


def get_snoozed_alarms(alarms):
    oldalarms = {}

    for filename in core_api.get_open_databases():
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        cur.execute(queries.alarms_select_alarms)
        core_api.give_connection(filename, conn)

        last_search = get_last_search(filename)

        for row in cur:
            itemid = row['A_item']
            start = row['A_start']
            end = row['A_end']
            snooze = row['A_snooze']

            # Check whether the snoozed alarm has a duplicate among the alarms
            # found using the alarm rules, and in that case delete the latter;
            # the creation of duplicates is possible especially when alarm
            # searches are performed in rapid succession, for example when
            # launching organism with multiple databases automatically opened
            # and many new alarms to be immediately activated
            # If I gave the possibility to use search_alarms for a specific
            # filename or id_, this check would probably become unnecessary
            alarms.try_delete_one(filename, itemid, start, end, row['A_alarm'])

            alarmd = {'filename': filename,
                      'id_': itemid,
                      'alarmid': row['A_id'],
                      'start': start,
                      'end': end,
                      'alarm': snooze}

            # For safety, also check that there aren't any alarms with snooze
            # <= last_search left (for example this may happen if an alarms is
            # temporarily undone together with its item, and then it's restored
            # with a redo)
            if snooze and snooze > last_search:
                alarms.add(last_search, alarmd)
            else:
                if filename not in oldalarms:
                    oldalarms[filename] = {}
                if itemid not in oldalarms[filename]:
                    oldalarms[filename][itemid] = []
                oldalarms[filename][itemid].append(alarmd)

    return oldalarms


def get_alarms(mint, maxt, filename, tempoccs):
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
            tempoccs.update(alarmd, origalarm, force=True)
        else:
            # Note that the second argument must be origalarm, not snooze, in
            # fact it's used to *update* the occurrence (if present) using the
            # new snooze time stored in alarmd
            tempoccs.update(alarmd, origalarm)


def set_last_search(filename, tstamp):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.alarmsproperties_update, (tstamp, ))
    core_api.give_connection(filename, conn)


def get_last_search(filename):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.alarmsproperties_select_search)
    core_api.give_connection(filename, conn)

    return cur.fetchone()['AP_last_search']


def restart_timer(oldalarms, next_alarm, alarmsd):
    cancel_timer()

    now = int(_time.time())

    if oldalarms:
        occurrences.activate_alarms(now, oldalarms, old=True)

    if next_alarm != None:
        if next_alarm <= now:
            occurrences.activate_alarms(next_alarm, alarmsd)
            search_alarms()
        else:
            next_loop = next_alarm - now
            global timer
            timer = Timer(next_loop, activate_alarms, (next_alarm, alarmsd, ))
            timer.start()

            log.debug('Timer refresh: {}'.format(next_loop))


def cancel_timer(kwargs=None):
    if timer:
        log.debug('Timer cancel')
        timer.cancel()


def activate_alarms(time, alarmsd):
    core_api.block_databases()

    occurrences.activate_alarms(time, alarmsd)
    search_alarms()

    core_api.release_databases()
