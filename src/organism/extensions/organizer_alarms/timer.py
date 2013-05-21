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

import alarmsmod


def activate_alarms(time, alarmsd):
    # It's important that the database is blocked on this thread, and not on the
    # main thread, otherwise the program would hang if the user is performing
    # an action
    core_api.block_databases()

    alarmsmod.activate_alarms(time, alarmsd)
    from organism.extensions.organizer_timer.timer import search_alarms  # TEMP import *************************
    search_alarms()

    core_api.release_databases()
