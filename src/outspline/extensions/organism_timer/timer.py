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

from threading import Thread, Timer
import time as time_

from outspline.static.pyaux import timeaux
from outspline.coreaux_api import log, Event
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api

import queries
from exceptions import (BadOccurrenceError, BadExceptRuleError,
                                                   ConflictingRuleHandlerError)

get_next_occurrences_event = Event()
search_old_occurrences_event = Event()
search_old_occurrences_end_event = Event()
search_next_occurrences_event = Event()
activate_occurrences_range_event = Event()
activate_old_occurrences_event = Event()
activate_occurrences_event = Event()


class Databases(object):
    def __init__(self, cdbs):
        self.cdbs = cdbs

    def get_last_search(self, filename):
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        cur.execute(queries.timerproperties_select_search)
        core_api.give_connection(filename, conn)

        return cur.fetchone()['TP_last_search']

    def get_last_search_all(self):
        return {filename: self.get_last_search(filename) for filename in
                                                            self.cdbs.copy()}

    def set_last_search(self, filename, tstamp):
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        # Use a UTC timestamp, so that even if the local time zone is changed
        # on the system, the timer behaves properly
        cur.execute(queries.timerproperties_update, (tstamp, ))
        core_api.give_connection(filename, conn)

    def set_last_search_all(self, tstamp):
        for filename in self.cdbs.copy():
            self.set_last_search(filename, tstamp)

    def set_last_search_all_safe(self, tstamp):
        for filename in self.cdbs.copy():
            conn = core_api.get_connection(filename)
            cur = conn.cursor()

            cur.execute(queries.timerproperties_select_search)
            last_search = cur.fetchone()['TP_last_search']

            # It's possible that the database has last_search > tstamp, for
            # example when a database has just been opened while others were
            # already open: it would have a lower last_search than the other
            # databases, and when the next occurrences are searched, all the
            # databases' last_search values would be updated to the lower
            # value, thus possibly reactivating old alarms
            if tstamp > last_search:
                # Use a UTC timestamp, so that even if the local time zone is
                # changed on the system, the timer behaves properly
                cur.execute(queries.timerproperties_update, (tstamp, ))

            core_api.give_connection(filename, conn)


class NextOccurrences(object):
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
        tl = [occ['alarm'], occ['start'], occ['end']]
        # When sorting, None values are put first
        tl.sort()

        for t in tl:
            # Note that "base_time < t" is always False if t is None
            if base_time < t:
                if not self.next or t < self.next:
                    self.next = t
                    self.occs = {occ['filename']: {occ['id_']: [occ]}}
                    return True
                elif t == self.next:
                    self._add(self.occs, occ)
                    return True
                else:
                    return False
        else:
            return False

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
                # Occurrences with start == o['end'] shouldn't be excepted, as
                # they're not considered part of the end minute
                if start <= occ['start'] <= end or (inclusive and
                                           occ['start'] <= start < occ['end']):
                    self.occs[filename][id_].remove(occ)
                    if not self.occs[filename][id_]:
                        del self.occs[filename][id_]
                        if not self.occs[filename]:
                            del self.occs[filename]
        # Do not try to update self.next (even in case there are no occurrences
        # left): this lets NextOccurrencesEngine reset the last search time to
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
        # Do not try to update self.next (even in case there are no occurrences
        # left): this would let NextOccurrencesEngine reset the last search
        # time to this value, thus avoiding repeating this same procedure
        # This function is however designed to be used just before adding a
        # very similar occurrence, so self.next will be updated by that anyway

    def get_dict(self):
        return self.occs

    def get_old_dict(self):
        return self.oldoccs

    def get_next_occurrence_time(self):
        return self.next

    def get_item_time_span(self, filename, id_):
        # Note that this method ignores self.oldoccs _deliberately_
        try:
            occs = self.occs[filename][id_]
        except KeyError:
            return False
        else:
            # The final minstart and maxend should never end up being None
            minstart = occs[0]['start']
            # Initialize maxend to minstart, which is surely != None
            maxend = minstart

            for occ in occs:
                # This assumes that start <= end
                minstart = min((minstart, occ['start']))
                # occ['end'] could be None
                maxend = max((occ['start'], occ['end'], maxend))

            return (minstart, maxend)


class Rules(object):
    def __init__(self):
        self.handlers = {}

    def install_rule_handler(self, rulename, handler):
        if rulename not in self.handlers:
            self.handlers[rulename] = handler
        else:
            raise ConflictingRuleHandlerError()


class NextOccurrencesSearch(object):
    def __init__(self, cdbs, rule_handlers, base_time=None, base_times=None):
        self.cdbs = cdbs
        self.rule_handlers = rule_handlers
        self.base_time = base_time
        self.base_times = base_times

    def start(self):
        # Note that this function must be kept separate from
        # NextOccurrencesEngine because it can be used without the latter (e.g.
        # by wxtasklist); note also that both functions generate their own
        # events
        self.occs = NextOccurrences()
        utcoffset = timeaux.UTCOffset()
        search_start = (time_.time(), time_.clock())

        for filename in self.cdbs.copy():
            if not self.base_time:
                self.base_time = self.base_times[filename]

            utcbase = self.base_time - utcoffset.compute(self.base_time)

            for row in organism_api.get_all_valid_item_rules(filename):
                id_ = row['R_id']
                rules = organism_api.convert_string_to_rules(row['R_rules'])

                for rule in rules:
                    self.rule_handlers[rule['rule']](self.base_time, utcbase,
                                    utcoffset, filename, id_, rule, self.occs)

            get_next_occurrences_event.signal(base_time=self.base_time,
                                            filename=filename, occs=self.occs)

        log.debug('Next occurrences found in {} (time) / {} (clock) s'.format(
                                              time_.time() - search_start[0],
                                              time_.clock() - search_start[1]))

    def get_results(self):
        return self.occs


class OldOccurrencesSearch(object):
    def __init__(self, databases, filename):
        self.databases = databases
        self.filename = filename

    def start(self):
        # Do not use directly NextOccurrencesEngine to search for old
        # occurrences when opening a database, in fact if the database hasn't
        # been opened for a while and it has _many_ old occurrences to
        # activate, NextOccurrencesEngine could recurse too many times,
        # eventually raising a RuntimeError exception
        # This function can also speed up opening an old database if it has
        # many occurrences to activate immediately

        # Search until 2 minutes ago and let NextOccurrencesEngine handle the
        # rest, so as to make sure not to interfere with its functionality
        self.whileago = int(time_.time()) - 120
        self.last_search = self.databases.get_last_search(self.filename)

        if self.whileago > self.last_search:
            log.debug('Search old occurrences')

            # Set the last search in this (main) thread, otherwise
            # NextOccurrencesEngine would race with this function, and possibly
            # do the same search, in fact still seeing the old last search
            # timestamp
            # Note that saving and closing the database after this point, but
            # before the search is finished and the old alarms are activated,
            # would lose all the old alarms
            self.databases.set_last_search(self.filename, self.whileago)

            # Use a thread to let the GUI be responsive and possibly abort the
            # search
            thread = Thread(target=self._continue)
            # Do not set the thread as a daemon, it's better to properly handle
            # closing the database
            thread.start()

    def _continue(self):
        search_old_occurrences_event.signal(filename=self.filename,
                                                last_search=self.last_search)

        self.search = organism_api.get_occurrences_range(mint=self.last_search,
                            maxt=self.whileago, filenames=(self.filename, ))
        self.search.start()

        # Bind only here, in fact the search may not even be started if
        # self.whileago <= self.last_search
        core_api.bind_to_close_database(self._handle_close_database)

        occs = self.search.get_results()
        occsd = occs.get_dict()
        # Executing occs.get_active_dict here wouldn't make sense; let
        # NextOccurrencesEngine deal with snoozed and active alarms

        if self.filename in occsd:
            # Note that occsd still includes occurrence times equal to
            # self.last_search: these must be excluded because self.last_search
            # is the time that was last already activated
            activate_occurrences_range_event.signal(filename=self.filename,
                                    mint=self.last_search, maxt=self.whileago,
                                    occsd=occsd[self.filename])

        search_old_occurrences_end_event.signal(filename=self.filename)

    def _handle_close_database(self, kwargs):
        if kwargs['filename'] == self.filename:
            self.search.stop()

            core_api.bind_to_close_database(self._handle_close_database, False)


class NextOccurrencesEngine(object):
    def __init__(self, cdbs, databases, rule_handlers):
        self.cdbs = cdbs
        self.databases = databases
        self.rule_handlers = rule_handlers
        self.timer = None

    def restart(self):
        # Note that this function must be kept separate from
        # NextOccurrencesSearch because the latter can be used without this
        # (e.g. by wxtasklist); note also that both functions generate their
        # own events

        log.debug('Search next occurrences')

        search = NextOccurrencesSearch(self.cdbs, self.rule_handlers,
                            base_times=self.databases.get_last_search_all())
        search.start()
        occs = search.get_results()
        next_occurrence = occs.get_next_occurrence_time()
        occsd = occs.get_dict()
        oldoccsd = occs.get_old_dict()

        self.cancel()

        now = int(time_.time())

        activate_old_occurrences_event.signal(oldoccsd=oldoccsd)

        if next_occurrence != None:
            if next_occurrence <= now:
                self.databases.set_last_search_all_safe(next_occurrence)
                self._activate_occurrences(next_occurrence, occsd)
            else:
                # Reset last search time in every open database, so that if a
                # rule is created with an alarm time between the last search
                # and now, the alarm won't be activated
                self.databases.set_last_search_all(now)

                next_loop = next_occurrence - now

                self.timer = Timer(next_loop, self._activate_occurrences_block,
                                                    (next_occurrence, occsd))
                self.timer.start()

                log.debug('Next occurrence in {} seconds'.format(next_loop))
        else:
            # Even if no occurrence is found, reset last search time in every
            # open database, so that:
            # 1) this will let the next NextOccurrencesSearch ignore the
            # occurrences excepted in the previous search
            # 2) if a rule is created with an alarm time between the last
            # search and now, the alarm won't be activated
            self.databases.set_last_search_all(now)

        search_next_occurrences_event.signal()

    def cancel(self):
        if self.timer and self.timer.is_alive():
            log.debug('Cancel timer')
            self.timer.cancel()

    def _activate_occurrences_block(self, time, occsd):
        # It's important that the databases are blocked on this thread, and not
        # on the main thread, otherwise the program would hang if some
        # occurrences are activated while the user is performing an action
        core_api.block_databases()
        self._activate_occurrences(time, occsd)
        core_api.release_databases()

    def _activate_occurrences(self, time, occsd):
        activate_occurrences_event.signal(time=time, occsd=occsd)
        self.restart()
