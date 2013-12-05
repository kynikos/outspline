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

import json
import time as _time

from outspline.coreaux_api import log, Event
import outspline.core_api as core_api

import queries
from exceptions import (BadOccurrenceError, BadExceptRuleError,
                                                   ConflictingRuleHandlerError)

update_item_rules_conditional_event = Event()
get_alarms_event = Event()

rule_handlers = {}
cdbs = set()


class OccurrencesRange():
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


def install_rule_handler(rulename, handler):
    global rule_handlers

    if rulename not in rule_handlers:
        rule_handlers[rulename] = handler
    else:
        raise ConflictingRuleHandlerError()

def insert_item(filename, id_, group, description='Insert item'):
    if filename in cdbs:
        query_redo = queries.rules_insert.format(id_)
        query_undo = queries.rules_delete_id.format(id_)

        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()
        cursor.execute(query_redo, (rules_to_string([]), ))
        core_api.give_connection(filename, qconn)

        core_api.insert_history(filename, group, id_, 'rules_insert',
                description, query_redo, rules_to_string([]), query_undo, None)


def update_item_rules(filename, id_, rules, group,
                                              description='Update item rules'):
    update_item_rules_no_event(filename, id_, rules, group,
                                                       description=description)

    # Note that update_item_rules_no_event can be called directly, thus not
    # signalling this event
    update_item_rules_conditional_event.signal(filename=filename, id_=id_)


def update_item_rules_no_event(filename, id_, rules, group,
                                              description='Update item rules'):
    if isinstance(rules, list):
        rules = rules_to_string(rules)

    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.rules_select_id, (id_, ))
    sel = cursor.fetchone()

    # The query should always return a result, so sel should never be None
    unrules = sel['R_rules']

    query_redo = queries.rules_update_id.format(id_)
    query_undo = queries.rules_update_id.format(id_)

    cursor.execute(query_redo, (rules, ))

    core_api.give_connection(filename, qconn)

    core_api.insert_history(filename, group, id_, 'rules_update', description,
                            query_redo, rules, query_undo, unrules)


def copy_item_rules(filename, id_):
    record = [id_, ]

    if filename in cdbs:
        conn = core_api.get_connection(filename)
        cur = conn.cursor()
        cur.execute(queries.rules_select_id, (id_, ))
        record.extend(cur.fetchone())
        core_api.give_connection(filename, conn)
    else:
        # Even if filename doesn't support rules, create a correct table that
        # can be safely used when pasting
        record.append(rules_to_string([]))

    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copyrules_insert, record)
    core_api.give_memory_connection(mem)


def can_paste_safely(filename, exception):
    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copyrules_select, (rules_to_string([]), ))
    core_api.give_memory_connection(mem)

    # Warn if CopyRules table has rules but filename doesn't support them
    if curm.fetchone() and filename not in cdbs:
        raise exception()


def paste_item_rules(filename, id_, oldid, group, description):
    if filename in cdbs:
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copyrules_select_id, (oldid, ))
        core_api.give_memory_connection(mem)

        # Do not signal update_item_rules_conditional_event because it's
        # handled by organism_timer.timer.search_next_occurrences, and it would
        # slow down the pasting of items a lot; search_next_occurrences is
        # bound anyway to copypaste_api.bind_to_items_pasted
        update_item_rules_no_event(filename, id_, curm.fetchone()['CR_rules'],
                                                            group, description)


def delete_item_rules(filename, id_, group, description='Delete item rules'):
    if filename in cdbs:
        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()

        cursor.execute(queries.rules_select_id, (id_, ))
        sel = cursor.fetchone()

        # The query should always return a result, so sel should never be None
        current_rules = sel['R_rules']

        query_redo = queries.rules_delete_id.format(id_)
        query_undo = queries.rules_insert.format(id_)

        cursor.execute(query_redo)

        core_api.give_connection(filename, qconn)

        return core_api.insert_history(filename, group, id_, 'rules_delete',
                      description, query_redo, None, query_undo, current_rules)


def get_item_rules(filename, id_):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.rules_select_id, (id_, ))
    row = cursor.fetchone()
    core_api.give_connection(filename, qconn)

    # The query should always return a result, so row should never be None
    return string_to_rules(row['R_rules'])


def rules_to_string(rules):
    # rules should always be a list, never equal to None
    return json.dumps(rules, separators=(',',':'))


def string_to_rules(string):
    # Items without rules should have an empty list anyway (thus manageable by
    # json.loads)
    return json.loads(string)


def get_occurrences_range(mint, maxt):
    occs = OccurrencesRange(mint, maxt)

    search_start = (_time.time(), _time.clock())

    for filename in cdbs:
        for id_ in core_api.get_items_ids(filename):
            rules = get_item_rules(filename, id_)
            for rule in rules:
                rule_handlers[rule['rule']](mint, maxt, filename, id_, rule,
                                                                          occs)

        # Get active alarms *after* all occurrences, to avoid except rules
        get_alarms_event.signal(mint=mint, maxt=maxt, filename=filename,
                                                                     occs=occs)

    log.debug('Occurrences range found in {} (time) / {} (clock) s'.format(
              _time.time() - search_start[0], _time.clock() - search_start[1]))

    # Note that the list is practically unsorted: sorting its items is a duty
    # of the interface
    return occs
