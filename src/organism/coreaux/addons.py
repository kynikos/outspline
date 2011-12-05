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

import sys
import pkgutil
import os.path

import configfile

import configuration
import exceptions
from logger import log
from events import Event

addons_loaded_event = Event()


def load_config(section, folder):
    for p in pkgutil.iter_modules((os.path.join(configuration._ROOT_DIR,
                                                folder), )):
        if p[2]:
            configuration.config(section).make_subsection(p[1])
            configuration.config(section)(p[1]).add(os.path.join(
                                                       configuration._ROOT_DIR,
                                                       folder, p[1] + '.conf'))


def load_addon(folder, addon):
    if folder == 'extensions':
        section = 'Extensions'
        logname = 'extension'
    elif folder == 'interfaces':
        section = 'Interfaces'
        logname = 'interface'
    else:
        section = 'Plugins'
        logname = 'plugin'
    
    faddon = '.'.join((folder, addon))
    mfaddon = '.'.join(('organism', faddon))
    
    if mfaddon not in sys.modules:
        if addon in configuration.config(section).get_sections():
            if configuration.config(section)(addon).get_bool('enabled'):
                info = configfile.ConfigFile(os.path.join(
                                                       configuration._ROOT_DIR,
                                                       folder, addon,
                                                       addon + '.info'))
                
                deps = []
                opts = []
                for o in info.get_options():
                    if o[:10] == 'dependency':
                        deps.append(info[o])
                    elif o[:19] == 'optional_dependency':
                        opts.append(info[o])
                
                for d in deps:
                    p = d.split('.')
                    try:
                        load_addon(p[0], p[1])
                    except exceptions.AddonDisabledError:
                        log.warning('Dependency for ' + faddon +
                                    ' not found: ' + d)
                        # Disable the addon in the configuration to prevent
                        # the following bug: an enabled addon is activated
                        # since all its dependencies are enabled; that addon
                        # also has an optional dependency which is also enabled
                        # and activated; this optional dependency, though, has
                        # a dependency which is not enabled, so it is not
                        # imported by this load_addon() function; however,
                        # since in the configuration it is enabled, it's
                        # imported by the main addon anyway with
                        # coreaux_api.import_extension_api(), thus breaking
                        # the application, since the dependency for the
                        # optional dependency is still missing
                        # Note that this change won't be written in the
                        # configuration file, since it's updated with
                        # config.export_add()
                        configuration.config(section)(addon)['enabled'
                                                               ] = 'off'
                        # Raise AddonDisabledError explicitly because
                        # otherwise it's caught and ignored in start_addons()
                        raise
                        # Note that AddonNotFound instead is never caught and
                        # will always terminate the program
                
                for o in opts:
                    p = o.split('.')
                    try:
                        load_addon(p[0], p[1])
                    except exceptions.AddonNotFoundError:
                        log.debug('Optional dependency for ' + faddon +
                                                            ' not found: ' + o)
                    except exceptions.AddonDisabledError:
                        log.debug('Optional dependency for ' + faddon +
                                                             ' disabled: ' + o)
                
                log.info('Load ' + logname + ': ' + addon)
                
                # ext = __import__(mfaddon) somehow doesn't work
                __import__(mfaddon)
                mod = sys.modules[mfaddon]
                
                # Interfaces must have a main() fnuction
                if hasattr(mod, 'main') or folder == 'interfaces':
                    mod.main()
            else:
                raise exceptions.AddonDisabledError()
        else:
            raise exceptions.AddonNotFoundError()


def start_addons():
    # Use a tuple because a simple dictionary doesn't keep sequence order
    t = (('Extensions', 'extensions'),
         ('Interfaces', 'interfaces'),
         ('Plugins', 'plugins'))
    
    for p in t:
        section = p[0]
        folder = p[1]
        load_config(section, folder)
        for pkg in configuration.config(section).get_sections():
            try:
                load_addon(folder, pkg)
            except exceptions.AddonDisabledError:
                log.debug(folder + '.' + pkg + ' is disabled')
    
    addons_loaded_event.signal()


def start_interface():
    interface = None
    
    for i in configuration.config('Interfaces').get_sections():
        if configuration.config('Interfaces')(i).get_bool('enabled'):
            # Exactly one interface must be enabled
            if interface:
                raise exceptions.MultipleInterfacesError()
            else:
                interface = sys.modules['organism.interfaces.' + i]
    
    # Exactly one interface must be enabled
    if interface:
        interface.loop()
    else:
        raise exceptions.InterfaceNotFoundError()


def get_addons_info(disabled=True):
    # Do not use a global info, because for example some addons may be disabled
    # by load_addon()
    info = configfile.ConfigFile({}, inherit_options=False)
    for t in ('Extensions', 'Interfaces', 'Plugins'):
        info.make_subsection(t)
        for a in configuration.config(t).get_sections():
            if disabled or configuration.config(t)(a).get_bool('enabled'):
                info(t).make_subsection(a)
                info(t)(a).add(os.path.join(configuration._ROOT_DIR, t.lower(),
                                            a, a + '.info'))
    return info


def main():
    start_addons()
    configuration.config.export_add(configuration.user_config_file)
    start_interface()
    log.debug('Organism exited successfully')
