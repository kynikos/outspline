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

from organism_timer import extension, timer


def install_rule_handler(rulename, handler):
    # Warning, the handler will be executed on a separate thread!!!
    # (Check for race conditions)
    return extension.rules.install_rule_handler(rulename, handler)


def get_next_occurrences(base_time=None, base_times=None):
    return timer.NextOccurrencesSearch(extension.cdbs,
                                    extension.rules.handlers,
                                    base_time=base_time, base_times=base_times)


def search_next_occurrences():
    return timer.search_next_occurrences()


def bind_to_get_next_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    # (Check for race conditions)
    # Compare to bind_to_search_next_occurrences
    return timer.get_next_occurrences_event.bind(handler, bind)


def bind_to_search_next_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    # (Check for race conditions)
    # Compare to bind_to_get_next_occurrences
    return timer.search_next_occurrences_event.bind(handler, bind)


def bind_to_activate_occurrences_range(handler, bind=True):
    return timer.activate_occurrences_range_event.bind(handler, bind)


def bind_to_activate_old_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    # (Check for race conditions)
    return timer.activate_old_occurrences_event.bind(handler, bind)


def bind_to_activate_occurrences(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    # (Check for race conditions)
    return timer.activate_occurrences_event.bind(handler, bind)
