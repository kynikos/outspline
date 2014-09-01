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

import os.path
import time
import wx

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import Event, OutsplineError
import outspline.core_api as core_api
import outspline.dbdeps as dbdeps

import editor
import msgboxes
import tree
import dbprops

open_database_event = Event()
close_database_event = Event()

dbpropmanager = dbprops.DatabasePropertyManager()
aborted_save_warnings = {}


def create_database(defpath=None, filename=None):
    if not filename:
        if not defpath:
            defpath = os.path.join(os.path.expanduser('~'),
                                    '.'.join(('new_database',
                                    coreaux_api.get_standard_extension())))

        dlg = msgboxes.create_db_ask()
        dlg.SetPath(defpath)

        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        else:
            return False

    if filename:
        try:
            core_api.create_database(filename)
        except core_api.DatabaseAlreadyOpenError:
            msgboxes.create_db_open(filename).ShowModal()
            return False
        except core_api.AccessDeniedError:
            msgboxes.create_db_access(filename).ShowModal()
            return False
        else:
            return filename
    else:
        return False


def open_database(filename=None, check_new_extensions=True,
                                                        open_properties=False):
    if not filename:
        dlg = msgboxes.open_db_ask(os.path.expanduser('~'))

        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        else:
            return False

    if filename:
        try:
            core_api.open_database(filename,
                                    check_new_extensions=check_new_extensions)
        except core_api.DatabaseAlreadyOpenError:
            msgboxes.open_db_open(filename).ShowModal()
            return False
        except core_api.DatabaseNotAccessibleError:
            msgboxes.open_db_access(filename).ShowModal()
            return False
        except dbdeps.DatabaseNotValidError:
            msgboxes.open_db_invalid(filename).ShowModal()
            return False
        except dbdeps.DatabaseIncompatibleAddError as err:
            msgboxes.DatabaseUpdaterAdd(err.updater, open_properties)
            return False
        except dbdeps.DatabaseIncompatibleUpdateError as err:
            msgboxes.DatabaseUpdaterUpdate(err.updater, open_properties)
            return False
        except dbdeps.DatabaseIncompatibleAbortError as err:
            msgboxes.DatabaseUpdaterAbort(err.updater)
            return False
        except core_api.DatabaseLockedError:
            msgboxes.open_db_locked(filename).ShowModal()
            return False
        else:
            tree.Database.open(filename)
            # Note that this event is also bound directly by the menubar and
            # sessions modules
            open_database_event.signal(filename=filename)

            if open_properties:
                dbpropmanager.open(filename)

            return True
    else:
        return False


def save_database_as(origin):
    for tab in tuple(editor.tabs.copy()):
        if editor.tabs[tab].get_filename() == origin and \
                                                  not editor.tabs[tab].close():
            break
    else:
        defpath = '{}_copy{}'.format(*os.path.splitext(origin))
        destination = create_database(defpath=defpath)

        if destination:
            try:
                core_api.save_database_copy(origin, destination)
            except OutsplineError as err:
                # This will leave the new created file empty, see bug #322
                warn_aborted_save(err)
            else:
                close_database(origin, no_confirm=True)
                open_database(destination)


def save_database_backup(origin):
    defpath = time.strftime('{}_%Y%m%d%H%M%S{}'.format(
                                                    *os.path.splitext(origin)))
    destination = create_database(defpath=defpath)

    if destination:
        try:
            core_api.save_database_copy(origin, destination)
        except OutsplineError as err:
            # This will leave the new created file empty, see bug #322
            warn_aborted_save(err)


def close_database(filename, no_confirm=False, exit_=False):
    # Do not use nb_left.select_tab() to get the tree, use tree.dbs
    nbl = wx.GetApp().nb_left

    # Temporary fix for bug #270
    sashposs = {filename: tree.dbs[filename].GetSashPosition() \
                                                    for filename in tree.dbs}

    for item in tuple(editor.tabs.keys()):
        if editor.tabs[item].get_filename() == filename:
            if editor.tabs[item].close(ask='quiet' if no_confirm else 'apply'
                                                                    ) == False:
                return False

    if not no_confirm and core_api.check_pending_changes(filename):
        save = msgboxes.close_db_ask(filename).ShowModal()
        if save == wx.ID_YES:
            try:
                core_api.save_database(filename)
            except OutsplineError as err:
                warn_aborted_save(err)
                return False
        elif save == wx.ID_CANCEL:
            return False

    index = nbl.GetPageIndex(tree.dbs[filename])
    tree.dbs[filename].close()
    nbl.close_page(index)

    core_api.close_database(filename)

    # Note that this event is also bound directly by the sessions and dbprops
    # modules
    close_database_event.signal(filename=filename, exit_=exit_)

    # Temporary fix for bug #270
    for filename in tree.dbs:
        tree.dbs[filename].SetSashPosition(sashposs[filename])

    return True


def get_open_databases():
    nbl = wx.GetApp().nb_left
    return {nbl.GetPageIndex(tree.dbs[db]): db for db in tree.dbs}


def register_aborted_save_warning(exception, message):
    global aborted_save_warnings
    aborted_save_warnings[exception] = message


def warn_aborted_save(error):
    try:
        msgboxes.warn_aborted_save(aborted_save_warnings[error.__class__]
                                                                ).ShowModal()
    except KeyError:
        msgboxes.warn_aborted_save(msgboxes.aborted_save_default_warning
                                                                ).ShowModal()
