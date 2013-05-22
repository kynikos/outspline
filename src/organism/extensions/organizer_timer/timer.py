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

import queries

search_occurrences_event = Event()
restart_timer_event = Event()
activate_occurrences_event = Event()

timer = None


class NextOccurrences():
    def __init__(self):
        self.occs = {}
        self.next = None

    def add(self, last_search, occ):
        filename = occ['filename']
        id_ = occ['id_']

        if self.next and self.next in (occ['alarm'], occ['start'], occ['end']):
            try:
                self.occs[filename][id_]
            except KeyError:
                try:
                    self.occs[filename]
                except KeyError:
                    self.occs[filename] = {}
                self.occs[filename][id_] = []
            self.occs[filename][id_].append(occ)
            return True
        else:
            return self._update_next(last_search, occ)

    def _update_next(self, last_search, occ):
        tl = [occ['start'], occ['end'], occ['alarm']]
        # When sorting, None values are put first
        tl.sort()

        for t in tl:
            # Note that "last_search < t" is always False if t is None
            if last_search < t and (not self.next or t < self.next):
                self.next = t
                self.occs = {occ['filename']: {occ['id_']: [occ]}}
                return True
        else:
            return False

    def except_(self, filename, id_, start, end, inclusive):
        # Test if the item has some rules, for safety, also for coherence with
        # organizer.items.OccurrencesRange.except_
        try:
            occsc = self.occs[filename][id_][:]
        except KeyError:
            pass
        else:
            for occ in occsc:
                if start <= occ['start'] <= end or (inclusive and
                                           occ['start'] <= start <= occ['end']):
                    self.occs[filename][id_].remove(occ)
        # Do not reset self.next to None in case there are no occurrences left:
        # this lets restart_timer, and consequently search_occurrences, ignore
        # the excepted occurrences at the following search

    def try_delete_one(self, filename, id_, start, end, alarm):
        try:
            occsc = self.occs[filename][id_][:]
        except KeyError:
            return False
        else:
            for occd in occsc:
                if (start, end, alarm) == (occd['start'], occd['end'],
                                                                 occd['alarm']):
                    self.occs[filename][id_].remove(occd)
                    if not self.occs[filename][id_]:
                        del self.occs[filename][id_]
                    if not self.occs[filename]:
                        del self.occs[filename]
                    # Delete only one occurrence, hence the name try_delete_one
                    return True

    def get_dict(self):
        return self.occs

    def get_next_occurrence_time(self):
        return self.next

    def get_time_span(self):
        minstart = None
        maxend = None
        for filename in self.occs:
            for id_ in self.occs[filename]:
                for occ in self.occs[filename][id_]:
                    # This assumes that start <= end
                    if minstart is None or occ['start'] < minstart:
                        minstart = occ['start']
                    if maxend is None or occ['end'] > maxend:
                        maxend = occ['end']
        return (minstart, maxend)


def search_occurrences():
    # Currently this function should always be called without arguments
    #def search_occurrences(filename=None, id_=None):
    filename = None
    id_ = None

    log.debug('Search occurrences')

    occs = NextOccurrences()

    if filename is None:
        for filename in core_api.get_open_databases():
            last_search = get_last_search(filename)
            for id_ in core_api.get_items_ids(filename):
                search_item_occurrences(last_search, filename, id_, occs)
    elif id_ is None:
        last_search = get_last_search(filename)
        for id_ in core_api.get_items_ids(filename):
            search_item_occurrences(last_search, filename, id_, occs)
    else:
        last_search = get_last_search(filename)
        search_item_occurrences(last_search, filename, id_, occs)

    restart_timer(occs)


def search_item_occurrences(last_search, filename, id_, occs):
    rules = organizer_api.get_item_rules(filename, id_)
    for rule in rules:
        search_occurrences_event.signal(last_search=last_search,
                               filename=filename, id_=id_, rule=rule, occs=occs)


def set_last_search(filename, tstamp):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.timerproperties_update, (tstamp, ))
    core_api.give_connection(filename, conn)


def get_last_search(filename):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.timerproperties_select_search)
    core_api.give_connection(filename, conn)

    return cur.fetchone()['TP_last_search']


def restart_timer(occs):
    from organism.extensions.organizer_alarms import alarmsmod  # TEMP import *************************
    cancel_timer()

    now = int(_time.time())

    restart_timer_event.signal(time=now, occs=occs)

    # Note that these two parameters must be retrieved *after*
    # restart_timer_event is signalled
    next_occurrence = occs.get_next_occurrence_time()
    occsd = occs.get_dict()

    if next_occurrence != None:
        if next_occurrence <= now:
            activate_occurrences(next_occurrence, occsd)
        else:
            next_loop = next_occurrence - now
            global timer
            timer = Timer(next_loop, activate_occurrences_block,
                                                       (next_occurrence, occsd))
            timer.start()

            log.debug('Timer refresh: {}'.format(next_loop))
    else:
        # If no occurrence is found, execute activate_alarms, which will in turn  # MENTIONS activate_alarms ******************
        # execute set_last_search, so that if a rule is created with an alarm
        # time between the last search and now, the alarm won't be activated
        alarmsmod.activate_alarms(now, occsd)


def cancel_timer(kwargs=None):
    # kwargs is passed from the binding to core_api.bind_to_exit_app_1
    if timer and timer.is_alive():
        log.debug('Timer cancel')
        timer.cancel()


def activate_occurrences_block(time, occsd):
    # It's important that the database is blocked on this thread, and not on the
    # main thread, otherwise the program would hang if the user is performing
    # an action
    core_api.block_databases()
    activate_occurrences(time, occsd)
    core_api.release_databases()


def activate_occurrences(time, occsd):
    activate_occurrences_event.signal(time=time, occsd=occsd)
    search_occurrences()
