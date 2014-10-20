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

import configuration
import exceptions
from logger import log


def load_addon(faddon, reqversion, tablenames):
    '''
    Poss. cases | BASE               | DEPENDENCY         | OPTIONAL
    ------------+--------------------+--------------------+--------------------
    NOT FOUND   | impossible         | critical exception | debug message
    ------------+--------------------+--------------------+--------------------
    DISABLED    | debug message      | critical exception | debug message
    ------------+--------------------+--------------------+--------------------
    VERSION     | impossible         | critical exception | critical exception
    ------------+--------------------+--------------------+--------------------
    TABLES      | critical exception | critical exception | critical exception
    '''
    try:
        folder, addon = faddon.split('.')
    except ValueError:
        # Check core version

        # Get only the major version number
        instversion = int(configuration.info('Core').get_float('version'))

        if reqversion is not False and instversion != reqversion:
            raise exceptions.AddonVersionError(instversion)
    else:
        section, logname = {
            'extensions': ('Extensions', 'extension'),
            'interfaces': ('Interfaces', 'interface'),
            'plugins': ('Plugins', 'plugin'),
        }[folder]

        mfaddon = '.'.join(('outspline', faddon))

        # An addon may list a dependency that is not installed
        # This check must be done before the other ones, in fact if the addon
        # is not installed it's impossible to read its info
        if addon not in configuration.config(section).get_sections():
            raise exceptions.AddonNotFoundError()

        # This check must be done before the version or the provided tables
        # ones, in fact if an addon is disabled these problems shouldn't matter
        if not configuration.config(section)(addon).get_bool('enabled'):
            raise exceptions.AddonDisabledError()

        info = configuration.info(section)(addon)

        # Get only the major version number
        # This version check must be done before the 'mfaddon not in
        # sys.modules' one, otherwise it's not always performed; for example
        # two different addons may require the same addon with different
        # versions, and if the first one required the correct version, when
        # checking the second one no exception would be raised
        instversion = int(info.get_float('version'))

        if reqversion is not False and instversion != reqversion:
            raise exceptions.AddonVersionError(instversion)

        # This check must be done after the version one, see the comment there
        # for the reason
        if mfaddon not in sys.modules:
            if section == 'Extensions':
                ptables = {table: faddon for table in info['provides_tables'
                                                        ].split(' ') if table}
                test = [table for table in set(tablenames) & set(ptables)
                                        if tablenames[table] != ptables[table]]

                if test:
                    raise exceptions.ExtensionProvidedTablesError(test,
                                        [tablenames[table] for table in test])

                tablenames.update(ptables)

            try:
                sdeps = info['dependencies']
            except KeyError:
                pass
            else:
                for sdep in sdeps.split(' '):
                    dep, ver = sdep.rsplit(".", 1)

                    try:
                        load_addon(dep, int(ver), tablenames=tablenames)
                    # If I wanted to silently disable an addon in case one of
                    # its dependencies is not satisfied (not found,
                    # disabled...) I should disable the addon in the
                    # configuration to prevent the following bug: an enabled
                    # addon is activated since all its dependencies are
                    # enabled; that addon also has an optional dependency which
                    # is also enabled and activated; this optional dependency,
                    # though, has a dependency which is not enabled, so it is
                    # not imported by this load_addon() function; however,
                    # since in the configuration it is enabled, it's imported
                    # by the main addon anyway with
                    # coreaux_api.import_optional_extension_api(), thus
                    # breaking the application, since the dependency for the
                    # optional dependency is still missing
                    # Note that this change won't be written in the
                    # configuration file, since it's updated with
                    # config.export_add()
                    #except ...:
                    #    configuration.config(section)(addon)['enabled'] = 'off'
                    except exceptions.AddonNotFoundError:
                        log.error(faddon + ' depends on ' + dep +
                                            ' which however cannot be found')
                        # Raise a different exception, otherwise it may be
                        # caught by start_addons()
                        raise exceptions.AddonDependencyError()
                    except exceptions.AddonDisabledError:
                        log.error(faddon + ' depends on ' + dep +
                                                ' which however is disabled')
                        # Raise a different exception, otherwise it will be
                        # caught by start_addons()
                        raise exceptions.AddonDependencyError()
                    except exceptions.AddonVersionError as err:
                        log.error(faddon + ' depends on ' + dep + ' ' + ver +
                                ' which however is installed with version ' +
                                str(err.version))
                        # Raise a different exception, otherwise it may be
                        # caught by start_addons()
                        raise exceptions.AddonDependencyError()
                    except exceptions.ExtensionProvidedTablesError as err:
                        log.error(faddon + ' depends on ' + dep + ' which '
                                'provides tables ' + ', '.join(err.tables) +
                                ' that are already provided by ' +
                                ', '.join(err.extensions))
                        # Raise a different exception, otherwise it will be
                        # caught by start_addons()
                        raise exceptions.AddonDependencyError()

            try:
                sopts = info['optional_dependencies']
            except KeyError:
                pass
            else:
                for sopt in sopts.split(' '):
                    opt, ver = sopt.rsplit(".", 1)

                    try:
                        load_addon(opt, int(ver), tablenames=tablenames)
                    except exceptions.AddonNotFoundError:
                        log.debug(faddon + ' optionally depends on ' + opt +
                                            ' which however cannot be found')
                    except exceptions.AddonDisabledError:
                        log.debug(faddon + ' optionally depends on ' + opt +
                                                ' which however is disabled')
                    except exceptions.AddonVersionError as err:
                        log.error(faddon + ' optionally depends on ' + opt +
                                ' ' + ver + ' which however is '
                                'installed with version ' + str(err.version))
                        # Just crash the application, in fact it's not easy to
                        # handle this case, as the same addon may be required
                        # by another addon with the correct version, but still
                        # this addon should *not* use this dependency
                        # Raise a different exception, otherwise it will be
                        # caught by start_addons()
                        raise exceptions.AddonDependencyError()
                    except exceptions.ExtensionProvidedTablesError as err:
                        log.error(faddon + ' optionally depends on ' + opt +
                                            ' which provides tables ' +
                                            ', '.join(err.tables) +
                                            ' that are already provided by ' +
                                            ', '.join(err.extensions))
                        # Just crash the application, in fact it's not easy to
                        # handle this case, as the same addon may be required
                        # by another addon with the correct version, but still
                        # this addon should *not* use this dependency
                        # Raise a different exception, otherwise it will be
                        # caught by start_addons()
                        raise exceptions.AddonDependencyError()

            mod = importlib.import_module(mfaddon)

            # Interfaces must have a main() fnuction
            if hasattr(mod, 'main') or folder == 'interfaces':
                mod.main()

            log.info('Loaded ' + logname + ': ' + addon)


def start_addons():
    info = configuration.info('Core')

    tablenames = {table: 'core' for table in info['provides_tables'].split(' ')
                                                                    if table}

    # Use a tuple because a simple dictionary doesn't keep sequence order
    for section, folder in (('Extensions', 'extensions'),
                            ('Interfaces', 'interfaces'),
                            ('Plugins', 'plugins')):
        # Don't use configuration.config to prevent the following bug: an
        # optional component is installed, then Outspline is run, then the
        # optional component is uninstalled; its configuration would still be
        # read in configuration.config, so this function would try to load an
        # addon that is not installed anymore; use configuration.info instead
        for pkg in configuration.info(section).get_sections():
            faddon = folder + '.' + pkg

            try:
                load_addon(faddon, False, tablenames)
            except exceptions.AddonDisabledError:
                log.debug(faddon + ' is disabled')
            except exceptions.ExtensionProvidedTablesError as err:
                log.error(faddon +  ' provides tables ' +
                                            ', '.join(err.tables) +
                                            ' which are already provided by ' +
                                            ', '.join(err.extensions))
                raise
            # If wanting to catch other exceptions here that come only from
            # base addons (not propagated from dependencies), remember to raise
            # different exceptions for any exception that is caught in
            # load_addon() (i.e. don't propagate the same exception, use e.g.
            # exceptions.AddonDependencyError)


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


def main():
    start_addons()
    configuration.export_configuration(log)
    start_interface()
    log.info('Outspline exited successfully')
