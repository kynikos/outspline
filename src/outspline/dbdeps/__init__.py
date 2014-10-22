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

import sqlite3 as sql
import importlib

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import OutsplineError
from outspline.core import queries


class Core(object):
    # Keep core upgrade functions here, not in a module like for the
    #  extensions, because giving core a dedicated module would "pollute" the
    #  dbdeps folder with a module that doesn't represent an extension,
    #  requiring a name (e.g. "_core.py") that in the future may conflict with
    #  a new real extension

    # Core can't be added nor removed

    @staticmethod
    def upgrade_0_to_1(cursor):
        # These queries must stay here because they must not be updated with
        # the normal queries
        cursor.execute('DROP TABLE History')
        cursor.execute("CREATE TABLE History (H_id INTEGER PRIMARY KEY, "
                                                "H_group INTEGER, "
                                                "H_status INTEGER, "
                                                "H_item INTEGER, "
                                                "H_type TEXT, "
                                                "H_tstamp INTEGER, "
                                                "H_description TEXT, "
                                                "H_redo TEXT, "
                                                "H_undo TEXT)")

    @staticmethod
    def upgrade_1_to_2(cursor):
        # These queries must stay here because they must not be updated with
        # the normal queries
        pass


class Database(object):
    def __init__(self, filename):
        self.filename = filename

        try:
            connection = sql.connect(filename)
            cursor = connection.cursor()

            # I have to import here, or a circular import will happen
            import outspline.core_api as core_api
            cursor.execute(queries.compatibility_select)
        except sql.DatabaseError:
            connection.close()
            raise DatabaseNotValidError()

        # ABORT - If a dependency is not installed
        # ABORT - If a dependency is installed with a lesser version number
        # OK - If a dependency is installed with the correct version number
        # IGNORE - If a dependency is disabled and set to be ignored in the
        #          CoMpatibility table
        # UPDATE - If a dependency is installed with a greater version number
        # ADD - If an extension is not present in the dependencies

        info = coreaux_api.get_addons_info(disabled=False)

        self.dependencies = {
            'ignore': {},
            'add': {},
            'update': {},
            'abort': {},
        }
        self.fdeps = []

        # Only compare major versions, as they are supposed to keep backward
        # compatibility
        # Core must be stored as None in the database to avoid clashes with a
        # possible extension called 'core'
        self.dependencies['add'][None] = [int(float(
                                        coreaux_api.get_core_version())), None]

        extensions = info('Extensions')

        for ext in extensions.get_sections():
            if extensions(ext).get_bool('affects_database'):
                # Core will never end up staying in the 'add' key, however
                # initialize it here so that it can be moved like the
                # extensions
                # Only compare major versions, as they are supposed to keep
                # backward compatibility
                self.dependencies['add'][ext] = [int(extensions(ext).get_float(
                                                            'version')), None]

        for row in cursor:
            # 'row[2] == None' means that the addon is not a dependency, but if
            #   installed it shouldn't trigger a reminder to enable it
            # Don't just test `if row[2]:` because '0' should not pass
            try:
                dep = self.dependencies['add'][row[1]]
            except KeyError:
                if row[2] is None:
                    pass
                else:
                    self.dependencies['abort'][row[1]] = [None, row[2]]
            else:
                if row[2] is None:
                    self.dependencies['ignore'][row[1]] = dep[:]
                else:
                    dep[1] = row[2]

                    if row[2] > dep[0]:
                        self.dependencies['abort'][row[1]] = dep[:]
                    elif row[2] < dep[0]:
                        self.dependencies['update'][row[1]] = dep[:]
                    else:
                        version = str(row[2])

                        if row[1] is None:
                            self.fdeps.append('.'.join(('core', version)))
                        else:
                            self.fdeps.append('.'.join(('extensions', row[1],
                                                                    version)))

                del self.dependencies['add'][row[1]]

        connection.close()

    def is_compatible(self, check_new_extensions):
        if len(self.dependencies['abort']) > 0:
            raise DatabaseIncompatibleAbortError(self)
        elif len(self.dependencies['update']) > 0:
            raise DatabaseIncompatibleUpdateError(self)
        elif check_new_extensions and len(self.dependencies['add']) > 0:
            raise DatabaseIncompatibleAddError(self)

        return (True, self.fdeps)

    def get_filename(self):
        return self.filename

    def get_addible_dependencies(self):
        return self.dependencies['add']

    def get_updatable_dependencies(self):
        return self.dependencies['update']

    def get_aborting_dependencies(self):
        return self.dependencies['abort']

    def _sort_extensions(self, inexts):
        extinfo = coreaux_api.get_addons_info(disabled=False)('Extensions')
        inexts = list(inexts)
        outexts = []

        def recurse(ext):
            # ext comes as unicode from the database
            sext = str(ext)

            try:
                deps = extinfo(sext)['dependencies'].split(" ")
            except KeyError:
                deps = []

            try:
                opts = extinfo(sext)['optional_dependencies'].split(" ")
            except KeyError:
                opts = []

            for dep in deps + opts:
                dsplit = dep.split('.')

                if dsplit[0] == 'extensions':
                    if dsplit[1] in inexts:
                        recurse(dsplit[1])

            inexts.remove(ext)
            outexts.append(sext)

        if None in inexts:
            # Always put core (None) first, if present
            inexts.remove(None)
            outexts.append(None)

        while True:
            try:
                ext = inexts[0]
            except IndexError:
                break
            else:
                recurse(ext)

        return outexts

    def _execute(self, extensions, action, **kwargs):
        connection = sql.connect(self.filename)
        connection.row_factory = sql.Row
        cursor = connection.cursor()

        for ext in self._sort_extensions(extensions):
            if ext is None:
                # Yeah, Core is a static class, not a module like for the
                #  extensions, but giving core a dedicated module would
                #  "pollute" the dbdeps folder with a module that doesn't
                #  represent an extension, requiring a name (e.g. "_core.py")
                #  that in the future may conflict with a new real extension
                module = Core
            else:
                module = importlib.import_module('outspline.dbdeps.' + ext)

            action(module, ext, cursor, **kwargs)

        # Always purge the history because not only when removing, but also
        # when adding dependencies some old entries should be accompanied by
        # queries to the new tables, and trying to predict all this would be
        # too dangerous
        cursor.execute(queries.history_delete_purge)

        connection.commit()
        connection.close()

    def add(self, extensions):
        self._execute(extensions, self._add)

    def _add(self, module, ext, cursor):
        deps = self.dependencies['add'].copy()
        deps.update(self.dependencies['ignore'])
        # Only store major versions, as they are supposed to
        # keep backward compatibility
        try:
            ver = self.dependencies['add'][ext][0]
        except KeyError:
            ver = self.dependencies['ignore'][ext][0]
            cursor.execute(queries.compatibility_update_extension, (ver, ext))
        else:
            cursor.execute(queries.compatibility_insert, (ext, ver))

        module.add(cursor)

    def upgrade(self, extensions):
        self._execute(extensions, self._upgrade)

    def _upgrade(self, module, ext, cursor):
        to, from_ = self.dependencies['update'][ext]

        if ext is None:
            cursor.execute(queries.compatibility_update_core, (to, ))
        else:
            cursor.execute(queries.compatibility_update_extension, (to, ext))

        while from_ < to:
            getattr(module, 'upgrade_{}_to_{}'.format(from_, from_ + 1))(
                                                                        cursor)
            from_ += 1

    def remove(self, extensions, ignored=False):
        self._execute(extensions, self._remove, ignored=ignored)

    def _remove(self, module, ext, cursor, ignored=False):
        if ignored:
            cursor.execute(queries.compatibility_update_extension, (None, ext))
        else:
            cursor.execute(queries.compatibility_delete, (ext, ))

        module.remove(cursor)


class DatabaseNotValidError(OutsplineError):
    pass


class DatabaseIncompatibleError(OutsplineError):
    def __init__(self, updater):
        self.updater = updater


class DatabaseIncompatibleAddError(DatabaseIncompatibleError):
    def __init__(self, updater):
        super(DatabaseIncompatibleAddError, self).__init__(updater)


class DatabaseIncompatibleUpdateError(DatabaseIncompatibleError):
    def __init__(self, updater):
        super(DatabaseIncompatibleUpdateError, self).__init__(updater)


class DatabaseIncompatibleAbortError(DatabaseIncompatibleError):
    def __init__(self, updater):
        super(DatabaseIncompatibleAbortError, self).__init__(updater)
