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

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api
import outspline.interfaces.wxgui_api as wxgui_api
organism_alarms_api = coreaux_api.import_optional_extension_api(
                                                              'organism_alarms')
wxcopypaste_api = coreaux_api.import_optional_plugin_api('wxcopypaste')
wxalarms_api = coreaux_api.import_optional_plugin_api('wxalarms')

import msgboxes


def check_all_active_alarms_have_a_corresponding_item(kwargs):
    leftovers = set()
    for alarm in wxalarms_api.get_active_alarms():
        if alarm['filename'] not in \
                         organism_alarms_api.get_supported_open_databases() or \
                   alarm['id'] not in core_api.get_items_ids(alarm['filename']):
            leftovers.add((alarm['filename'], str(alarm['id'])))
    if leftovers:
        msgboxes.warn_generic('The following active alarms don\'t have a '
                              'corresponding item any more:\n{}'.format(
                              '\n'.join([' '.join(a) for a in leftovers]))
                              ).ShowModal()


def main():
    if organism_alarms_api and wxalarms_api:
        wxgui_api.bind_to_delete_items(
                              check_all_active_alarms_have_a_corresponding_item)
        wxgui_api.bind_to_undo_tree(
                              check_all_active_alarms_have_a_corresponding_item)
        wxgui_api.bind_to_redo_tree(
                              check_all_active_alarms_have_a_corresponding_item)
        if wxcopypaste_api:
            wxcopypaste_api.bind_to_cut_items(
                              check_all_active_alarms_have_a_corresponding_item)
