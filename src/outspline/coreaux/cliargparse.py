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
import os.path
import argparse

from configuration import (_USER_CONFIG_FILE, _COPYRIGHT_V1, _DISCLAIMER_SHORT,
                           components, info, config)


class ShowVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print("Outspline {} ({})\n\n{}\n{}".format(
                components('Components')(components['core'])['version'],
                components('Components')(components['core'])['release_date'],
                _COPYRIGHT_V1, _DISCLAIMER_SHORT))
        sys.exit()


def parse_cli_args():
    # Options -h and --help are automatically created
    cliparser = argparse.ArgumentParser(description=info('Core')[
                                                                'description'])

    cliparser.add_argument('-c',
                           '--config',
                           default=None,
                           metavar='FILE',
                           dest='configfile',
                           help='set the configuration file name: a relative '
                                'or full path can be specified (default: {})'
                                ''.format(_USER_CONFIG_FILE))

    cliparser.add_argument('-l',
                           '--loglevel',
                           default=None,
                           metavar='NN',
                           dest='loglevel',
                           help='a 2-digit number (in base 4, from 00 to 33) '
                                'whose digits define the verbosity of, '
                                'respectively, stdout and file log messages; '
                                '0) disabled; 1) essential reports; 2) normal '
                                'verbosity; 3) debug mode; digits different '
                                'from 0,1,2,3 will be converted to 3 '
                                '(default: {}, see also --logfile option)'
                                ''.format(config('Log')['log_level']))

    cliparser.add_argument('-f',
                           '--logfile',
                           default=None,
                           metavar='FILE',
                           dest='logfile',
                           help='set the log file name: a relative or full '
                                'path can be specified (default: {}, see also '
                                '--loglevel option)'
                                ''.format(os.path.expanduser(config('Log'
                                                            )['log_file'])))

    cliparser.add_argument('-v',
                           '--version',
                           '--about',
                           action=ShowVersion,
                           nargs=0,
                           dest='version',
                           help='show program\'s version number, copyright '
                                'and license information, then exit')

    return cliparser.parse_args()
