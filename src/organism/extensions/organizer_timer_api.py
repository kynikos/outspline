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

from organizer_timer import timer


def get_last_search(filename):
    return timer.get_last_search(filename)


def get_next_occurrences():
    return timer.get_next_occurrences()


def bind_to_search_next_item_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return timer.search_next_item_occurrences_event.bind(handler, bind)


def bind_to_get_next_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return timer.get_next_occurrences_event.bind(handler, bind)


def bind_to_activate_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return timer.activate_occurrences_event.bind(handler, bind)
