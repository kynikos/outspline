# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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
import importlib

import outspline.components.main
import outspline.info as info

from configuration import (_USER_CONFIG_FILE, _COPYRIGHT, _DESCRIPTION,
                                        _DISCLAIMER_SHORT, components, config)


class ShowVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print("Outspline {} ({})\n\n{}\n{}".format(
                                        outspline.components.main.version,
                                        outspline.components.main.release_date,
                                        _COPYRIGHT, _DISCLAIMER_SHORT))
        sys.exit()


class ShowAbout(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print("Installed components:")
        for cname in components["info"]:
            component = components["info"][cname]

            print("{}{} {} ({})".format("\t", cname, component.version,
                                                    component.release_date))

            try:
                assert component.provides_core
            except (AttributeError, AssertionError):
                pass
            else:
                print("{}Core {}".format("\t" * 2, info.core.version))

            for type_ in ("extensions", "interfaces", "plugins"):
                try:
                    addons = getattr(component, type_)
                except AttributeError:
                    pass
                else:
                    print("{}{}:".format("\t" * 2, type_.capitalize()))

                    for aname in addons:
                        addon = importlib.import_module(".".join(("outspline",
                                                        "info", type_, aname)))
                        print ("{}{} {}".format("\t" * 3, aname,
                                                                addon.version))

        sys.exit()


def parse_cli_args():
    # Options -h and --help are automatically created
    cliparser = argparse.ArgumentParser(description=_DESCRIPTION)

    cliparser.add_argument('-c',
                           '--config',
                           default=None,
                           metavar='FILE',
                           dest='configfile',
                           help='set the configuration file name: a relative '
                                'or full path can be specified (default: {})'
                                ''.format(_USER_CONFIG_FILE))

    cliparser.add_argument('-l',
                           '--logfile',
                           default=None,
                           metavar='FILE',
                           dest='logfile',
                           help='set the log file name: a relative or full '
                                'path can be specified (default: {}, see also '
                                '--loglevel option)'
                                ''.format(os.path.expanduser(config('Log'
                                                            )['log_file'])))

    cliparser.add_argument('-L',
                           '--loglevel',
                           default=None,
                           metavar='NN',
                           dest='loglevel',
                           help='a 2-digit number (in base 4, from 00 to 33) '
                                'whose digits define the verbosity of, '
                                'respectively, stdout and file log messages; '
                                '0) disabled; 1) essential reports; 2) normal '
                                'verbosity; 3) debug mode; digits different '
                                'from 0,1,2,3 will default to the respective '
                                'value set in the configuration file '
                                '(default: {}{}, see also --logfile option)'
                                ''.format(config('Log')['log_level_stdout'],
                                config('Log')['log_level_file']))

    cliparser.add_argument('-u',
                           '--config-update',
                           action='store_true',
                           dest='updonly',
                           help='only create or update the configuration '
                                'file, then exit')

    cliparser.add_argument('-v',
                           '--version',
                           action=ShowVersion,
                           nargs=0,
                           dest='version',
                           help='show program\'s version number, copyright '
                                'and license information, then exit')

    cliparser.add_argument('--about',
                           action=ShowAbout,
                           nargs=0,
                           dest='about',
                           help='show information on the installed components '
                                                    'and addons, then exit')

    return cliparser.parse_args()
