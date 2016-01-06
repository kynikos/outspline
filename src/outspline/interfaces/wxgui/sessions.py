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

import wx

import outspline.coreaux_api as coreaux_api

import rootw
import databases


class SessionManager(object):
    def __init__(self):
        self.savedession = coreaux_api.get_interface_configuration('wxgui')(
                                                                'SessionFiles')
        # Use CallAfter in order to let the interface be completely drawn,
        # before e.g. showing the database upgrade dialog
        wx.CallAfter(self._post_init)

    def _post_init(self):
        for o in self.savedession:
            filename = self.savedession[o]
            databases.open_database(filename)

        try:
            wx.GetApp().nb_left.select_page(0)
        except IndexError:
            pass

        # Bind *after* opening the databases in the session, because the
        # session must be refreshed only when databases are opened manually
        databases.open_database_event.bind(self._handle_open_database)
        databases.close_database_event.bind(self._handle_close_database)

    def _handle_open_database(self, kwargs):
        self.refresh_session()

    def _handle_close_database(self, kwargs):
        if not kwargs['exit_']:
            self.refresh_session()

    def refresh_session(self):
        self.savedession.reset({})
        dbs = databases.get_open_databases()

        for n in dbs:
            self.savedession['db' + str(n)] = str(dbs[n])

        self.savedession.export_reset(coreaux_api.get_user_config_file())
