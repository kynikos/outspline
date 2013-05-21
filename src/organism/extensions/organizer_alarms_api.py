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

from organizer_alarms import queries, alarmsmod


def snooze_alarms(alarmst, stime):
    alarmsmod.snooze_alarms(alarmst, stime)


def dismiss_alarms(alarmst):
    alarmsmod.dismiss_alarms(alarmst)


def bind_to_alarm(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return alarmsmod.alarm_event.bind(handler, bind)


def bind_to_alarms(handler, bind=True):
    # Warning, this function is executed on a separate thread!!!
    return alarmsmod.alarms_event.bind(handler, bind)


def bind_to_alarm_off(handler, bind=True):
    return alarmsmod.alarm_off_event.bind(handler, bind)
