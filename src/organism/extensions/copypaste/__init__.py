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

copy_items_event = Event()
item_copy_event = Event()
item_paste_event = Event()


def copy_items(filename, cids, cut=False, group=None,
               description='Cut items'):
    qmemory = core_api.get_memory_connection()
    cursorm = qmemory.cursor()
    cursorm.execute(queries.copy_delete)
    core_api.give_memory_connection(qmemory)
    
    copy_items_event.signal()
    
    for id_ in cids:
        info = core_api.get_item_info(filename, id_)
        record = (id_, info['parent'], info['previous'], info['text'])
        
        qmemory = core_api.get_memory_connection()
        cursorm = qmemory.cursor()
        cursorm.execute(queries.copy_insert, record)
        core_api.give_memory_connection(qmemory)
        
        item_copy_event.signal(filename=filename, id_=id_)
    
    if cut and group:
        core_api.delete_items(filename, cids, group=group,
                              description=description)

    
def paste_items(filename, baseid, mode, group, description='Paste items'):
    qmemory = core_api.get_memory_connection()
    cursor = qmemory.cursor()
    cursor.execute(queries.copy_select_parent_roots)
    roots = cursor.fetchall()
    core_api.give_memory_connection(qmemory)
    
    ids = {}
    
    def recurse(baseid, previd):
        cursor.execute(queries.copy_select_parent, (baseid, previd))
        child = cursor.fetchone()
        if child:
            id_ = child['C_id']
            
            ids[id_] = core_api.append_item(filename, ids[baseid], group=group,
                                            text=child['C_text'],
                                            description=description)
            
            item_paste_event.signal(filename=filename, id_=ids[id_],
                                    oldid=id_, group=group,
                                    description=description)
            
            recurse(id_, 0)
            recurse(baseid, id_)
    
    if mode == 'siblings':
        roots.reverse()
    
    for root in roots:
        if mode == 'children':
            ids[root['C_id']] = core_api.append_item(filename, baseid,
                                                     group=group,
                                                     text=root['C_text'],
                                                     description=description)
        elif mode == 'siblings':
            ids[root['C_id']] = core_api.insert_item_after(filename, baseid,
                                                       group=group,
                                                       text=root['C_text'],
                                                       description=description)
        
        item_paste_event.signal(filename=filename, id_=ids[root['C_id']],
                                oldid=root['C_id'], group=group,
                                description=description)
        
        recurse(root['C_id'], 0)
    
    newroots = []
    for r in roots:
        newroots.append(ids[r['C_id']])
    
    return newroots

    
def has_copied_items(filename):
    qmemory = core_api.get_memory_connection()
    cursor = qmemory.cursor()
    cursor.execute(queries.copy_select_check)
    core_api.give_memory_connection(qmemory)
    
    if cursor.fetchone():
        return True
    else:
        return False


def main():
    qmemory = core_api.get_memory_connection()
    cursor = qmemory.cursor()
    cursor.execute(queries.copy_create)
    core_api.give_memory_connection(qmemory)
