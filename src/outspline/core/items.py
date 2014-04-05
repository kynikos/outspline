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

from outspline.coreaux_api import Event

import databases
import queries
import exceptions

item_insert_event = Event()
item_update_event = Event()
item_delete_event = Event()


class Item(object):
    def __init__(self, database, filename, id_):
        self.database = database
        self.filename = filename
        self.id_ = id_

    @classmethod
    def insert(cls, filename, mode, baseid, group, text='New item',
               description='Insert item'):
        items = databases.dbs[filename].items

        if not baseid:
            parent = 0
            previous = cls._get_last_base_item_id(filename)
            updnext = False
        elif mode == 'child':
            base = items[baseid]
            parent = baseid
            children = base.get_children()
            previous = children[-1].get_id() if children else 0
            updnext = False
        elif mode == 'sibling':
            parentt = items[baseid].get_parent()
            parent = parentt.get_id() if parentt else 0
            previous = items[baseid].get_id()
            updnext = items[baseid].get_next()

        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_insert, (None, parent, previous, text))
        id_ = cursor.lastrowid
        # For the moment it's necessary to pass 'text' for both the redo and
        # undo queries, because it's needed also when a history action removes
        # an item
        cursor.execute(queries.history_insert,
                    (group, id_, 'insert', description,
                    json.dumps((parent, previous, text), separators=(',',':')),
                    None, text, None))

        databases.dbs[filename].connection.give(qconn)

        databases.dbs[filename].items[id_] = cls(database=databases.dbs[
                                        filename], filename=filename, id_=id_)

        item_insert_event.signal(filename=filename, id_=id_, group=group,
                                 description=description)

        if updnext:
            items[updnext.get_id()].update(group, previous=id_,
                                                    description=description)

        return id_

    def update(self, group, parent=None, previous=None, text=None,
                                                    description='Update item'):
        self.update_no_event(group, parent=parent, previous=previous,
                                            text=text, description=description)

        # Note that update_no_event can be called directly, thus not
        # signalling this event
        item_update_event.signal(filename=self.filename, id_=self.id_,
                                parent=parent, previous=previous, text=text,
                                group=group, description=description)

    def update_no_event(self, group, parent=None, previous=None, text=None,
                                                    description='Update item'):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_select_id, (self.id_, ))
        current_values = cursor.fetchone()

        kwparams = {'I_parent': parent,
                    'I_previous': previous,
                    'I_text': text}

        hparams = {}
        hunparams = {}
        set_fields = ''
        qparams = []

        for field in kwparams:
            value = kwparams[field]

            if value is not None:
                hparams[field] = value
                hunparams[field] = current_values[field]
                set_fields += '{}=?, '.format(field)
                qparams.append(value)

        set_fields = set_fields[:-2]
        query = queries.items_update_id.format(set_fields)
        qparams.append(self.id_)
        cursor.execute(query, qparams)

        jhparams = json.dumps(hparams, separators=(',',':'))
        jhunparams = json.dumps(hunparams, separators=(',',':'))
        cursor.execute(queries.history_insert, (group, self.id_, 'update',
                                                description, jhparams, None,
                                                jhunparams, None))

        self.database.connection.give(qconn)

    def delete(self, group, description='Delete item'):
        prev = self.get_previous()
        next = self.get_next()

        if next:
            if prev:
                previd = prev.get_id()
            else:
                previd = 0
            next.update(group, previous=previd, description=description)

        qconn = self.database.connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_select_id, (self.id_, ))
        current_values = cursor.fetchone()

        # For the moment it's necessary to pass current_values['I_text'] for
        # both the redo and undo queries, because it's needed also when a
        # history action removes an item
        query_redo = current_values['I_text']
        query_undo = json.dumps((current_values['I_parent'],
                    current_values['I_previous'], current_values['I_text']),
                    separators=(',',':'))



        cursor.execute(queries.items_delete_id, (self.id_, ))
        cursor.execute(queries.history_insert, (group, self.id_, 'delete',
                            description, query_redo, None, query_undo, None))

        self.database.connection.give(qconn)

        self.remove()

        # This event is designed to be signalled _after_ self.remove()
        item_delete_event.signal(filename=self.filename, id_=self.id_,
                         hid=cursor.lastrowid, text=current_values['I_text'],
                         group=group, description=description)

    def remove(self):
        del self.database.items[self.id_]

    def shift(self, mode, group, description='Shift item'):
        items = self.database.items
        filename = self.filename
        id_ = self.id_
        if mode == 'up':
            prev = self.get_previous()
            if prev:
                previd = prev.get_id()
                prev2 = prev.get_previous()
                prev2id = prev2.get_id() if prev2 else 0
                next_ = self.get_next()
                # Keep all items[id_].get_{next,previous,...} _before_ updates!
                self.update(group, previous=prev2id, description=description)
                prev.update(group, previous=id_, description=description)
                if next_:
                    next_.update(group, previous=previd,
                                                    description=description)
            else:
                raise exceptions.CannotMoveItemError()
        elif mode == 'down':
            next_ = self.get_next()
            if next_:
                nextid = next_.get_id()
                prev = self.get_previous()
                previd = prev.get_id() if prev else 0
                next2 = next_.get_next()
                # Keep all items[id_].get_{next,previous,...} _before_ updates!
                self.update(group, previous=nextid, description=description)
                next_.update(group, previous=previd, description=description)
                if next2:
                    next2.update(group, previous=id_, description=description)
            else:
                raise exceptions.CannotMoveItemError()
        elif mode == 'parent':
            parent = self.get_parent()
            if parent:
                parent2 = parent.get_parent()
                if parent2:
                    parent2id = parent2.get_id()
                    lastchild = parent2.get_children()[-1]
                    lastchildid = lastchild.get_id()
                else:
                    parent2id = 0
                    lastchildid = self._get_last_base_item_id(filename)
                next_ = self.get_next()
                if next_:
                    prev = self.get_previous()
                    previd = prev.get_id() if prev else 0
                # Keep all items[id_].get_{next,previous,...} _before_ updates!
                self.update(group, parent=parent2id, previous=lastchildid,
                            description=description)
                if next_:
                    next_.update(group, previous=previd,
                                                    description=description)
            else:
                raise exceptions.CannotMoveItemError()

        return True

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    def get_children(self):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_children, (self.id_, ))
        self.database.connection.give(qconn)

        dd = {}
        for row in cursor:
            dd[row['I_previous']] = row['I_id']

        children = []
        prev = 0
        while prev in dd:
            children.append(self.database.items[dd[prev]])
            prev = dd[prev]

        return children

    def get_all_info(self):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id, (self.id_, ))
        self.database.connection.give(qconn)
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

    def get_ancestors(self, ancestors=[]):
        parent = self.get_parent()

        if parent:
            ancestors.append(parent)
            ancestors = parent.get_ancestors(ancestors)

        return ancestors

    def get_descendants(self):
        items = self.database.items
        descendants = []

        def recurse(id_):
            children = items[id_].get_children()
            descendants.extend(children)
            for child in children:
                recurse(child)

        recurse(self.id_)
        return descendants

    def get_previous(self):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_previous, (self.id_, ))
        self.database.connection.give(qconn)
        pid = cursor.fetchone()
        if pid['I_previous'] != 0:
            return self.database.items[pid['I_previous']]
        else:
            return None

    def get_next(self):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_next, (self.id_, ))
        self.database.connection.give(qconn)
        nid = cursor.fetchone()
        if nid:
            return self.database.items[nid['I_id']]
        else:
            return None

    def get_parent(self):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_parent, (self.id_, ))
        self.database.connection.give(qconn)
        pid = cursor.fetchone()
        if pid['I_parent']:
            return self.database.items[pid['I_parent']]
        else:
            return None

    def get_text(self):
        qconn = self.database.connection.get()
        cur = qconn.cursor()
        cur.execute(queries.items_select_id_editor, (self.id_, ))
        text = cur.fetchone()['I_text']
        self.database.connection.give(qconn)
        return text

    def has_children(self):
        qconn = self.database.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_haschildren, (self.id_, ))
        self.database.connection.give(qconn)
        if cursor.fetchone():
            return True
        else:
            return False

    @staticmethod
    def _get_last_base_item_id(filename):
        qconn =  databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_children, (0, ))
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
