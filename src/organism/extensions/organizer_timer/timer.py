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

search_next_item_occurrences_event = Event()
search_next_occurrences_event = Event()
activate_occurrences_event = Event()

timer = None


class NextOccurrences():
    def __init__(self):
        self.occs = {}
        self.next = None

    def add(self, base_time, occ):
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
            return self._update_next(base_time, occ)

    def _update_next(self, base_time, occ):
        tl = [occ['start'], occ['end'], occ['alarm']]
        # When sorting, None values are put first
        tl.sort()

        for t in tl:
            # Note that "base_time < t" is always False if t is None
            if base_time < t and (not self.next or t < self.next):
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
        # this lets restart_timer, and consequently search_next_occurrences,
        # ignore the excepted occurrences at the following search

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


def search_next_occurrences():
    # Currently this function should always be called without arguments
    #def search_next_occurrences(filename=None, id_=None):
    filename = None
    id_ = None

    log.debug('Search next occurrences')

    occs = NextOccurrences()

    if filename is None:
        for filename in core_api.get_open_databases():
            last_search = get_last_search(filename)
            for id_ in core_api.get_items_ids(filename):
                search_next_item_occurrences(last_search, filename, id_, occs)
            search_next_occurrences_event.signal(base_time=last_search,
                                                   filename=filename, occs=occs)
    elif id_ is None:
        last_search = get_last_search(filename)
        for id_ in core_api.get_items_ids(filename):
            search_next_item_occurrences(last_search, filename, id_, occs)
        search_next_occurrences_event.signal(base_time=last_search,
                                                   filename=filename, occs=occs)
    else:
        last_search = get_last_search(filename)
        search_next_item_occurrences(last_search, filename, id_, occs)
        search_next_occurrences_event.signal(base_time=last_search,
                                                   filename=filename, occs=occs)

    restart_timer(occs.get_next_occurrence_time(), occs.get_dict())


def search_next_item_occurrences(base_time, filename, id_, occs):
    rules = organizer_api.get_item_rules(filename, id_)
    for rule in rules:
        search_next_item_occurrences_event.signal(base_time=base_time,
                               filename=filename, id_=id_, rule=rule, occs=occs)


def get_last_search(filename):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.timerproperties_select_search)
    core_api.give_connection(filename, conn)

    return cur.fetchone()['TP_last_search']


def set_last_search_all(tstamp):
    for filename in core_api.get_open_databases():
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        cur.execute(queries.timerproperties_update, (tstamp, ))
        core_api.give_connection(filename, conn)


def set_last_search_all_safe(tstamp):
    for filename in core_api.get_open_databases():
        conn = core_api.get_connection(filename)
        cur = conn.cursor()

        cur.execute(queries.timerproperties_select_search)
        last_search = cur.fetchone()['TP_last_search']

        # It's possible that the database has last_search > tstamp, for example
        # when a database has just been opened while others were already open:
        # it would have a lower last_search than the other databases, and when
        # the next occurrences are searched, all the databases' last_search
        # values would be updated to the lower value, thus possibly reactivating
        # old alarms
        if tstamp > last_search:
            cur.execute(queries.timerproperties_update, (tstamp, ))

        core_api.give_connection(filename, conn)


def restart_timer(next_occurrence, occsd):
    cancel_timer()

    now = int(_time.time())

    if next_occurrence != None:
        if next_occurrence <= now:
            set_last_search_all_safe(next_occurrence)
            activate_occurrences(next_occurrence, occsd)
        else:
            # Reset last search time in every open database, so that if a rule
            # is created with an alarm time between the last search and now, the
            # alarm won't be activated
            set_last_search_all(now)

            next_loop = next_occurrence - now
            global timer
            timer = Timer(next_loop, activate_occurrences_block,
                                                       (next_occurrence, occsd))
            timer.start()

            log.debug('Timer restart: {}'.format(next_loop))
    else:
        # Even if no occurrence is found, reset last search time in every open
        # database, so that:
        # 1) this will let the next search_next_occurrences ignore the
        # occurrences excepted in the previous search
        # 2) if a rule is created with an alarm time between the last search and
        # now, the alarm won't be activated
        set_last_search_all(now)


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
    search_next_occurrences()
