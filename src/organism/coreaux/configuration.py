# Organism - Organism, a simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
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

import os
import errno

import configfile

__author__ = "Dario Giovannetti <dev@dariogiovannetti.com>"

_ROOT_DIR = 'src/organism'
_CORE_INFO = os.path.join(_ROOT_DIR, 'coreaux', 'core.info')
_CONFIG_FILE = os.path.join(_ROOT_DIR, 'organism.conf')
_USER_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.config',
                                 'organism', 'organism.conf')
_USER_FOLDER_PERMISSIONS = 0750

info = configfile.ConfigFile(_CORE_INFO, inherit_options=False)
user_config_file = _USER_CONFIG_FILE
config = None


def load_default_config():
    global config
    config = configfile.ConfigFile(_CONFIG_FILE, inherit_options=False)


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
