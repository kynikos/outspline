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

import sys
import os
import errno
import locale
from datetime import datetime
import importlib
import pkgutil

import outspline.conf as conf_
import outspline.static.configfile as configfile

import exceptions

# The program must explicitly say that it wants the user's preferred locale
# settings
# http://docs.python.org/2/library/locale.html#background-details-hints-tips-and-caveats
locale.setlocale(locale.LC_ALL, '')

MAIN_THREAD_NAME = "MAIN"
_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
_USER_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.config',
                                                'outspline', 'outspline.conf')
_USER_FOLDER_PERMISSIONS = 0750
_COMPONENTS_DIR = os.path.join(_ROOT_DIR, "components")
_CONFIG_DIR = os.path.join(_ROOT_DIR, "conf")
# Use the icons in $XDG_DATA_DIRS/icons only when there's no alternative, e.g.
#  for the .desktop file and the notifications
BUNDLED_DATA_DIR = os.path.join(_ROOT_DIR, "data")
_DESCRIPTION = ("Outspline - An outliner with optional advanced time "
                                                    "management features.")
_DESCRIPTION_2 = ("Outspline is an extensible outliner with optional "
                                        "advanced time management features.")
_COPYRIGHT = ('Copyright (C) 2011-{} Dario Giovannetti '
                '<dev@dariogiovannetti.net>'.format(datetime.now().year))
_COPYRIGHT_UNICODE = 'Copyright © 2011-{} Dario Giovannetti'.format(
                                                        datetime.now().year)
_DISCLAIMER_SHORT = \
'''This program comes with ABSOLUTELY NO WARRANTY.
This is free software, you are welcome to redistribute it under the
conditions of the GNU General Public License version 3 or later.
See <http://gnu.org/licenses/gpl.html> for details.'''
_DISCLAIMER = \
'''Outspline - A highly modular and extensible outliner.
Copyright (C) 2011-{} Dario Giovannetti <dev@dariogiovannetti.net>

Outspline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Outspline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Outspline.  If not, see <http://www.gnu.org/licenses/>.'''.format(
                                                        datetime.now().year)

user_config_file = _USER_CONFIG_FILE
components = {
    "info": {},
    "addons": {
        "core": None,
        "Extensions": {},
        "Interfaces": {},
        "Plugins": {},
    },
}
config = None
update_only = False


def load_components_info():
    for module_loader, comp_name, ispkg in pkgutil.iter_modules((
                                                        _COMPONENTS_DIR, )):
        module = importlib.import_module(".".join(("outspline", "components",
                                                                comp_name)))
        components["info"][comp_name] = module

        try:
            assert module.provides_core
        except (AttributeError, AssertionError):
            pass
        else:
            components["addons"]["core"] = comp_name

        for type_ in ("Extensions", "Interfaces", "Plugins"):
            try:
                addons = getattr(module, type_.lower())
            except AttributeError:
                pass
            else:
                for addon in addons:
                    components["addons"][type_][addon] = comp_name


def load_default_config():
    global config
    config = configfile.ConfigFile(conf_.core.data)

    for type_ in ('Extensions', 'Interfaces', 'Plugins'):
        for module_loader, addon_name, ispkg in pkgutil.iter_modules((
                                    os.path.join(_CONFIG_DIR, type_.lower()), )):
            config(type_).make_subsection(addon_name)

            aconf = importlib.import_module(".".join(("outspline", "conf",
                                                type_.lower(), addon_name)))
            config(type_)(addon_name).add(aconf.data)


def set_configuration_file(cliargs):
    if cliargs.configfile != None:
        global user_config_file
        user_config_file = os.path.expanduser(cliargs.configfile)

    return user_config_file


def set_update_only(cliargs):
    global update_only
    update_only = cliargs.updonly


def load_configuration():
    # Try to make the directory separately from the logger, because they could
    # be set to different paths
    try:
        os.makedirs(os.path.dirname(user_config_file),
                                                mode=_USER_FOLDER_PERMISSIONS)
    except OSError as e:
        # ENOENT can happen if user_config_file is a string without "/", i.e.
        # it represents a file in the current folder
        if e.errno not in (errno.EEXIST, errno.ENOENT):
            raise

    try:
        config.upgrade(user_config_file)
    except configfile.NonExistentFileError:
        # If the file just doesn't exist, create it (happens later)
        pass
    except configfile.InvalidFileError:
        # If the file is unreadable but exists, better be safe and crash here
        # instead of overwriting it
        raise


def export_configuration(log):
    config.export_add(user_config_file)

    if update_only:
        log.info('Configuration file correctly created or updated')
        sys.exit()
