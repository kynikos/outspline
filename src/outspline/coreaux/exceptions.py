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


class OutsplineError(Exception):
    pass


class AddonDisabledError(OutsplineError):
    pass


class AddonProvidedHistoryActionsError(OutsplineError):
    actions = None
    addons = None

    def __init__(self, actions, addons):
        self.actions = actions
        self.addons = addons
        OutsplineError.__init__(self)


class AddonProvidedTablesError(OutsplineError):
    tables = None
    addons = None

    def __init__(self, tables, addons):
        self.tables = tables
        self.addons = addons
        OutsplineError.__init__(self)


class AddonVersionError(OutsplineError):
    version = None

    def __init__(self, version):
        self.version = version
        OutsplineError.__init__(self)


class AddonNotFoundError(OutsplineError):
    pass


class AddonDependencyError(OutsplineError):
    pass


class MultipleInterfacesError(OutsplineError):
    pass


class InterfaceNotFoundError(OutsplineError):
    pass
