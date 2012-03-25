# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import sys

from coreaux.configuration import info, config, _ROOT_DIR
import coreaux.configuration
# Import the base Exception so that it can be imported by interfaces and
# plugins
from coreaux.exceptions import OrganismError
# Import the logger so that it can be imported by interfaces and plugins
from coreaux.logger import log
# Import the base Event so that it can be imported by interfaces and plugins
from coreaux.events import Event
import coreaux.events
import coreaux.addons


def get_main_component_version():
    return info['component_version']


def get_core_version():
    return info['version']


def get_main_component_release_date():
    return info['component_release_date']


def get_website():
    return info['website']


def get_core_contributors():
    return [info[o] for o in info.get_options() if o[:11] == 'contributor']


def get_installed_components():
    components = ['{} {} ({})'.format(info['component'],
                                      info['component_version'],
                                      info['component_release_date'])]
    addons = coreaux.addons.get_addons_info()
    for t in addons.get_sections():
        for a in addons(t).get_sections():
            addon = addons(t)(a)
            component = '{} {} ({})'.format(addon['component'],
                                            addon['component_version'],
                                            addon['component_release_date'])
            if component not in components:
                components.append(component)
    return components


def get_standard_extension():
    return config('Save')['default_extension']


def get_root_directory():
    return _ROOT_DIR


def get_description():
    return info['description']


def get_user_config_file():
    return coreaux.configuration.user_config_file


def get_addons_info(disabled=True):
    return coreaux.addons.get_addons_info(disabled=disabled)


def get_configuration():
    return config


def get_extension_configuration(extension):
    return config('Extensions')(extension)


def get_interface_configuration(interface):
    return config('Interfaces')(interface)


def get_plugin_configuration(plugin):
    return config('Plugins')(plugin)


def get_default_history_limit():
    return config('History').get_int('default_max_operations')


def import_extension_api(extension):
    if extension in config('Extensions').get_sections() and \
                           config('Extensions')(extension).get_bool('enabled'):
        # extension = __import__('organism.extensions.' + extension + '_api')
        # somehow doesn't work
        __import__('organism.extensions.' + extension + '_api')
        return sys.modules['organism.extensions.' + extension + '_api']


def import_interface_api(interface):
    if interface in config('Interfaces').get_sections() and \
                           config('Interfaces')(interface).get_bool('enabled'):
        # interface = __import__('organism.interfaces.' + interface + '_api')
        # somehow doesn't work
        __import__('organism.interfaces.' + interface + '_api')
        return sys.modules['organism.interfaces.' + interface + '_api']


def import_plugin_api(plugin):
    if plugin in config('Plugins').get_sections() and \
                                 config('Plugins')(plugin).get_bool('enabled'):
        # plugin = __import__('organism.plugins.' + plugin + '_api') somehow
        # doesn't work
        __import__('organism.plugins.' + plugin + '_api')
        return sys.modules['organism.plugins.' + plugin + '_api']


def bind_to_addons_loaded(handler, bind=True):
    return coreaux.addons.addons_loaded_event.bind(handler, bind)


def bind_to_uncaught_exception(handler, bind=True):
    return coreaux.events.uncaught_exception_event.bind(handler, bind)
