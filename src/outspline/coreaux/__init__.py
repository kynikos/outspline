# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import configuration
from events import uncaught_exception_event


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


def main():
    configuration.load_addon_info()
    configuration.load_default_config()

    import cliargparse
    cliargs = cliargparse.parse_cli_args()

    configuration.load_user_config(cliargs)

    import logger
    logger.set_logger(cliargs)

    sys.excepthook = handle_uncaught_exception
