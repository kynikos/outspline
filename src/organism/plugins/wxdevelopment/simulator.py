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

import random
from Queue import Empty
import wx

import organism.core_api as core_api
import organism.coreaux_api as coreaux_api
from organism.coreaux_api import log

import simulator_actions

# [1] Do not instantiate timer with a dummy wx.CallAfter call, in fact it's
# necessary to distinguish when the simulator is active or not, since there is a
# very short time interval, between each action is called and the next timer is
# started, when timer.IsRunning() would return False although the simulator is
# actually still active
timer = None


def start():
    log.debug('Start simulator')

    DELAY = coreaux_api.get_plugin_configuration('wxdevelopment'
                                                    ).get_int('simulator_delay')

    # Don't use a combination of threading.Timer and wx.CallAfter, both for
    # simplicity and because Timer.is_alive() doesn't seem to return False
    # immediately as the action is executed, and this way *sometimes* the
    # application would execute the stop function, which should be put at the
    # top of the restart fucntion, before actually restarting the timer (this
    # would be a minor bug anyway, but using wx.CallLater avoids it, so prefer
    # using it)
    global timer
    timer = wx.CallLater(DELAY, _do_action)

def _restart():
    # This check is performed for safety, note that it's different from the
    # check in stop, see also comment [1]
    if timer.IsRunning():
        timer.Stop()

    timer.Restart()

def stop(kwargs=None):
    # kwargs is passed from the binding to core_api.bind_to_exit_app_1

    # Do *not* check also if timer.IsRunning(), see also comment [1]
    if timer:
        log.debug('Stop simulator')
        timer.Stop()

        global timer
        timer = None

def is_active():
    # See also comment [1]
    return True if timer else False

def _do_action():
    # [2] Try to block the databases here to avoid hanging the program in case
    # e.g. modal windows are active: this is not a perfect solution, in fact the
    # databases must be released just before calling the simulator action, which
    # has to block them again. This way there's still a (very) short interval
    # between the release_databases and the block_databases called by the
    # simulator actions when the user or the alarms timer can still block the
    # databases, thus hanging the program; note that the simulator is not
    # designed to be used while interacting manually (the problem with alarms
    # remains, though, although they should block the databases on their own
    # thread, and this should prevent hanging the whole application)
    try:
        core_api.block_databases(False)
    except Empty:
        log.debug('Databases are locked')
        _restart()
    else:
        if random.choice(simulator_actions.ACTIONS)() == False:
            # core_api.release_databases must be called by the action even in
            # case it returns False, see also comment [2]
            _do_action()
        else:
            # core_api.release_databases must be called by the action, see also
            # comment [2]
            _restart()
