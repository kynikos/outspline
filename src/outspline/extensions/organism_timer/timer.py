# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

from threading import Timer
import time as _time

from outspline.coreaux_api import log, Event
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api

import queries
from exceptions import (BadOccurrenceError, BadExceptRuleError,
                                                    ConflictingRuleHandlerError)

get_next_occurrences_event = Event()
search_next_occurrences_event = Event()
activate_occurrences_range_event = Event()
activate_old_occurrences_event = Event()
activate_occurrences_event = Event()

timer = None

rule_handlers = {}
cdbs = set()


class NextOccurrences():
    def __init__(self):
        self.occs = {}
        self.oldoccs = {}
        self.next = None

    def add(self, base_time, occ):
        # Make sure this occurrence is compliant with the requirements defined
        # in organism_api.update_item_rules
        if occ['start'] and (not occ['end'] or occ['end'] > occ['start']):
            return self.add_safe(base_time, occ)
        else:
            raise BadOccurrenceError()

    def add_safe(self, base_time, occ):
        if self.next and self.next in (occ['alarm'], occ['start'], occ['end']):
            self._add(self.occs, occ)
            return True
        else:
            return self._update_next(base_time, occ)

    def add_old(self, occ):
        self._add(self.oldoccs, occ)

    def _add(self, occsd, occ):
        filename = occ['filename']
        id_ = occ['id_']

        try:
            occsd[filename][id_]
        except KeyError:
            try:
                occsd[filename]
            except KeyError:
                occsd[filename] = {}
            occsd[filename][id_] = []
        occsd[filename][id_].append(occ)

    def _update_next(self, base_time, occ):
        tl = [occ['alarm'], occ['start'], occ['end']]
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
        # Make sure this call is compliant with the requirements defined in
        # organism_api.update_item_rules
        if start and start < end:
            self.except_safe(filename, id_, start, end, inclusive)
        else:
            raise BadExceptRuleError()

    def except_safe(self, filename, id_, start, end, inclusive):
        # Test if the item has some rules, for safety, also for coherence with
        # organism.items.OccurrencesRange.except_safe
        try:
            occsc = self.occs[filename][id_][:]
        except KeyError:
            pass
        else:
            for occ in occsc:
                if start <= occ['start'] <= end or (inclusive and
                                           occ['start'] <= start <= occ['end']):
                    self.occs[filename][id_].remove(occ)
        # Do not try to update self.next (even in case there are no occurrences
        # left): this lets search_next_occurrences reset the last search time to
        # this value, thus ignoring the excepted occurrences at the following
        # search

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

    def get_old_dict(self):
        return self.oldoccs

    def get_next_occurrence_time(self):
        return self.next

    def get_time_span(self):
        # Note that this method ignores self.oldoccs _deliberately_
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


def install_rule_handler(rulename, handler):
    global rule_handlers

    if rulename not in rule_handlers:
        rule_handlers[rulename] = handler
    else:
        raise ConflictingRuleHandlerError()


def get_next_occurrences(base_time=None, base_times=None):
    occs = NextOccurrences()

    search_start = (_time.time(), _time.clock())

    for filename in cdbs:
        if not base_time:
            base_time = base_times[filename]

        for id_ in core_api.get_items_ids(filename):
            rules = organism_api.get_item_rules(filename, id_)

            for rule in rules:
                rule_handlers[rule['rule']](base_time, filename, id_, rule,
                                                                           occs)

        get_next_occurrences_event.signal(base_time=base_time,
                                                   filename=filename, occs=occs)

    log.debug('Next occurrences found in {} (time) / {} (clock) s'.format(
               _time.time() - search_start[0], _time.clock() - search_start[1]))

    return occs


def get_last_search(filename):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.timerproperties_select_search)
    core_api.give_connection(filename, conn)

    return cur.fetchone()['TP_last_search']


def get_last_search_all():
    return {filename: get_last_search(filename) for filename in cdbs}


def set_last_search(filename, tstamp):
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.timerproperties_update, (tstamp, ))
    core_api.give_connection(filename, conn)


def set_last_search_all(tstamp):
    for filename in cdbs:
        set_last_search(filename, tstamp)


def set_last_search_all_safe(tstamp):
    for filename in cdbs:
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


def search_old_occurrences(filename):
    # Do not use directly search_next_occurrences to search for old occurrences
    # when opening a database, in fact if the database hasn't been opened for a
    # while and it has _many_ old occurrences to activate,
    # search_next_occurrences could recurse too many times, eventually raising
    # a RuntimeError exception
    # This function can also speed up opening an old database if it has many
    # occurrences to activate immediately

    # Search until 2 minutes ago and let search_next_occurrences handle the
    # rest, so as to make sure not to interfere with its functionality
    whileago = int(_time.time()) - 120
    last_search = get_last_search(filename)

    if whileago > last_search:
        log.debug('Search old occurrences')

        occs = organism_api.get_occurrences_range(mint=last_search,
                                                                  maxt=whileago)
        occsd = occs.get_dict()
        # Executing occs.get_active_dict here wouldn't make sense; let
        # search_next_occurrences deal with snoozed and active alarms

        set_last_search(filename, whileago)

        if filename in occsd:
            # Note that occsd still includes occurrence times equal to
            # last_search: these must be excluded because last_search is the
            # time that was last already activated
            activate_occurrences_range_event.signal(filename=filename,
                         mint=last_search, maxt=whileago, occsd=occsd[filename])


def search_next_occurrences(kwargs=None):
    # kwargs is passed from the bindings in __init__

    log.debug('Search next occurrences')

    occs = get_next_occurrences(base_times=get_last_search_all())
    next_occurrence = occs.get_next_occurrence_time()
    occsd = occs.get_dict()
    oldoccsd = occs.get_old_dict()

    cancel_search_next_occurrences()

    now = int(_time.time())

    activate_old_occurrences_event.signal(oldoccsd=oldoccsd)

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

            log.debug('Next occurrence in {} seconds'.format(next_loop))
    else:
        # Even if no occurrence is found, reset last search time in every open
        # database, so that:
        # 1) this will let the next get_next_occurrences ignore the occurrences
        # excepted in the previous search
        # 2) if a rule is created with an alarm time between the last search and
        # now, the alarm won't be activated
        set_last_search_all(now)

    search_next_occurrences_event.signal()


def cancel_search_next_occurrences(kwargs=None):
    # kwargs is passed from the binding to core_api.bind_to_exit_app_1
    if timer and timer.is_alive():
        log.debug('Cancel timer')
        timer.cancel()


def activate_occurrences_block(time, occsd):
    # It's important that the databases are blocked on this thread, and not on
    # the main thread, otherwise the program would hang if some occurrences are
    # activated while the user is performing an action
    core_api.block_databases()
    activate_occurrences(time, occsd)
    core_api.release_databases()


def activate_occurrences(time, occsd):
    activate_occurrences_event.signal(time=time, occsd=occsd)
    search_next_occurrences()
