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

from organism.coreaux_api import Event

import databases
import queries

item_insert_event = Event()
item_delete_event = Event()

items = {}


class Item():
    filename = None
    id_ = None
    item = None

    def __init__(self, filename, id_, item):
        self.filename = filename
        self.id_ = id_
        self.item = item

    @classmethod
    def add(cls, filename=None, id_=None, item=None):
        if not item:
            item = cls.make_itemid(filename, id_)
        if not (filename and id_):
            filename = item.rsplit('_', 1)[0]
            id_ = item.rsplit('_', 1)[1]

        global items
        items[item] = cls(filename, id_, item)

    @classmethod
    def insert(cls, filename, mode, baseid, group, text='New item',
               description='Insert item'):
        if not baseid:
            parent = 0
            previous = cls.get_last_base_item_id(filename)
            updnext = False
        elif mode == 'child':
            base = cls.make_itemid(filename, baseid)
            parent = items[base].get_id()
            children = items[base].get_children()
            if children:
                previous = items[children[-1]].get_id()
            else:
                previous = 0
            updnext = False
        elif mode == 'sibling':
            base = cls.make_itemid(filename, baseid)
            parentt = items[base].get_parent()
            parent = items[parentt].get_id() if parentt else 0
            previous = items[base].get_id()
            updnext = items[base].get_next()

        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_insert.format('NULL', parent, previous, ),
                       (text, ))
        id_ = cursor.lastrowid
        cursor.execute(queries.history_insert,
                        (group, id_, 'insert', description,
                         queries.items_insert.format(id_, parent, previous, ),
                         text, queries.items_delete_id.format(id_), ''))

        databases.dbs[filename].connection.give(qconn)

        cls.add(filename=filename, id_=id_)

        item_insert_event.signal(filename=filename, id_=id_, group=group,
                                 description=description)

        if updnext:
            items[updnext].update(group, previous=id_, description=description)

        return id_

    def update(self, group, parent=None, previous=None, text=None,
               description='Update item'):
        filename = self.filename
        id_ = self.id_

        new_values = {'I_parent': parent,
                      'I_previous': previous}

        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id, (id_, ))
        current_values = cursor.fetchone()

        set = []
        unset = []
        for field in new_values:
            if new_values[field] != None:
                string = ''.join((field, '={}'))
                set.append(string.format(new_values[field]))
                unset.append(string.format(current_values[field]))

        if text != None:
            field = 'I_text=?'
            set.append(field)
            unset.append(field)
            qtext = text
            unqtext = current_values['I_text']
        else:
            qtext = ''
            unqtext = ''

        query_redo = queries.items_update_id.format(', '.join(set), id_)
        query_undo = queries.items_update_id.format(', '.join(unset), id_)

        if text != None:
            cursor.execute(query_redo, (qtext, ))
        else:
            cursor.execute(query_redo)

        cursor.execute(queries.history_insert, (group, id_, 'update',
                                                description, query_redo, qtext,
                                                query_undo, unqtext))

        databases.dbs[filename].connection.give(qconn)

    def delete(self, group, description='Delete item'):
        filename = self.filename
        id_ = self.id_
        prev = self.get_previous()
        next = self.get_next()

        if next:
            if prev:
                prev = items[prev].get_id()
            else:
                prev = 0
            items[next].update(group, previous=prev, description=description)

        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_select_id, (id_, ))
        current_values = cursor.fetchone()

        query_redo = queries.items_delete_id.format(id_)
        query_undo = queries.items_insert.format(id_,
                      current_values['I_parent'], current_values['I_previous'])

        cursor.execute(query_redo)
        cursor.execute(queries.history_insert, (group, id_, 'delete',
                                                description, query_redo, '',
                                                query_undo,
                                                current_values['I_text']))

        databases.dbs[filename].connection.give(qconn)

        self.remove()

        # This event is designed to be signalled _after_ self.remove()
        item_delete_event.signal(filename=filename, id_=id_,
                                 hid=cursor.lastrowid, group=group,
                                 description=description)

    def remove(self):
        global items
        del items[self.item]

    def shift(self, mode, group, description='Shift item'):
        # Keep all items[item].get_{next|previous|...} _before_ updates!
        item = self.item
        filename = self.filename
        id_ = self.id_
        if mode == 'up':
            prev = items[item].get_previous()
            parent = self.get_parent()
            prev2 = items[prev].get_previous()
            if prev2:
                prev2 = items[prev2].get_id()
            else:
                prev2 = 0
            next = items[item].get_next()
            prev = items[prev].get_id()
            self.update(group, previous=prev2, description=description)
            items[self.make_itemid(filename, prev)
                  ].update(group, previous=id_, description=description)
            if next:
                next = items[next].get_id()
                items[self.make_itemid(filename, next)
                      ].update(group, previous=prev, description=description)
        elif mode == 'down':
            next = items[item].get_next()
            parent = self.get_parent()
            prev = items[item].get_previous()
            if prev:
                prev = items[prev].get_id()
            else:
                prev = 0
            next2 = items[next].get_next()
            next = items[next].get_id()
            self.update(group, previous=next, description=description)
            items[self.make_itemid(filename, next)
                  ].update(group, previous=prev, description=description)
            if next2:
                next2 = items[next2].get_id()
                items[self.make_itemid(filename, next2)
                      ].update(group, previous=id_, description=description)
        elif mode == 'parent':
            parent = items[self.get_parent()].get_parent()
            parentid = items[parent].get_id()
            lastchild = items[parent].get_children()[-1]
            lastchild = items[lastchild].get_id()
            next = items[item].get_next()
            if next:
                prev = items[item].get_previous()
            self.update(group, parent=parentid, previous=lastchild,
                        description=description)
            if next:
                if prev:
                    prev = items[prev].get_id()
                else:
                    prev = 0
                next = items[next].get_id()
                items[self.make_itemid(filename, next)
                      ].update(group, previous=prev, description=description)

    def get_filename(self):
        return(self.filename)

    def get_id(self):
        return(self.id_)

    def get_children(self):
        qconn = databases.dbs[self.filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_children, (self.id_, ))
        databases.dbs[self.filename].connection.give(qconn)

        dd = {}
        for row in cursor:
            dd[row['I_previous']] = row['I_id']

        children = []
        prev = 0
        while prev in dd:
            children.append(self.make_itemid(self.filename, dd[prev]))
            prev = dd[prev]

        return children

    def get_all_info(self):
        qconn = databases.dbs[self.filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id, (self.id_, ))
        databases.dbs[self.filename].connection.give(qconn)
        row = cursor.fetchone()
        if row:
            return {'id_': self.id_,
                    'parent': row['I_parent'],
                    'previous': row['I_previous'],
                    'text': row['I_text']}
        else:
            return False

    @staticmethod
    def get_tree_item(filename, parentid, previd):
        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_parent, (parentid, previd))
        databases.dbs[filename].connection.give(qconn)
        row = cursor.fetchone()
        if row:
            return {'id_': row['I_id'],
                    'text': row['I_text']}
        else:
            return False

    def get_descendants(self):
        descendants = []

        def recurse(item):
            children = items[item].get_children()
            descendants.extend(children)
            for child in children:
                recurse(child)

        recurse(self.item)
        return descendants

    def get_previous(self):
        qconn = databases.dbs[self.filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_previous, (self.id_, ))
        databases.dbs[self.filename].connection.give(qconn)
        pid = cursor.fetchone()
        if pid['I_previous']:
            return self.make_itemid(self.filename, pid['I_previous'])
        else:
            return None

    def get_next(self):
        qconn = databases.dbs[self.filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_next, (self.id_, ))
        databases.dbs[self.filename].connection.give(qconn)
        nid = cursor.fetchone()
        if nid:
            return self.make_itemid(self.filename, nid['I_id'])
        else:
            return False

    def get_parent(self):
        qconn = databases.dbs[self.filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_parent, (self.id_, ))
        databases.dbs[self.filename].connection.give(qconn)
        pid = cursor.fetchone()
        if pid['I_parent']:
            return self.make_itemid(self.filename, pid['I_parent'])
        else:
            return None

    def get_text(self):
        qconn = databases.dbs[self.filename].connection.get()
        cur = qconn.cursor()
        cur.execute(queries.items_select_id_editor, (self.id_, ))
        text = cur.fetchone()['I_text']
        databases.dbs[self.filename].connection.give(qconn)
        return text

    def has_children(self):
        qconn = databases.dbs[self.filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_haschildren, (self.id_, ))
        databases.dbs[self.filename].connection.give(qconn)
        if cursor.fetchone():
            return True
        else:
            return False

    @staticmethod
    def get_last_base_item_id(filename):
        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_children, (None, ))
        databases.dbs[filename].connection.give(qconn)

        ids = set()
        prevs = set()
        for row in cursor:
            ids.add(row['I_id'])
            prevs.add(row['I_previous'])

        last = ids - prevs

        try:
            return last.pop()
        except KeyError:
            return 0

    @staticmethod
    def make_itemid(filename, id_):
        return '_'.join((filename, str(id_)))
