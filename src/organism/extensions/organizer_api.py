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

import organism.core_api as core_api

from organizer import queries, items


def update_item_rules(filename, id_, rules, group,
                      description='Update item rules'):
    return items.update_item_rules(filename, id_, rules, group,
                                   description=description)


def get_item_rules(filename, id_):
    return items.get_item_rules(filename, id_)


def get_occurrences_range(mint, maxt):
    # Note that the list is practically unsorted: sorting its items is a duty
    # of the interface
    return items.get_occurrences_range(mint, maxt)


def bind_to_update_item_rules(handler, bind=True):
    return items.update_item_rules_event.bind(handler, bind)


def bind_to_get_occurrences_range(handler, bind=True):
    return items.get_occurrences_range_event.bind(handler, bind)


def bind_to_get_alarms(handler, bind=True):
    return items.get_alarms_event.bind(handler, bind)
