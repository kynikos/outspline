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

import outspline.core_api as core_api

from organism import extension, items, database_open_event


def install_rule_handler(rulename, handler):
    return extension.rules.install_rule_handler(rulename, handler)


def update_item_rules(filename, id_, rules, group,
                                            description='Update item rules'):
    # All rules must be able to produce only occurrences compliant with the
    # following requirements:
    # - Normal rules:
    #   * 'alarm', 'start' and 'end', if set, must be integers representing a
    #     Unix time each
    #   * 'start' must always be set
    #   * 'end', if set, must always be greater than 'start'
    # - Except rules:
    #   * 'start' and 'end' must be integers representing a Unix time
    #     each
    #   * 'inclusive' must be a boolean value
    #   * 'start', 'end' and 'inclusive' must always be set
    #   * 'end' must always be greater than 'start'
    return extension.databases[filename].update_item_rules(id_, rules, group,
                                   description=description)


def get_supported_open_databases():
    return extension.databases.keys()


def get_item_rules(filename, id_):
    return extension.databases[filename].get_item_rules(id_)


def get_all_valid_item_rules(filename):
    return extension.databases[filename].get_all_valid_item_rules()


def get_all_item_rules(filename):
    return extension.databases[filename].get_all_item_rules()


def get_occurrences_range(mint, maxt, filenames):
    return items.OccurrencesRangeSearch(mint, maxt, filenames,
                                extension.databases, extension.rules.handlers)


def convert_string_to_rules(string):
    return items.Database.string_to_rules(string)


def bind_to_open_database(handler, bind=True):
    return database_open_event.bind(handler, bind)


def bind_to_history_insert(handler, bind=True):
    return items.history_insert_event.bind(handler, bind)


def bind_to_history_update(handler, bind=True):
    return items.history_update_event.bind(handler, bind)


def bind_to_update_item_rules_conditional(handler, bind=True):
    return items.update_item_rules_conditional_event.bind(handler, bind)


def bind_to_delete_item_rules(handler, bind=True):
    return items.delete_item_rules_event.bind(handler, bind)


def bind_to_get_alarms(handler, bind=True):
    return items.get_alarms_event.bind(handler, bind)
