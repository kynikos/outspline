# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import inspect


class Event():
    handlers = None
    
    def __init__(self):
        self.handlers = {}
    
    def bind(self, handler, bind=True):
        if bind:
            # Use a dictionary to avoid duplicating bindings when closing and
            # reopening a database
            self.handlers[handler] = None
        elif handler in self.handlers:
            del self.handlers[handler]
    
    def signal(self, **kwargs):
        for handler in tuple(self.handlers.copy()):
            if inspect.isfunction(handler):
                handler(kwargs)
            # The object that bound the method could not exist any longer
            elif inspect.ismethod(handler) and handler.__self__:
                handler(kwargs)
            else:
                del self.handlers[handler]

uncaught_exception_event = Event()
