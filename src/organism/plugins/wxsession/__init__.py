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

import organism.coreaux_api as coreaux_api
import organism.core_api as core_api
import organism.interfaces.wxgui_api as wxgui_api


def handle_addons_loaded(kwargs):
    config = coreaux_api.get_plugin_configuration('wxsession')
    for o in config('Files'):
        filename = config('Files')[o]
        wxgui_api.open_database(filename, startup=True)

    try:
        wxgui_api.select_database_tab_index(0)
    except IndexError:
        pass


def handle_open_database(kwargs):
    if not kwargs['startup']:
        refresh_session()


def handle_close_database(kwargs):
    if not kwargs['exit_']:
        refresh_session()


def handle_exit_application(kwargs):
    # Refresh also when exiting, in order to save the order of visualization of
    # the tabs
    refresh_session()


def refresh_session():
    config = coreaux_api.get_plugin_configuration('wxsession')
    config('Files').reset({})
    for n, filename in enumerate(core_api.get_open_databases()):
        config('Files')['db' + str(n)] = str(filename)
    config('Files').export_reset(coreaux_api.get_user_config_file())


def main ():
    coreaux_api.bind_to_addons_loaded(handle_addons_loaded)
    wxgui_api.bind_to_open_database(handle_open_database)
    wxgui_api.bind_to_close_database(handle_close_database)
    wxgui_api.bind_to_exit_application(handle_exit_application)
