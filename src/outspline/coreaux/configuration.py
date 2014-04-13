# coding: utf-8

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

import os
import errno
import locale
from datetime import datetime

import configfile

import exceptions

# The program must explicitly say that it wants the user's preferred locale
# settings
# http://docs.python.org/2/library/locale.html#background-details-hints-tips-and-caveats
locale.setlocale(locale.LC_ALL, '')

__author__ = "Dario Giovannetti <dev@dariogiovannetti.net>"

_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
_CORE_INFO = os.path.join(_ROOT_DIR, 'coreaux', 'core.info')
_CONFIG_FILE = os.path.join(_ROOT_DIR, 'outspline.conf')
_USER_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.config',
                                 'outspline', 'outspline.conf')
_USER_FOLDER_PERMISSIONS = 0750
_DESCRIPTION_LONG = 'Outspline is a highly modular outliner whose '\
                    'functionality can be widely extended through the '\
                    'installation of addons.'
_COPYRIGHT_V1 = 'Copyright (C) 2011-{} Dario Giovannetti '\
                '<dev@dariogiovannetti.net>'.format(datetime.now().year)
_COPYRIGHT_V2 = 'Copyright © 2011-{} Dario Giovannetti'.format(datetime.now(
                                                                         ).year)
_DISCLAIMER_SHORT = \
'''This program comes with ABSOLUTELY NO WARRANTY.
This is free software, you are welcome to redistribute it under the
conditions of the GNU General Public License version 3 or later.
See <http://gnu.org/licenses/gpl.html> for details.'''
_DISCLAIMER = \
'''Outspline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Outspline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Outspline.  If not, see <http://www.gnu.org/licenses/>.'''

user_config_file = _USER_CONFIG_FILE
components = None
info = None
config = None


def load_component_info():
    global components

    components = configfile.ConfigFile({}, inherit_options=False)
    components.make_subsection('Components')
    components.make_subsection('Core')
    components.make_subsection('Extensions')
    components.make_subsection('Interfaces')
    components.make_subsection('Plugins')

    for c in os.listdir(_ROOT_DIR):
        split = os.path.splitext(c)

        if split[1] == '.component':
            components('Components').make_subsection(split[0])
            components('Components')(split[0]).add(os.path.join(_ROOT_DIR, c))

            if components('Components')(split[0]).get_bool('provides_core',
                                                              fallback='false'):
                if 'core' not in components:
                    components['core'] = split[0]
                else:
                    raise exceptions.ComponentConflictError()

            for a in components('Components')(split[0]):
                if a[:9] == 'extension':
                    extension, version = components('Components')(split[0])[a
                                                                    ].split(' ')
                    components('Extensions').make_subsection(extension)

                    if version not in components('Extensions')(extension):
                        components('Extensions')(extension)[version] = split[0]
                    else:
                        raise exceptions.ComponentConflictError()
                elif a[:9] == 'interface':
                    interface, version = components('Components')(split[0])[a
                                                                    ].split(' ')
                    components('Interfaces').make_subsection(interface)

                    if version not in components('Interfaces')(interface):
                        components('Interfaces')(interface)[version] = split[0]
                    else:
                        raise exceptions.ComponentConflictError()
                elif a[:6] == 'plugin':
                    plugin, version = components('Components')(split[0])[a
                                                                    ].split(' ')
                    components('Plugins').make_subsection(plugin)

                    if version not in components('Plugins')(plugin):
                        components('Plugins')(plugin)[version] = split[0]
                    else:
                        raise exceptions.ComponentConflictError()

    if 'core' not in components:
        raise exceptions.CoreComponentNotFoundError()


def load_addon_info_and_default_config():
    global info
    global config

    info = configfile.ConfigFile({}, inherit_options=False)
    info.make_subsection('Core')
    info('Core').add(_CORE_INFO)

    config = configfile.ConfigFile(_CONFIG_FILE, inherit_options=False)

    for t in ('Extensions', 'Interfaces', 'Plugins'):
        info.make_subsection(t)

        # Note that an addon needs to be provided by a component in order to be
        # loaded (the mere existence of its folder and files is not enough)
        for a in components(t).get_sections():
            info(t).make_subsection(a)
            config(t).make_subsection(a)

            # Let the normal exception be raised if the .info or .conf files are
            # not found
            info(t)(a).add(os.path.join(_ROOT_DIR, t.lower(), a, a + '.info'))
            config(t)(a).add(os.path.join(_ROOT_DIR, t.lower(), a + '.conf'))

            if info(t)(a)['version'] not in components(t)(a).get_options():
                raise exceptions.AddonNotFoundError()


def load_user_config(cliargs):
    if cliargs.configfile != None:
        global user_config_file
        user_config_file = os.path.expanduser(cliargs.configfile)
        config.upgrade(user_config_file)
    else:
        try:
            config.upgrade(_USER_CONFIG_FILE)
        except configfile.InvalidFileError:
            pass

    try:
        os.makedirs(os.path.dirname(user_config_file),
                    mode=_USER_FOLDER_PERMISSIONS)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def export_configuration():
    config.export_add(user_config_file)
