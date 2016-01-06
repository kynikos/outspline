# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import os
import errno
import Queue as queue
import sqlite3

import outspline.info
import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import Event, log
import outspline.dbdeps as dbdeps

import exceptions
import items
import queries
import history

protection = None
memory = None

blocked_databases_event = Event()
open_database_dirty_event = Event()
open_database_event = Event()
closing_database_event = Event()
close_database_event = Event()
save_permission_check_event = Event()
save_database_event = Event()
delete_subtree_event = Event()
exit_app_event_1 = Event()
exit_app_event_2 = Event()

dbs = {}


class Protection(object):
    # Avoid that an operation is started while the timer is doing something
    # In theory it could happen that, because the database connection is
    #   taken and released with .get() and .give() various times during an
    #   operation, if the timer does something in the meanwhile it could
    #   "steal" the connection to the ongoing operation, with unknown results
    # Make sure that all the commands that can be started either directly by
    #   the user (through interaction with interfaces and their plugins) or
    #   automatically (e.g. by a timer) are protected
    # Also be sure to protect the functions from start to end; for example
    #   it would be wrong, in a loop, to protect every iteration but leave out
    #   the for itself; this way, in fact, another function that was waiting
    #   for a .get() could steal the connection between a loop and the other
    # Pay attention to functions that have returns, because they could bypass
    #   the .release() and hang the program
    # Another advantage is that if an exception is raised, the program hangs
    #   at the following command issued, instead of possibly continuing
    #     operating
    # Another advantage is that this class makes sure that when a function sets
    #     the history group, it's impossible that another function manages to
    #     set the same group
    def __init__(self):
        baton = True
        self.q = queue.Queue()
        self.q.put(baton)

    def block(self, block=False, quiet=False):
        try:
            self.s = self.q.get(block)
        except queue.Empty:
            if not quiet:
                blocked_databases_event.signal()

            return False
        else:
            log.debug('Block databases')
            return True

    def release(self):
        log.debug('Release databases')

        self.q.task_done()
        self.q.join()
        self.q.put(self.s)


class DBQueue(queue.Queue):
    def give(self, item):
        self.task_done()
        self.join()
        self.put(item)
        return True


class MemoryDB(DBQueue):
    def __init__(self):
        DBQueue.__init__(self)

        # Enable multi-threading, as the database is protected with a queue
        self.put(sqlite3.connect(':memory:', check_same_thread=False))

        qmemory = self.get()
        qmemory.row_factory = sqlite3.Row
        self.give(qmemory)

    def exit_(self):
        exit_app_event_1.signal()

        qmemory = self.get()
        qmemory.close()
        self.task_done()
        self.join()

        exit_app_event_2.signal()


class FileDB(object):
    def __init__(self, filename, check_same_thread=False, name_based=False):
        self.connection = sqlite3.connect(filename,
                                        check_same_thread=check_same_thread)

        if name_based:
            self.connection.row_factory = sqlite3.Row

        cursor = self.connection.cursor()

        # No exception will be raised by sqlite3.connect if the file isn't a
        #  database, a query must be attempted
        try:
            cursor.execute(queries.pragma_valid_test)
        except sqlite3.DatabaseError:
            self.disconnect()
            raise exceptions.DatabaseNotValidError()

        # If == 0 it means the database is new (just been created)
        if cursor.fetchone()[0] > 0:
            try:
                # In order to test if the database is locked (open by another
                # instance of Outspline), a SELECT query is not enough
                cursor.execute(queries.properties_insert_dummy)
            except sqlite3.OperationalError:
                self.disconnect()
                raise exceptions.DatabaseLockedError()
            else:
                cursor.execute(queries.properties_delete_dummy)

    def cursor(self):
        return self.connection.cursor()

    def save(self):
        self.connection.commit()

    def disconnect(self):
        self.connection.close()

    def save_and_disconnect(self):
        self.save()
        self.disconnect()


class Database(object):
    def __init__(self, filename):
        self.connection = DBQueue()
        self.filename = filename
        self.items = {}
        self.dbhistory = history.DBHistory(self.connection, self.items,
                                                                self.filename)

        # Enable multi-threading, as the database is protected with a queue
        self.connection.put(FileDB(filename, check_same_thread=False,
                                                            name_based=True))
        qconn = self.connection.get()
        cursor = qconn.cursor()

        cursor.execute(queries.properties_select_history)
        softlimit = cursor.fetchone()[0]
        config = coreaux_api.get_configuration()('History')
        timelimit = config.get_int('time_limit')
        hardlimit = config.get_int('hard_limit')
        self.dbhistory.set_limits(softlimit, timelimit, hardlimit)

        dbitems = cursor.execute(queries.items_select_tree)
        self.connection.give(qconn)

        for item in dbitems:
            self.items[item['I_id']] = items.Item(self.connection,
                    self.dbhistory, self.items, self.filename, item['I_id'])

    @staticmethod
    def create(filename):
        if filename in dbs:
            raise exceptions.DatabaseAlreadyOpenError()
        else:
            try:
                db = open(filename, 'w')
            except IOError as e:
                if e.errno in (errno.EACCES, errno.ENOENT):
                    # errno.ENOENT happens when trying to to do a save as in
                    # a non-authorized folder
                    raise exceptions.AccessDeniedError()
                raise
            else:
                db.close()

                conn = FileDB(filename)
                cursor = conn.cursor()

                cursor.execute(queries.properties_create)

                limit = coreaux_api.get_configuration()('History').get_int(
                                                        'default_soft_limit')
                cursor.execute(queries.properties_insert_init, (limit, ))

                cursor.execute(queries.compatibility_create)
                # Only store major versions, as they are supposed to keep
                # backward compatibility
                # None must be used for core, because it must be safe in case
                # an extension is called 'core' for some reason
                cursor.execute(queries.compatibility_insert, (None,
                                    int(float(outspline.info.core.version)), ))

                cursor.execute(queries.items_create)
                cursor.execute(queries.history_create)

                conn.save_and_disconnect()

                extensions = coreaux_api.get_enabled_installed_addons()[
                                                                'Extensions']
                dbdeps.Database(filename).add([ext for ext in extensions
                                    if coreaux_api.import_extension_info(ext
                                    ).affects_database])

                return filename

    @classmethod
    def open(cls, filename, check_new_extensions=True):
        global dbs
        if filename in dbs:
            raise exceptions.DatabaseAlreadyOpenError()
        elif not os.access(filename, os.W_OK):
            raise exceptions.DatabaseNotAccessibleError()
        else:
            can_open, dependencies = dbdeps.Database(filename).is_compatible(
                                                        check_new_extensions)

            if can_open:
                dbs[filename] = cls(filename)

                open_database_dirty_event.signal(filename=filename,
                                                    dependencies=dependencies)

                # Reset modified state after instantiating the class, since
                # this signals an event whose handlers might require the object
                # to be already created
                dbs[filename].dbhistory.reset_modified_state()

                open_database_event.signal(filename=filename)
                return True

    def save(self):
        # Some addons may use this event to generate an exception
        save_permission_check_event.signal(filename=self.filename)

        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.history_update_status_new)
        cursor.execute(queries.history_update_status_old)
        qconn.save()
        self.connection.give(qconn)

        self.dbhistory.reset_modified_state()

        save_database_event.signal(filename=self.filename)

    def save_copy(self, destination):
        # Some addons may use this event to generate an exception
        # For consistency, signal 'self.filename' and not 'destination'
        save_permission_check_event.signal(filename=self.filename)

        # Of course the original file cannot be simply copied, in fact in that
        # case it should be saved first, and that's not what is expected

        qconn = self.connection.get()
        qconnd = FileDB(destination)
        cursor = qconn.cursor()
        cursord = qconnd.cursor()

        cursor.execute(queries.master_select_tables)

        for row in cursor:
            tname = row["name"]

            # Some tables are initialized by self.create
            cursord.execute(queries.master_delete.format(tname))

            tcursor = qconn.cursor()
            tcursor.execute(queries.master_select_table.format(tname))

            for trow in tcursor:
                cursord.execute(queries.master_insert.format(tname,
                                    ", ".join(trow.keys()),
                                    ", ".join(["?", ] * len(trow))), (trow))

        cursord.execute(queries.history_update_status_new)
        cursord.execute(queries.history_update_status_old)

        self.connection.give(qconn)

        qconnd.save_and_disconnect()

    def close(self):
        closing_database_event.signal(filename=self.filename)

        global dbs
        del dbs[self.filename]

        qconn = self.connection.get()
        qconn.disconnect()
        self.connection.task_done()
        self.connection.join()

        close_database_event.signal(filename=self.filename)

        # Note that if the database has not been closed correctly, the history
        # is not cleaned
        self.dbhistory.clean_history()

        return True

    def delete_subtree(self, id_, group, description='Delete subtree'):
        self.items[id_].delete_subtree(group, description=description)
        delete_subtree_event.signal()

    def find_independent_items(self, ids):
        roots = set(ids)

        for id_ in ids:
            roots -= set(self.items[id_].get_children())

        return roots

    def get_root_items(self):
        return items.Item.get_children_sorted(self.filename, 0)

    def get_all_items(self):
        qconn = self.connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_search)
        self.connection.give(qconn)
        return cursor

    def get_all_items_text(self):
        return self.get_all_items().fetchall()

    def add_ignored_dependency(self, extension):
        qconn = self.connection.get()
        cur = qconn.cursor()
        cur.execute(queries.compatibility_insert_ignored, (extension, ))
        self.connection.give(qconn)

        self.dbhistory.set_modified()

    def remove_ignored_dependency(self, extension):
        qconn = self.connection.get()
        cur = qconn.cursor()
        cur.execute(queries.compatibility_delete, (extension, ))
        self.connection.give(qconn)

        self.dbhistory.set_modified()
