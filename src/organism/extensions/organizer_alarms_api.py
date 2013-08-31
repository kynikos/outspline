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

from organizer_alarms import queries, timer, occurrences


def select_alarmsproperties_table(filename):
    qconn = core_api.get_connection(filename)
    cur = qconn.cursor()
    cur.execute(queries.alarmsproperties_select)
    core_api.give_connection(filename, qconn)
    return cur


def select_alarms_table(filename):
    qconn = core_api.get_connection(filename)
    cur = qconn.cursor()
    cur.execute(queries.alarms_select)
    core_api.give_connection(filename, qconn)
    return cur


def select_copyalarms_table():
    qmemory = core_api.get_memory_connection()
    cur = qmemory.cursor()
    cur.execute(queries.copyalarms_select)
    core_api.give_memory_connection(qmemory)
    return cur


def snooze_alarms(alarmst, stime):
    occurrences.snooze_alarms(alarmst, stime)


def dismiss_alarms(alarmst):
    occurrences.dismiss_alarms(alarmst)


def bind_to_search_alarms(handler, bind=True):
    return timer.search_alarms_event.bind(handler, bind)


def bind_to_alarm(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return occurrences.alarm_event.bind(handler, bind)


def bind_to_alarms(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return occurrences.alarms_event.bind(handler, bind)


def bind_to_alarm_off(handler, bind=True):
    return occurrences.alarm_off_event.bind(handler, bind)
