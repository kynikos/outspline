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

import sqlite3 as _sql

from outspline.coreaux_api import Event

import queries
import items

check_pending_changes_event = Event()
reset_modified_state_event = Event()
history_event = Event()
history_insert_event = Event()
history_update_event = Event()
history_delete_event = Event()
history_other_event = Event()
history_clean_event = Event()


class DBHistory(object):
    def __init__(self, filename, connection, items):
        self.filename = filename
        self.connection = connection
        self.items = items

        self.hactions = {
            'insert': {
                'undo': self._do_history_row_delete,
                'redo': self._do_history_row_insert,
            },
            'update': {
                'undo': self._do_history_row_update,
                'redo': self._do_history_row_update,
            },
            'delete': {
                'undo': self._do_history_row_insert,
                'redo': self._do_history_row_delete,
            },
            None: {
                'undo': self._do_history_row_other,
                'redo': self._do_history_row_other,
            },
        }

    def insert_history(self, group, id_, type_, description, query_redo,
                                            text_redo, query_undo, text_undo):
        qconn = self.connection.get()
        cur = qconn.cursor()
        cur.execute(queries.history_insert, (group, id_, type_, description,
                                query_redo, text_redo, query_undo, text_undo))
        self.connection.give(qconn)

        return cur.lastrowid

    def get_next_history_group(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.history_delete_status)
        cursor.execute(queries.history_select_status_next)
        self.connection.give(qconn)

        row = cursor.fetchone()
        if row['H_group']:
            group = row['H_group'] + 1
        else:
            group = 1
        return group

    def get_history_descriptions(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.history_select_description)
        self.connection.give(qconn)

        # Putting the results in a dictionary loses record order

        return cursor

    def _update_history_id(self, id_, status):
        if status == 0:
            newstatus = 1
        elif status == 1:
            newstatus = 0
        elif status == 2:
            newstatus = 3
        elif status == 3:
            newstatus = 2
        elif status == 4:
            newstatus = 5
        elif status == 5:
            newstatus = 4
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.history_update_id, (newstatus, id_))
        self.connection.give(qconn)

    def check_pending_changes(self):
        check_pending_changes_event.signal(filename=self.filename)

        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.history_select_status)
        self.connection.give(qconn)

        row = cursor.fetchone()
        if row or self.modified:
            return True
        else:
            return False

    def set_modified(self):
        self.modified = True

    def reset_modified_state(self):
        self.modified = False

        reset_modified_state_event.signal(filename=self.filename)

    def read_history_undo(self):
        return self._read_history(queries.history_select_status_undo,
                                            queries.history_select_group_undo)

    def read_history_redo(self):
        return self._read_history(queries.history_select_status_redo,
                                            queries.history_select_group_redo)

    def _read_history(self, history_select_status_query,
                                                history_select_group_query):
        # SavedStatus  CurrentStatus  Status
        # 0 unsaved    0 undone       0 unsaved and undone
        # 0 unsaved    1 done         1 unsaved and done
        # 2 undone     0 undone       2 saved as undone
        # 2 undone     1 done         3 saved as undone but pending as done
        # 4 done       0 undone       4 saved as done but pending as undone
        # 4 done       1 done         5 saved as done

        # Possible scenarios:
        # 5
        # 5 4
        # 5 4 2
        # 5 4 2 0
        # 5 4 0
        # 5 3
        # 5 3 2
        # 5 3 2 0
        # 5 3 1
        # 5 3 1 0
        # 5 3 0
        # 5 2
        # 5 2 0
        # 5 1
        # 5 1 0
        # 5 0
        # 4
        # 4 2
        # 4 2 0
        # 4 0
        # 3
        # 3 2
        # 3 2 0
        # 3 1
        # 3 1 0
        # 3 0
        # 2
        # 2 0
        # 1
        # 1 0
        # 0

        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(history_select_status_query)
        self.connection.give(qconn)
        lastgroup = cursor.fetchone()

        if lastgroup:
            qconn = self.connection.get()
            cursorm = qconn.cursor()
            # Create a list, because it has to be looped twice
            history = tuple(cursorm.execute(history_select_group_query,
                                                    (lastgroup['H_group'], )))
            self.connection.give(qconn)
            return {'history': history,
                    'status': lastgroup['H_status']}
        else:
            return False

    def undo_history(self):
        self._do_history(self.read_history_undo(), 'undo')

    def redo_history(self):
        self._do_history(self.read_history_redo(), 'redo')

    def _do_history(self, read, action):
        if read:
            history = read['history']
            status = read['status']

            for row in history:
                self._do_history_row(action, row[3], row[4], row['H_id'],
                                                row['H_type'], row['H_item'])
                self._update_history_id(row['H_id'], status)
            history_event.signal(filename=self.filename)

    def _do_history_row(self, action, query, text, hid, type_, itemid):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        # Update queries can or cannot have I_text=?, hence they accept or
        # don't accept a query binding
        try:
            cursor.execute(query)
        except _sql.ProgrammingError:
            cursor.execute(query, (text, ))
        self.connection.give(qconn)

        try:
            haction = self.hactions[type_]
        except KeyError:
            haction = self.hactions[None]

        haction[action](type_, action, itemid, hid, text)

    def _do_history_row_insert(self, type_, action, itemid, hid, text):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id, (itemid, ))
        select = cursor.fetchone()
        self.connection.give(qconn)

        self.items[itemid] = items.Item(database=self, filename=self.filename,
                                                                    id_=itemid)

        history_insert_event.signal(filename=self.filename, id_=itemid,
                                                parent=select['I_parent'],
                                                previous=select['I_previous'],
                                                text=select['I_text'], hid=hid)

    def _do_history_row_update(self, type_, action, itemid, hid, text):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id, (itemid, ))
        select = cursor.fetchone()
        self.connection.give(qconn)

        history_update_event.signal(filename=self.filename, id_=itemid,
                                                parent=select['I_parent'],
                                                previous=select['I_previous'],
                                                text=select['I_text'])

    def _do_history_row_delete(self, type_, action, itemid, hid, text):
        self.items[itemid].remove()
        history_delete_event.signal(filename=self.filename, id_=itemid, hid=hid,
                                                                text=text)

    def _do_history_row_other(self, type_, action, itemid, hid, text):
        history_other_event.signal(type_=type_, action=action,
                                filename=self.filename, id_=itemid, hid=hid)

    def clean_history(self):
        # This operation must be performed on a different connection than
        # the main one (which at this point has been closed already anyway)
        qconn = _sql.connect(self.filename)
        cursor = qconn.cursor()

        cursor.execute(queries.properties_select_history)
        hlimit = cursor.fetchone()[0]

        cursor.execute(queries.history_select_select, (hlimit, ))
        t = tuple(cursor)

        # history_clean_event handlers will need a proper connection
        qconn.close()

        history_clean_event.signal(filename=self.filename, hids=t)

        qconn = _sql.connect(self.filename)
        cursor = qconn.cursor()

        for row in t:
            cursor.execute(queries.history_delete_id, (row[0], ))

        cursor.execute(queries.history_update_group)

        qconn.commit()
        qconn.close()
