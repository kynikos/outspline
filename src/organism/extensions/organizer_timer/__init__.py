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
import organism.extensions.organizer_api as organizer_api
copypaste_api = coreaux_api.import_extension_api('copypaste')

import timer


def handle_search_occurrences(kwargs):
    timer.search_occurrences()


def main():
    core_api.bind_to_open_database(handle_search_occurrences)
    core_api.bind_to_close_database(handle_search_occurrences)
    core_api.bind_to_delete_items(handle_search_occurrences)
    core_api.bind_to_history(handle_search_occurrences)
    core_api.bind_to_exit_app_1(timer.cancel_timer)

    organizer_api.bind_to_update_item_rules(handle_search_occurrences)

    if copypaste_api:
        copypaste_api.bind_to_items_pasted(handle_search_occurrences)
