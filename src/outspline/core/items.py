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
item_update_previous_event = Event()
item_update_parent_event = Event()
item_update_text_event = Event()
item_deleting_event = Event()
item_deleted_event = Event()
item_deleted_2_event = Event()


class Item(object):
    def __init__(self, connection, dbhistory, items, filename, id_):
        self.connection = connection
        self.dbhistory = dbhistory
        self.items = items
        self.filename = filename
        self.id_ = id_

    @classmethod
    def insert(cls, filename, parent, previous, group, text='New item',
                                                    description='Insert item'):
        items = databases.dbs[filename].items

        # Set updnext *before* inserting the new item in the database
        try:
            updnext = items[previous]._get_next()
        except KeyError:
            # previous may be 0
            updnext = False

        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_insert, (None, parent, previous, text))
        id_ = cursor.lastrowid

        databases.dbs[filename].connection.give(qconn)

        # For the moment it's necessary to pass 'text' for both the redo and
        # undo queries, because it's needed also when a history action removes
        # an item
        databases.dbs[filename].dbhistory.insert_history(group, id_, 'insert',
                    description,
                    json.dumps((parent, previous, text), separators=(',',':')),
                    json.dumps((parent, text), separators=(',',':')))

        db = databases.dbs[filename]
        databases.dbs[filename].items[id_] = cls(db.connection, db.dbhistory,
                                                    db.items, filename, id_)

        if updnext:
            items[updnext.get_id()].update_previous(id_, group,
                                                    description=description)

        # Signal the even *after* updating the next item
        item_insert_event.signal(filename=filename, id_=id_, parent=parent,
                            text=text, group=group,  description=description)

        return id_

    def update_previous(self, previous, group, description='Update item'):
        self._update(group, previous=previous, description=description)

        item_update_previous_event.signal(filename=self.filename, id_=self.id_,
                    previous=previous, group=group, description=description)

    def update_parent(self, parent, previous, group,
                                                    description='Update item'):
        self._update(group, parent=parent, previous=previous,
                                                    description=description)

        item_update_parent_event.signal(filename=self.filename, id_=self.id_,
                                        parent=parent, previous=previous,
                                        group=group, description=description)

    def update_text(self, text, group, event=True, description='Update item'):
        qconn = self.connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_select_id_editor, (self.id_, ))
        oldtext = cursor.fetchone()["I_text"]
        cursor.execute(queries.items_update_text, (text, self.id_))
        self.connection.give(qconn)

        self.dbhistory.insert_history(group, self.id_, 'update_text',
                                                    description, text, oldtext)

        if event:
            item_update_text_event.signal(filename=self.filename, id_=self.id_,
                            text=text, group=group, description=description)

    def _update(self, group, parent=None, previous=None, text=None,
                                                    description='Update item'):
        # Split in the above methods ****************************************************
        qconn = self.connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_select_id, (self.id_, ))
        current_values = cursor.fetchone()

        kwparams = {'I_parent': parent,
                    'I_previous': previous,
                    'I_text': text}

        # The interface requires the old parent when undoing/redoing an item
        # update
        if parent is not None:
            hparams = ({}, current_values["I_parent"])
            hunparams = ({}, parent)
        elif previous is not None:
            hparams = ({}, current_values["I_parent"])
            hunparams = ({}, current_values["I_parent"])
        else:
            hparams = ({}, None)
            hunparams = ({}, None)

        set_fields = ''
        qparams = []

        for field in kwparams:
            value = kwparams[field]

            if value is not None:
                hparams[0][field] = value
                hunparams[0][field] = current_values[field]
                set_fields += '{}=?, '.format(field)
                qparams.append(value)

        set_fields = set_fields[:-2]
        query = queries.items_update_id.format(set_fields)
        qparams.append(self.id_)
        cursor.execute(query, qparams)
        self.connection.give(qconn)

        jhparams = json.dumps(hparams, separators=(',',':'))
        jhunparams = json.dumps(hunparams, separators=(',',':'))
        self.dbhistory.insert_history(group, self.id_, 'update',
                                            description, jhparams, jhunparams)

    def delete_subtree(self, group, description='Delete subtree'):
        for child in self._get_children_unsorted():
            child.delete_subtree(group, description)

        qconn = self.connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.items_select_id, (self.id_, ))
        res = cursor.fetchone()
        parent = res['I_parent']
        previous = res['I_previous']
        text = res['I_text']

        self.connection.give(qconn)

        # This event must be signalled *before* updating the next item
        item_deleting_event.signal(filename=self.filename, parent=parent,
                                                                id_=self.id_)

        next = self._get_next()

        if next:
            next.update_previous(previous, group, description=description)

        qconn = self.connection.get()
        cursor = qconn.cursor()

        # For the moment it's necessary to pass res['I_text'] for both the redo
        # and undo queries, because it's needed also when a history action
        # removes an item
        hparams = json.dumps((parent, text), separators=(',',':'))
        hunparams = json.dumps((parent, previous, text), separators=(',',':'))

        cursor.execute(queries.items_delete_id, (self.id_, ))

        self.connection.give(qconn)

        self.dbhistory.insert_history(group, self.id_, 'delete',
                                            description, hparams, hunparams)

        self.remove()

        # This event is designed to be signalled _after_ self.remove()
        item_deleted_event.signal(filename=self.filename, id_=self.id_,
                                         hid=cursor.lastrowid, text=text,
                                         group=group, description=description)

        item_deleted_2_event.signal(filename=self.filename, id_=self.id_)

    def remove(self):
        del self.items[self.id_]

    def shift_up(self, group, description='Shift item up'):
        items = self.items
        filename = self.filename
        id_ = self.id_
        prev = self._get_previous()

        if prev:
            previd = prev.get_id()
            prev2 = prev._get_previous()
            prev2id = prev2.get_id() if prev2 else 0
            next_ = self._get_next()
            # Keep all items[id_].get_{next,previous,...} _before_ updates!
            self.update_previous(prev2id, group, description=description)
            prev.update_previous(id_, group, description=description)

            if next_:
                next_.update_previous(previd, group, description=description)
        else:
            raise exceptions.CannotMoveItemError()

        return True

    def shift_down(self, group, description='Shift item down'):
        items = self.items
        filename = self.filename
        id_ = self.id_
        next_ = self._get_next()

        if next_:
            nextid = next_.get_id()
            prev = self._get_previous()
            previd = prev.get_id() if prev else 0
            next2 = next_._get_next()
            # Keep all items[id_].get_{next,previous,...} _before_ updates!
            self.update_previous(nextid, group, description=description)
            next_.update_previous(previd, group, description=description)

            if next2:
                next2.update_previous(id_, group, description=description)
        else:
            raise exceptions.CannotMoveItemError()

        return True

    def move_to_parent(self, group, description='Move item to parent'):
        items = self.items
        filename = self.filename
        id_ = self.id_
        parent = self._get_parent()

        if parent:
            parent2 = parent._get_parent()

            if parent2:
                parent2id = parent2.get_id()
                lastchild = parent2._get_children()[-1]
                lastchildid = lastchild.get_id()
            else:
                parent2id = 0
                lastchildid = self.get_last_child(filename, 0)

            next_ = self._get_next()

            if next_:
                prev = self._get_previous()
                previd = prev.get_id() if prev else 0

            # Keep all items[id_].get_{next,previous,...} _before_ updates!
            self.update_parent(parent2id, lastchildid, group,
                                                    description=description)

            if next_:
                next_.update_previous(previd, group, description=description)
        else:
            raise exceptions.CannotMoveItemError()

        return True

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    def _get_children(self):
        return [self.items[id_] for id_ in self.get_children()]

    def _get_children_unsorted(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_children, (self.id_, ))
        self.connection.give(qconn)
        return [self.items[row["I_id"]] for row in cursor]

    def get_children(self):
        return self.get_children_sorted(self.filename, self.id_)

    def get_all_info(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id, (self.id_, ))
        self.connection.give(qconn)
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
        cursor.execute(queries.items_select_parent_text, (parentid, previd))
        databases.dbs[filename].connection.give(qconn)
        row = cursor.fetchone()

        if row:
            return {'id_': row['I_id'],
                    'text': row['I_text']}
        else:
            return False

    def get_ancestors(self):
        ancestors = []
        parent = self._get_parent()

        if parent:
            ancestors.append(parent.get_id())
            ancestors.extend(parent.get_ancestors())

        return ancestors

    def get_descendants(self):
        descendants = []

        for child in self._get_children_unsorted():
            descendants.append(child.get_id())
            descendants.extend(child.get_descendants())

        return descendants

    def _get_previous(self):
        try:
            return self.items[self.get_previous()]
        except KeyError:
            return None

    def get_previous(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_previous, (self.id_, ))
        self.connection.give(qconn)
        return cursor.fetchone()['I_previous']

    def _get_next(self):
        try:
            return self.items[self.get_next()]
        except KeyError:
            return None

    def get_next(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_next, (self.id_, ))
        self.connection.give(qconn)
        nid = cursor.fetchone()

        if nid:
            return nid['I_id']
        else:
            return None

    def _get_parent(self):
        pid = self.get_parent()

        try:
            return self.items[pid]
        except KeyError:
            return None

    def get_parent(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_parent, (self.id_, ))
        self.connection.give(qconn)
        pid = cursor.fetchone()
        return pid['I_parent']

    def get_text(self):
        qconn = self.connection.get()
        cur = qconn.cursor()
        cur.execute(queries.items_select_id_editor, (self.id_, ))
        text = cur.fetchone()['I_text']
        self.connection.give(qconn)
        return text

    def has_children(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_haschildren, (self.id_, ))
        self.connection.give(qconn)

        if cursor.fetchone():
            return True
        else:
            return False

    def is_root(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_parent, (self.id_, ))
        self.connection.give(qconn)

        if cursor.fetchone()["I_parent"] == 0:
            return True
        else:
            return False

    @classmethod
    def get_last_child(cls, filename, id_):
        ids = cls.get_children_sorted(filename, id_)

        try:
            return ids[-1]
        except IndexError:
            return 0

    @staticmethod
    def get_children_sorted(filename, parent):
        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_parent, (parent, 0))
        row = cursor.fetchone()
        ids = []

        if row:
            ids.append(row["I_id"])

            while True:
                cursor.execute(queries.items_select_id_next, (ids[-1], ))
                row = cursor.fetchone()

                if row:
                    ids.append(row["I_id"])
                else:
                    break

        databases.dbs[filename].connection.give(qconn)
        return ids
