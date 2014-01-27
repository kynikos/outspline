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

import wxalarms


def get_active_alarms():
    return [{
        'filename': wxalarms.alarmswindow.alarms[a].get_filename(),
        'id': wxalarms.alarmswindow.alarms[a].get_id(),
        'alarmid': wxalarms.alarmswindow.alarms[a].get_alarmid(),
    } for a in wxalarms.alarmswindow.alarms]


def simulate_set_snooze_time(number, unit):
    wxalarms.alarmswindow.number.SetValue(number)
    wxalarms.alarmswindow.unit.SetSelection(
                                wxalarms.alarmswindow.unit.FindString(unit))


def simulate_snooze_alarm(filename, alarmid):
    aitem = wxalarms.alarmswindow.make_alarmid(filename, alarmid)
    return wxalarms.alarmswindow.alarms[aitem].snooze(None)


def simulate_dismiss_alarm(filename, alarmid):
    aitem = wxalarms.alarmswindow.make_alarmid(filename, alarmid)
    return wxalarms.alarmswindow.alarms[aitem].dismiss(None)


def simulate_snooze_all_alarms():
    return wxalarms.alarmswindow.snooze_all(None)


def simulate_dismiss_all_alarms():
    return wxalarms.alarmswindow.dismiss_all(None)
