# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

from collections import OrderedDict as OD

data = (
    OD(),
    OD((
        ("Log", (
            OD((
                ("log_level_stdout", "1"),
                ("log_level_file", "0"),
                ("log_file", "~/.config/outspline/outspline.log"),
            )),
            OD()
        )),
        ("Save", (
            OD((
                ("default_extension", "osl"),
            )),
            OD()
        )),
        ("History", (
            OD((
                ("default_soft_limit", "60"),
                ("time_limit", "15"),
                ("hard_limit", "120"),
            )),
            OD()
        )),
        ("Extensions", (OD(), OD())),
        ("Interfaces", (OD(), OD())),
        ("Plugins", (OD(), OD())),
    ))
)
