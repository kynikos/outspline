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

import tkinter as _tk
from tkinter import N, E, S, W
from tkinter import ttk as _ttk
import notebook

mainpanes = None


def initialize(parent):
    global mainpanes
    mainpanes = _ttk.Panedwindow(parent,
                                 orient=_tk.HORIZONTAL)
    mainpanes.grid(column=0,
                   row=0,
                   sticky=(N, E, S, W))

    notebook.initialize(mainpanes)
