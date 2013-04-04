# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

from organism.coreaux_api import Event
import organism.core_api as core_api

import queries

update_item_rules_event = Event()
get_occurrences_event = Event()
get_alarms_event = Event()


class TempOccurrences():
    def __init__(self, mint, maxt):
        self.mint = mint
        self.maxt = maxt
        self.d = {}
    
    def update(self, occ, origalarm, force=False):
        filename = occ['filename']
        id_ = occ['id_']
        
        oocc = occ.copy()
        oocc['alarm'] = origalarm
        del oocc['alarmid']
        
        if filename in self.d and id_ in self.d[filename] and \
                                                 oocc in self.d[filename][id_]:
            self.d[filename][id_][self.d[filename][id_].index(oocc)] = occ
            return True
        elif force:
            return self._add(occ)
        else:
            return self.add(occ)

    def add(self, occ):
        if self.mint <= occ['start'] <= self.maxt or \
                  (occ['end'] and occ['start'] <= self.mint <= occ['end']) or \
                  (occ['alarm'] and self.mint <= occ['alarm'] <= self.maxt):
            return self._add(occ)
        else:
            return False
    
    def _add(self, occ):
        filename = occ['filename']
        id_ = occ['id_']
        
        if filename not in self.d:
            self.d[filename] = {}
        if id_ not in self.d[filename]:
            self.d[filename][id_] = []
        self.d[filename][id_].append(occ)
        
        return True
    
    def except_(self, filename, id_, start, end, inclusive):
        for o in self.d[filename][id_][:]:
            if start <= o['start'] <= end or \
                               (inclusive and o['start'] <= start <= o['end']):
                self.d[filename][id_].remove(o)
    
    def get_dict(self):
        return self.d


def insert_item(filename, id_, group, description='Insert item'):
    query_redo = queries.rules_insert.format(id_)
    query_undo = queries.rules_delete_id.format(id_)
    
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(query_redo, ('', ))
    core_api.give_connection(filename, qconn)
    
    core_api.insert_history(filename, group, id_, 'rules_insert', description,
                            query_redo, '', query_undo, '')


def update_item_rules(filename, id_, rules, group,
                      description='Update item rules'):
    if isinstance(rules, list):
        qrules = rules_to_string(rules)
    else:
        qrules = rules
        rules = string_to_rules(rules)
    
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.rules_select_id, (id_, ))
    sel = cursor.fetchone()
    
    if sel:
        unqrules = sel['R_rules']
    else:
        unqrules = ''
    
    query_redo = queries.rules_update_id.format(str(id_))
    query_undo = queries.rules_update_id.format(str(id_))
    
    cursor.execute(query_redo, (qrules, ))
    
    core_api.give_connection(filename, qconn)
    
    core_api.insert_history(filename, group, id_, 'rules_update', description,
                            query_redo, qrules, query_undo, unqrules)
    
    update_item_rules_event.signal(filename=filename, id_=id_)


def copy_item_rules(filename, id_):
    record = [id_, ]
    
    conn = core_api.get_connection(filename)
    cur = conn.cursor()
    cur.execute(queries.rules_select_id, (id_, ))
    record.extend(cur.fetchone())
    core_api.give_connection(filename, conn)
    
    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copyrules_insert, record)
    core_api.give_memory_connection(mem)


def paste_item_rules(filename, id_, oldid, group, description):
    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copyrules_select_id, (oldid, ))
    core_api.give_memory_connection(mem)
    
    update_item_rules(filename, id_, curm.fetchone()['CR_rules'], group,
                      description)


def delete_item_rules(filename, id_, group, description='Delete item rules'):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    
    cursor.execute(queries.rules_select_id, (id_, ))
    sel = cursor.fetchone()
    
    if sel:
        current_rules = sel['R_rules']
    else:
        current_rules = ''
    
    query_redo = queries.rules_delete_id.format(id_)
    query_undo = queries.rules_insert.format(id_)
    
    cursor.execute(query_redo)
    
    core_api.give_connection(filename, qconn)
    
    return core_api.insert_history(filename, group, id_, 'rules_delete',
                                   description, query_redo, '', query_undo,
                                   current_rules)


def get_item_rules(filename, id_):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.rules_select_id, (id_, ))
    row = cursor.fetchone()
    core_api.give_connection(filename, qconn)
    
    if row:
        return string_to_rules(row['R_rules'])
    else:
        return {}


def rules_to_string(rules):
    string = ''
    # It's possible that rules arrives here as None
    if rules:
        for rule in rules:
            for key in rule:
                sub = ':'.join((key, str(rule[key])))
                string = ''.join((string, sub, ';'))
            string = ''.join((string, '|'))
    
    return string


def string_to_rules(string):
    # Initialize rules in case string is False
    rules = []
    if string:
        rules = string.split('|')
        for i, v in enumerate(rules):
            strule = v.split(';')
            rules[i] = {}
            for sub in strule:
                spl = sub.split(':')
                # Get rid of the empty string coming from the final ; created
                # by rules_to_string()
                if spl[0]:
                    rules[i][spl[0]] = spl[1]
    
    # The last element is empty due to how the string is formatted by
    # rules_to_string()
    return rules[:-1]


def get_occurrences(mint, maxt):
    tempoccs = TempOccurrences(mint, maxt)
    
    for filename in core_api.get_open_databases():
        for id_ in core_api.get_items(filename):
            rules = get_item_rules(filename, id_)
            for rule in rules:
                get_occurrences_event.signal(mint=mint, maxt=maxt,
                                             filename=filename, id_=id_,
                                             rule=rule, tempoccs=tempoccs)
    
    # Get alarms after all occurrences, to avoid except rules
    for filename in core_api.get_open_databases():
        get_alarms_event.signal(mint=mint, maxt=maxt, filename=filename,
                                tempoccs=tempoccs)
    
    d = tempoccs.get_dict()
    tempoccsl = []
    for f in d:
        for i in d[f]:
            for o in d[f][i]:
                tempoccsl.append(o)
    
    def compare(i):
        return i['start']
    
    tempoccsl.sort(key=compare)
    
    return tempoccsl
