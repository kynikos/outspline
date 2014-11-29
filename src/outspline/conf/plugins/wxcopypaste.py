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
        ("GlobalShortcuts", (
            OD((
                ("cut", "Ctrl+Shift+x"),
                ("copy", "Ctrl+Shift+c"),
                ("paste", "Ctrl+Shift+v"),
                ("paste_children", "Ctrl+Shift+b"),
            )),
            OD()
        )),
        ("ContextualShortcuts", (
            OD((
                ("cut", "x"),
                ("copy", "c"),
                ("paste_siblings", "v"),
                ("paste_children", "Shift+v"),
            )),
            OD()
        )),
    ))
)

