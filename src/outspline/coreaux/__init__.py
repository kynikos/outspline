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

import sys
import os
import hashlib
import threading

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
except ImportError:
    dbus = None

import configuration
from events import external_nudge_event, uncaught_exception_event


def handle_uncaught_exception(type, value, traceback):
    # This method is better than wrapping core.main() and coreaux.addons.main()
    # in a try except, in fact this way also exceptions from the interface's
    # main loop are caught
    logger.log.critical('Uncaught exception', exc_info=(type, value,
                                                        traceback))

    uncaught_exception_event.signal(exc_info=(type, value, traceback))

    # Force exit, since sys.exit() may just hang the application waiting for
    # the process to respond
    os._exit(1)


def check_existing_processes(configfile):
    # Append the configuration file to the well-known name, not just to the
    # service name, because in the latter case it would seem to work with 2
    # processes, but it wouldn't work as expected with 3 or more processes
    # Add "C" because a digit cannot follow a dot
    wkname = 'org.Kynikos.Outspline.C' + hashlib.md5(configfile).hexdigest()
    DBUS_SERVICE_NAME = "/Main"

    # This class must be defined here because dbus.service.method has to get
    # the right well-known-name
    class DbusService(dbus.service.Object):
        def __init__(self):
            busname = dbus.service.BusName(wkname, bus=bus)
            super(DbusService, self).__init__(busname, DBUS_SERVICE_NAME)

        @dbus.service.method(wkname)
        def nudge(self):
            external_nudge_event.signal()

    try:
        # DBusGMainLoop must be instantiated *before* SessionBus
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
    except dbus.exceptions.DBusException as err:
        # D-Bus may be installed but not started
        sys.exit("DBusException: " + err.message)
    else:
        try:
            service = bus.get_object(wkname, DBUS_SERVICE_NAME)
        except dbus.exceptions.DBusException:
            service = DbusService()
        else:
            nudge_existing_process = service.get_dbus_method('nudge', wkname)
            nudge_existing_process()
            sys.exit("Another instance of Outspline is using " + configfile)


def install_thread_excepthook():
    # This function is a workaround for bug #341
    init_old = threading.Thread.__init__

    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run

        def run_with_excepthook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())

        self.run = run_with_excepthook

    threading.Thread.__init__ = init


def main():
    configuration.load_components_info()
    configuration.load_default_config()

    import cliargparse
    cliargs = cliargparse.parse_cli_args()

    # This must be done *before* checking for existing processes, because a
    # configuration file may haven't been set in the command arguments
    configfile = configuration.set_configuration_file(cliargs)
    configuration.set_update_only(cliargs)

    if dbus:
        check_existing_processes(configfile)

    configuration.load_configuration()

    import logger
    logger.set_logger(cliargs)

    # Make sure the main thread has a known name
    threading.current_thread().setName(configuration.MAIN_THREAD_NAME)
    sys.excepthook = handle_uncaught_exception
    # The application must crash also if an exception is raised in a secondary
    # thread, for example because if the thread has blocked the databases, it
    # won't release them otherwise; yes, they could be released in a finally
    # clause, but that would leave the database in an unknown state, which is
    # pretty bad
    install_thread_excepthook()
