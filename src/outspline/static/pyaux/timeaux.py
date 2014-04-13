# pyaux
# Copyright (C) 2013-2014 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of pyaux.
#
# pyaux is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyaux is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyaux.  If not, see <http://www.gnu.org/licenses/>.

import time as time_


class UTCOffset(object):
    """
    Tools for computing UTC time offsets.
    """
    def __init__(self):
        """
        Instantiating the class is recommended if computing offsets for several
        timestamps in the same timezone.
        """
        if time_.daylight == 0:
            self.compute = self._compute_fixed
        else:
            self.compute = self._compute_variable

    def compute(self, timestamp):
        """
        Return the local UTC offset for the given timestamp, also taking DST
        into account.
        """
        # This is a virtual method whose algorithm is instantiated with the
        # constructor
        pass

    @classmethod
    def compute2(cls, timestamp):
        """
        This static method is like 'compute' without optimizations, and is
        recommended for isolated time offset computations.
        """
        return cls._compute_variable(timestamp)

    @classmethod
    def _compute_fixed(cls, timestamp):
        return time_.timezone

    @classmethod
    def _compute_variable(cls, timestamp):
        if time_.localtime(timestamp).tm_isdst == 0:
            return time_.timezone
        else:
            return time_.altzone

    def compute_current(self):
        """
        Return the current local UTC offset, also taking DST into account.
        """
        return self.compute(time_.time())

    @classmethod
    def compute2_current(cls):
        """
        This static method is like 'compute2' without optimizations, and is
        recommended for isolated time offset computations.
        """
        return cls._compute_variable(time_.time())
