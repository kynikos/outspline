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

from tkinter import Tk, S, E
from tkinter import ttk as _ttk
import constants
import style
import menubar
import mainframe
import alarms
import menucommands

root = None


def initialize():
    global root
    root = Tk()
    
    style.initialize()
    
    root.title(constants._PROJECT_NAME)
    root.geometry(constants._ROOT_GEOMETRY)
    root.minsize(*constants._ROOT_MIN_SIZE)
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    
    root.protocol("WM_DELETE_WINDOW", menucommands.exit_)
    
    menubar.initialize(root)
    
    mainframe.initialize(root)
    
    alarms.alarmswindow = alarms.AlarmsWindow(root)
    
    _ttk.Sizegrip(root).grid(column=0, row=1, sticky=(S, E))
