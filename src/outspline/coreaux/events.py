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

import inspect


class Event(object):
    def __init__(self):
        self.handlers = set()

    def bind(self, handler, bind=True):
        if bind:
            # Use a set to avoid duplicating bindings when closing and reopening
            # a database
            self.handlers.add(handler)
        else:
            self.handlers.discard(handler)

    def signal(self, **kwargs):
        for handler in self.handlers.copy():
            if inspect.isfunction(handler):
                handler(kwargs)
            # The object that bound the method may not exist any more
            elif inspect.ismethod(handler) and handler.__self__:
                handler(kwargs)
            else:
                self.handlers.discard(handler)

uncaught_exception_event = Event()
