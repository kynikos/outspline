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

from collections import OrderedDict as OD

data = (
    OD((
        ("enabled", "on"),
    )),
    OD((
        ("TreeIcons", (
            OD((
                ("symbol", "~"),
                ("color_valid", "#FF7E00"),
                ("color_broken", "#ED1C24"),
                ("color_target", "#0F52BA"),
                ("color_valid_and_target", "#FF7E00"),
                ("color_broken_and_target", "#ED1C24"),
            )),
            OD()
        )),
        ("Shortcuts", (
            OD((
                ("focus", ""),
                ("toggle", "Ctrl+~"),
            )),
            (),
        )),
        ("ExtendedShortcuts", (
            OD((
                ("focus", "n"),
                ("toggle", "Shift+n"),
            )),
            OD()
        )),
    ))
)

