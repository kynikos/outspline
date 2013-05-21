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

from threading import Timer
import time as _time

from organism.coreaux_api import log
import organism.core_api as core_api
import organism.extensions.organizer_timer as organizer_timer  # TEMP import *************************

import alarmsmod

timer = None


def restart_timer(oldalarms, next_alarm, alarmsd):
    cancel_timer()

    now = int(_time.time())

    if oldalarms:
        alarmsmod.activate_alarms(now, oldalarms, old=True)

    if next_alarm != None:
        if next_alarm <= now:
            alarmsmod.activate_alarms(next_alarm, alarmsd)
            organizer_timer.timer.search_alarms()
        else:
            next_loop = next_alarm - now
            global timer
            timer = Timer(next_loop, activate_alarms, (next_alarm, alarmsd, ))
            timer.start()

            log.debug('Timer refresh: {}'.format(next_loop))
    else:
        # If no alarm is found, execute activate_alarms, which will in turn
        # execute set_last_search, so that if a rule is created with an alarm
        # time between the last search and now, the alarm won't be activated
        alarmsmod.activate_alarms(now, alarmsd)



def cancel_timer(kwargs=None):
    # kwargs is passed from the binding to core_api.bind_to_exit_app_1
    if timer and timer.is_alive():
        log.debug('Timer cancel')
        timer.cancel()


def activate_alarms(time, alarmsd):
    # It's important that the database is blocked on this thread, and not on the
    # main thread, otherwise the program would hang if the user is performing
    # an action
    core_api.block_databases()

    alarmsmod.activate_alarms(time, alarmsd)
    organizer_timer.timer.search_alarms()

    core_api.release_databases()
