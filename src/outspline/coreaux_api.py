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
import importlib
import threading

import outspline.components.main
import outspline.info as info
from coreaux.configuration import components, config
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


def get_standard_extension():
    return config('Save')['default_extension']


def get_root_directory():
    return coreaux.configuration._ROOT_DIR


def get_copyright_unicode():
    return coreaux.configuration._COPYRIGHT_UNICODE


def get_description():
    return coreaux.configuration._DESCRIPTION_2


def get_license():
    return coreaux.configuration._DISCLAIMER


def get_user_config_file():
    return coreaux.configuration.user_config_file


def get_main_component_info():
    return outspline.components.main


def get_components_info():
    return components


def get_enabled_installed_addons():
    return coreaux.addons.enabled_addons


def get_configuration():
    return config


def get_extension_configuration(extension):
    return config('Extensions')(extension)


def get_interface_configuration(interface):
    return config('Interfaces')(interface)


def get_plugin_configuration(plugin):
    return config('Plugins')(plugin)


def get_extension_bundled_data(extension, relpath):
    return get_bundled_data(["extensions", extension] + list(relpath))


def get_interface_bundled_data(interface, relpath):
    return get_bundled_data(["interfaces", interface] + list(relpath))


def get_plugin_bundled_data(plugin, relpath):
    return get_bundled_data(["plugins", plugin] + list(relpath))


def get_bundled_data(relpath):
    return os.path.join(coreaux.configuration.BUNDLED_DATA_DIR, *relpath)


def is_main_thread():
    return threading.current_thread().name == \
                                        coreaux.configuration.MAIN_THREAD_NAME


def get_core_info():
    return info.core


def import_extension_info(extension):
    return importlib.import_module(".".join(("outspline", "info", "extensions",
                                                                extension)))


def import_interface_info(interface):
    return importlib.import_module(".".join(("outspline", "info", "interfaces",
                                                                interface)))


def import_plugin_info(plugin):
    return importlib.import_module(".".join(("outspline", "info", "plugins",
                                                                    plugin)))


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
    # This event may be signalled in a separate thread
    return coreaux.events.uncaught_exception_event.bind(handler, bind)
