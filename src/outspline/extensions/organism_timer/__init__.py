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

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_api as organism_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')

import outspline.info.extensions.organism_timer as info

import queries
import timer

extension = None


class Main(object):
    def __init__(self):
        self.rules = timer.Rules()
        self.databases = {}
        self.nextoccsengine = timer.NextOccurrencesEngine(self.databases,
                                                        self.rules.handlers)

        core_api.bind_to_open_database_dirty(self._handle_open_database_dirty)
        core_api.bind_to_close_database(self._handle_close_database)
        core_api.bind_to_delete_subtree(
                                self._handle_search_next_occurrences_request)
        core_api.bind_to_history(self._handle_search_next_occurrences_request)
        core_api.bind_to_exit_app_1(
                        self._handle_search_next_occurrences_cancel_request)

        organism_api.bind_to_open_database(self._handle_open_database)
        organism_api.bind_to_update_item_rules_conditional(
                                self._handle_search_next_occurrences_request)

        if copypaste_api:
            copypaste_api.bind_to_items_pasted(
                                self._handle_search_next_occurrences_request)

    def _handle_open_database_dirty(self, kwargs):
        dependencies = info.database_dependency_group_1

        try:
            for dep in dependencies:
                if dep not in kwargs["dependencies"]:
                    raise UserWarning()
        except UserWarning:
            pass
        else:
            filename = kwargs['filename']
            self.databases[filename] = timer.Database(filename)

    def _handle_open_database(self, kwargs):
        filename = kwargs['filename']

        try:
            self.databases[filename].start_old_occurrences_search()
        except KeyError:
            pass
        else:
            self.nextoccsengine.restart()

    def _handle_search_next_occurrences_request(self, kwargs):
        self.nextoccsengine.restart()

    def _handle_search_next_occurrences_cancel_request(self, kwargs):
        self.nextoccsengine.cancel()

    def _handle_close_database(self, kwargs):
        try:
            del self.databases[kwargs['filename']]
        except KeyError:
            pass
        else:
            self.nextoccsengine.restart()


def main():
    global extension
    extension = Main()
