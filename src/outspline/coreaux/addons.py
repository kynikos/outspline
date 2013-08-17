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
import pkgutil
import os.path
import importlib

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


def load_addon(aname, reqversion):
    try:
        folder, addon = aname.split('.')
    except ValueError:
        # Check core version
        info = configfile.ConfigFile(os.path.join(configuration._ROOT_DIR,
                                                        'coreaux', 'core.info'))
        # Get only the major version number
        if int(info.get_float('version')) != reqversion:
            raise exceptions.AddonVersionError()
    else:
        section, logname = {
            'extensions': ('Extensions', 'extension'),
            'interfaces': ('Interfaces', 'interface'),
            'plugins': ('Plugins', 'plugin'),
        }[folder]

        faddon = '.'.join((folder, addon))
        mfaddon = '.'.join(('outspline', faddon))

        # An addon may list a dependency that is not installed
        # This check must be done before the other ones, in fact if the addon is
        # not installed it's impossible to read its info
        if addon in configuration.config(section).get_sections():
            info = configfile.ConfigFile(os.path.join(
                   configuration._ROOT_DIR, folder, addon, addon + '.info'))

            # Get only the major version number
            # This version check must be done before the 'mfaddon not in
            # sys.modules' one, otherwise it's not always performed; for example
            # two different addons may require the same addon with different
            # versions, and if the first one required the correct version, when
            # checking the second one no exception would be raised
            if reqversion is False or int(info.get_float('version')) == \
                                                                     reqversion:
                # This check must be done before the enabled/disabled one, in
                # order to prevent duplicated log messages in case of disabled
                # addons optionally required by more than one addon
                if mfaddon not in sys.modules:
                    if configuration.config(section)(addon).get_bool('enabled'):
                        deps = []
                        opts = []

                        for o in info.get_options():
                            osplit = info[o].split(' ')

                            if o[:10] == 'dependency':
                                deps.append((osplit[0], int(osplit[-1])))
                            elif o[:19] == 'optional_dependency':
                                opts.append((osplit[0], int(osplit[-1])))

                        for d in deps:
                            try:
                                load_addon(*d)
                            except exceptions.AddonNotFoundError:
                                log.error('Dependency for ' + faddon +
                                                          ' not found: ' + d[0])
                                # Note that AddonNotFoundError is never caught and
                                # will always terminate the program
                                raise
                            except exceptions.AddonDisabledError:
                                log.warning('Dependency for ' + faddon +
                                                           ' disabled: ' + d[0])
                                # Disable the addon in the configuration to
                                # prevent the following bug: an enabled addon is
                                # activated since all its dependencies are
                                # enabled; that addon also has an optional
                                # dependency which is also enabled and
                                # activated; this optional dependency, though,
                                # has a dependency which is not enabled, so it
                                # is not imported by this load_addon() function;
                                # however, since in the configuration it is
                                # enabled, it's imported by the main addon
                                # anyway with
                                # coreaux_api.import_optional_extension_api(),
                                # thus breaking the application, since the
                                # dependency for the optional dependency is
                                # still missing
                                # Note that this change won't be written in the
                                # configuration file, since it's updated with
                                # config.export_add()
                                configuration.config(section)(addon)['enabled'
                                                                       ] = 'off'
                                # Propagate AddonDisabledError so it's caught in
                                # start_addons()
                                raise
                            except exceptions.AddonVersionError:
                                log.error('Dependency for ' + faddon +
                                    ' found with incompatible version: ' + d[0])
                                # Note that AddonVersionError is never caught
                                # and will always terminate the program
                                raise

                        for o in opts:
                            try:
                                load_addon(*o)
                            except exceptions.AddonNotFoundError:
                                log.debug('Optional dependency for ' + faddon +
                                                          ' not found: ' + o[0])
                            except exceptions.AddonVersionError:
                                log.debug('Optional dependency for ' + faddon +
                                    ' found with incompatible version: ' + o[0])
                            except exceptions.AddonDisabledError:
                                log.debug('Optional dependency for ' + faddon +
                                                           ' disabled: ' + o[0])

                        log.info('Load ' + logname + ': ' + addon)

                        mod = importlib.import_module(mfaddon)

                        # Interfaces must have a main() fnuction
                        if hasattr(mod, 'main') or folder == 'interfaces':
                            mod.main()
                    else:
                        raise exceptions.AddonDisabledError()
            else:
                raise exceptions.AddonVersionError()
        else:
            raise exceptions.AddonNotFoundError()


def start_addons():
    # Use a tuple because a simple dictionary doesn't keep sequence order
    for section, folder in (('Extensions', 'extensions'),
                            ('Interfaces', 'interfaces'),
                            ('Plugins', 'plugins')):
        load_config(section, folder)
        for pkg in configuration.config(section).get_sections():
            aname = folder + '.' + pkg

            try:
                load_addon(aname, False)
            except exceptions.AddonDisabledError:
                log.debug(aname + ' is disabled')

    addons_loaded_event.signal()


def start_interface():
    interface = None

    for i in configuration.config('Interfaces').get_sections():
        if configuration.config('Interfaces')(i).get_bool('enabled'):
            # Exactly one interface must be enabled
            if interface:
                raise exceptions.MultipleInterfacesError()
            else:
                interface = sys.modules['outspline.interfaces.' + i]

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
                # Let the normal exception be raised if the .info file is not
                # found
                info(t)(a).add(os.path.join(configuration._ROOT_DIR, t.lower(),
                                                                a, a + '.info'))
    return info


def main():
    start_addons()
    configuration.config.export_add(configuration.user_config_file)
    start_interface()
    log.info('Outspline exited successfully')
