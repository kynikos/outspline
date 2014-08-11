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
import importlib
import copy
import json

from coreaux.configuration import components, info, config
import coreaux.configuration
# Import the base Exception so that it can be imported by interfaces and
# plugins
from coreaux.exceptions import OutsplineError
# Import the logger so that it can be imported by interfaces and plugins
from coreaux.logger import log
# Import the base Event so that it can be imported by interfaces and plugins
from coreaux.events import Event
import coreaux.events
import coreaux.addons


def get_main_component_version():
    return components('Components')(components['core'])['version']


def get_main_component_release_date():
    return components('Components')(components['core'])['release_date']


def get_core_version():
    return info('Core')['version']


def get_website():
    return info('Core')['website']


def get_core_contributors():
    return json.loads(info('Core').get('contibutors', fallback="[]"))


def get_standard_extension():
    return config('Save')['default_extension']


def get_root_directory():
    return coreaux.configuration._ROOT_DIR


def get_copyright(alt=False):
    return coreaux.configuration._COPYRIGHT_V2 if alt else \
                                            coreaux.configuration._COPYRIGHT_V1


def get_disclaimer():
    return coreaux.configuration._DISCLAIMER


def get_description():
    return info('Core')['description']


def get_long_description():
    return coreaux.configuration._DESCRIPTION_LONG


def get_user_config_file():
    return coreaux.configuration.user_config_file


def get_components_info():
    return components


def get_addons_info(disabled=True):
    if not disabled:
        cinfo = copy.deepcopy(info)

        for t in ('Extensions', 'Interfaces', 'Plugins'):
            for a in cinfo(t).get_sections():
                if not config(t)(a).get_bool('enabled'):
                    cinfo(t)(a).delete()

        return cinfo
    else:
        return info


def get_configuration():
    return config


def get_extension_configuration(extension):
    return config('Extensions')(extension)


def get_interface_configuration(interface):
    return config('Interfaces')(interface)


def get_plugin_configuration(plugin):
    return config('Plugins')(plugin)


def import_optional_extension_api(extension):
    if extension in config('Extensions').get_sections() and \
                        config('Extensions')(extension).get_bool('enabled'):
        return importlib.import_module(''.join(('outspline.extensions.',
                                                        extension, '_api')))


def import_optional_interface_api(interface):
    # Interfaces are not optional, but a plugin may support more than one
    # interface, and this is the safe way to test which one is enabled
    if interface in config('Interfaces').get_sections() and \
                        config('Interfaces')(interface).get_bool('enabled'):
        return importlib.import_module(''.join(('outspline.interfaces.',
                                                        interface, '_api')))


def import_optional_plugin_api(plugin):
    if plugin in config('Plugins').get_sections() and \
                                config('Plugins')(plugin).get_bool('enabled'):
        return importlib.import_module(''.join(('outspline.plugins.', plugin,
                                                                    '_api')))


def bind_to_external_nudge(handler, bind=True):
    return coreaux.events.external_nudge_event.bind(handler, bind)


def bind_to_uncaught_exception(handler, bind=True):
    return coreaux.events.uncaught_exception_event.bind(handler, bind)
