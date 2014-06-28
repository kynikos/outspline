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

import json
import time as time_
import sqlite3

from outspline.static.pyaux import timeaux
from outspline.coreaux_api import log, Event
import outspline.core_api as core_api

import queries
from exceptions import (BadOccurrenceError, BadExceptRuleError,
                                                   ConflictingRuleHandlerError)

update_item_rules_conditional_event = Event()
delete_item_rules_event = Event()
get_alarms_event = Event()


class Database(object):
    def __init__(self, filename):
        self.filename = filename

        core_api.register_history_action_handlers(filename, 'rules_insert',
                    self._handle_history_insert, self._handle_history_delete)
        core_api.register_history_action_handlers(filename, 'rules_update',
                    self._handle_history_update, self._handle_history_update)
        core_api.register_history_action_handlers(filename, 'rules_delete',
                    self._handle_history_delete, self._handle_history_insert)

    # This method has to accept filename as the first argument, even though
    # it's part of this object
    def _handle_history_insert(self, filename, action, jparams, hid, type_,
                                                                    itemid):
        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_insert, (itemid, jparams))
        core_api.give_connection(filename, qconn)

    # This method has to accept filename as the first argument, even though
    # it's part of this object
    def _handle_history_update(self, filename, action, jparams, hid, type_,
                                                                    itemid):
        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_update_id, (jparams, itemid))
        core_api.give_connection(filename, qconn)

    # This method has to accept filename as the first argument, even though
    # it's part of this object
    def _handle_history_delete(self, filename, action, jparams, hid, type_,
                                                                    itemid):
        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_delete_id, (itemid, ))
        core_api.give_connection(filename, qconn)

    def insert_item(self, id_, group, description='Insert item'):
        srules = self.rules_to_string([])

        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_insert, (id_, srules, ))
        core_api.give_connection(self.filename, qconn)

        core_api.insert_history(self.filename, group, id_, 'rules_insert',
                                                    description, srules, None)

    def update_item_rules(self, id_, rules, group,
                                            description='Update item rules'):
        self.update_item_rules_no_event(id_, rules, group,
                                                    description=description)

        # Note that update_item_rules_no_event can be called directly, thus not
        # signalling this event
        update_item_rules_conditional_event.signal(filename=self.filename,
                                                        id_=id_, rules=rules)

    def update_item_rules_no_event(self, id_, rules, group,
                                            description='Update item rules'):
        if isinstance(rules, list):
            rules = self.rules_to_string(rules)

        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()

        cursor.execute(queries.rules_select_id, (id_, ))
        sel = cursor.fetchone()

        # The query should always return a result, so sel should never be None
        unrules = sel['R_rules']

        cursor.execute(queries.rules_update_id, (rules, id_))

        core_api.give_connection(self.filename, qconn)

        core_api.insert_history(self.filename, group, id_, 'rules_update',
                                                description, rules, unrules)

    def copy_item_rules(self, id_, rules_supported):
        record = [id_, ]

        if rules_supported:
            conn = core_api.get_connection(self.filename)
            cur = conn.cursor()
            cur.execute(queries.rules_select_id, (id_, ))
            record.extend(cur.fetchone())
            core_api.give_connection(self.filename, conn)
        else:
            # Even if the database doesn't support rules, create a correct
            # table that can be safely used when pasting
            record.append(self.rules_to_string([]))

        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyrules_insert, record)
        core_api.give_memory_connection(mem)

    def can_paste_safely(self, exception, rules_supported):
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyrules_select, (self.rules_to_string([]), ))
        core_api.give_memory_connection(mem)

        # Warn if CopyRules table has rules but filename doesn't support them
        if curm.fetchone() and not rules_supported:
            raise exception()

    def paste_item_rules(self, id_, oldid, group, description):
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyrules_select_id, (oldid, ))
        core_api.give_memory_connection(mem)

        # Do not signal update_item_rules_conditional_event because it's
        # handled by organism_timer.timer.NextOccurrencesEngine, and it would
        # slow down the pasting of items a lot; NextOccurrencesEngine is bound
        # anyway to copypaste_api.bind_to_items_pasted
        self.update_item_rules_no_event(id_, curm.fetchone()['CR_rules'],
                                                            group, description)

    def delete_item_rules(self, id_, text, group,
                                            description='Delete item rules'):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()

        cursor.execute(queries.rules_select_id, (id_, ))
        sel = cursor.fetchone()

        # The query should always return a result, so sel should never be None
        current_rules = sel['R_rules']

        cursor.execute(queries.rules_delete_id, (id_, ))

        core_api.give_connection(self.filename, qconn)

        core_api.insert_history(self.filename, group, id_, 'rules_delete',
                                            description, None, current_rules)

        delete_item_rules_event.signal(filename=self.filename, id_=id_,
                                                                    text=text)

    def get_item_rules(self, id_):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_select_id, (id_, ))
        row = cursor.fetchone()
        core_api.give_connection(self.filename, qconn)

        # The query should always return a result, so row should never be None
        return self.string_to_rules(row['R_rules'])

    def get_all_valid_item_rules(self):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_select_all, (self.rules_to_string([]), ))
        core_api.give_connection(self.filename, qconn)

        return cursor

    def get_all_item_rules(self):
        qconn = core_api.get_connection(self.filename)
        cursor = qconn.cursor()
        cursor.execute(queries.rules_select)
        core_api.give_connection(self.filename, qconn)

        return cursor

    @staticmethod
    def rules_to_string(rules):
        # rules should always be a list, never equal to None
        return json.dumps(rules, separators=(',',':'))

    @staticmethod
    def string_to_rules(string):
        # Items without rules should have an empty list anyway (thus manageable
        # by json.loads)
        return json.loads(string)


class Rules(object):
    def __init__(self):
        self.handlers = {}

    def install_rule_handler(self, rulename, handler):
        if rulename not in self.handlers:
            self.handlers[rulename] = handler
        else:
            raise ConflictingRuleHandlerError()


class OccurrencesRange(object):
    def __init__(self, mint, maxt):
        self.mint = mint
        self.maxt = maxt
        self.d = {}
        self.actd = {}

    def update(self, occ, origalarm):
        return self._update(self.d, self.add_safe, self._replace, occ,
                                                                     origalarm)

    def move_active(self, occ, origalarm):
        return self._update(self.actd, self.add_active, self._move, occ,
                                                                     origalarm)

    def add(self, occ):
        # Make sure this occurrence is compliant with the requirements defined
        # in organism_api.update_item_rules
        if occ['start'] and (not occ['end'] or occ['end'] > occ['start']):
            return self.add_safe(occ)
        else:
            raise BadOccurrenceError()

    def add_safe(self, occ):
        # This method must accept the same arguments as self.add_active
        # Occurrences with self.mint == occ['end'] shouldn't be added, as
        # they're not considered part of the end minute
        if self.mint <= occ['start'] <= self.maxt or \
                   (occ['end'] and occ['start'] <= self.mint < occ['end']) or \
                     (occ['alarm'] and self.mint <= occ['alarm'] <= self.maxt):
            self._add(self.d, occ)
            return True
        else:
            return False

    def add_active(self, occ):
        # This method must accept the same arguments as self.add
        return self._add(self.actd, occ)

    def _update(self, occsd, add, action, occ, origalarm):
        filename = occ['filename']
        id_ = occ['id_']

        oocc = occ.copy()
        oocc['alarm'] = origalarm
        del oocc['alarmid']

        try:
            occsd[filename][id_]
        except KeyError:
            return add(occ)
        else:
            try:
                i = occsd[filename][id_].index(oocc)
            except ValueError:
                return add(occ)
            else:
                action(occsd[filename][id_], i, occ)
                return True

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

    def _replace(self, ioccs, i, occ):
        # This method must accept the same arguments as self._move
        ioccs[i] = occ

    def _move(self, ioccs, i, occ):
        # This method must accept the same arguments as self._replace
        del ioccs[i]
        self.add_active(occ)

    def except_(self, filename, id_, start, end, inclusive):
        # Make sure this call is compliant with the requirements defined in
        # organism_api.update_item_rules
        if start and start < end:
            self.except_safe(filename, id_, start, end, inclusive)
        else:
            raise BadExceptRuleError()

    def except_safe(self, filename, id_, start, end, inclusive):
        # If an except rule is put at the start of the rules list for an item,
        # self.d[filename][id_] wouldn't exist yet; note that if the item is
        # the first one being processed in the database, even self.d[filename]
        # wouldn't exist
        # This way the except rule is of course completely useless, however if
        # the user has to be warned at all, it must be done in the interface
        # when he saves the rules list, not here, where the exception has to be
        # just silenced
        try:
            dc = self.d[filename][id_][:]
        except KeyError:
            pass
        else:
            for o in dc:
                # Occurrences with start == o['end'] shouldn't be excepted, as
                # they're not considered part of the end minute
                if start <= o['start'] <= end or \
                                (inclusive and o['start'] <= start < o['end']):
                    self.d[filename][id_].remove(o)
                    if not self.d[filename][id_]:
                        del self.d[filename][id_]
                        if not self.d[filename]:
                            del self.d[filename]

    def get_dict(self):
        return self.d

    def get_active_dict(self):
        return self.actd

    def get_list(self):
        occsl = []
        for f in self.d:
            for i in self.d[f]:
                for o in self.d[f][i]:
                    occsl.append(o)
        return occsl

    def get_active_list(self):
        occsl = []
        for f in self.actd:
            for i in self.actd[f]:
                for o in self.actd[f][i]:
                    occsl.append(o)
        return occsl

    def get_next_completion_time(self):
        # Note that this method ignores self.actd _deliberately_
        ctime = None
        for f in self.d:
            for i in self.d[f]:
                for o in self.d[f][i]:
                    t = max((o['end'], o['start'], o['alarm']))
                    if t and (not ctime or t < ctime):
                        ctime = t
        return ctime

    def get_item_time_span(self, filename, id_):
        # Note that this method ignores self.actd _deliberately_
        try:
            occs = self.d[filename][id_]
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


class OccurrencesRangeSearch(object):
    def __init__(self, mint, maxt, cdbs, databases, rule_handlers):
        self.mint = mint
        self.maxt = maxt
        self.cdbs = cdbs
        self.databases = databases
        self.rule_handlers = rule_handlers
        self.occs = OccurrencesRange(mint, maxt)
        self.utcoffset = timeaux.UTCOffset()
        self.utcmint = mint - self.utcoffset.compute(mint)
        self._search_item = self._search_item_continue

    def start(self):
        search_start = (time_.time(), time_.clock())

        for filename in self.cdbs.copy():
            for row in self.databases[filename].get_all_valid_item_rules():
                id_ = row['R_id']
                rules = Database.string_to_rules(row['R_rules'])
                self._search_item(filename, id_, rules)

            # Get active alarms *after* all occurrences, to avoid except rules
            get_alarms_event.signal(mint=self.mint, maxt=self.maxt,
                                            filename=filename, occs=self.occs)

        log.debug('Occurrences range found in {} (time) / {} (clock) s'.format(
                                            time_.time() - search_start[0],
                                            time_.clock() - search_start[1]))

    def stop(self):
        self._search_item = self._search_item_stop

    def get_results(self):
        # Note that the list is practically unsorted: sorting its items is a
        # duty of the interface
        return self.occs

    def _search_item(self, filename, id_, rules):
        # This method is defined dynamically
        pass

    def _search_item_continue(self, filename, id_, rules):
        for rule in rules:
            self.rule_handlers[rule['rule']](self.mint, self.utcmint,
                    self.maxt, self.utcoffset, filename,  id_, rule, self.occs)

    def _search_item_stop(self, filename, id_, rules):
        raise Exception()
