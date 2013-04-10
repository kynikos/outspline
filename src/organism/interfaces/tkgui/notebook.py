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

from tkinter import ttk as _ttk
import tree
import tasklist
import calendarw
import editor
import msgboxes

notebook_l = None
notebook_r = None

# Pulsanti di chiusura sulle tab? ************************************************
#   in alternativa per chiuderle si potrebbe fare doppio click
#   il doppio click potrebbe invece essere riservato alla selezione della item
#     corrispondente nel tree (vedi bug più sotto)


def initialize(parent):
    global notebook_l
    global notebook_r
    notebook_l = _ttk.Notebook(parent)
    notebook_r = _ttk.Notebook(parent)
    
    tree.initialize(notebook_l)
    tasklist.initialize(notebook_l)
    calendarw.initialize(notebook_r)
    
    parent.add(notebook_l)
    parent.add(notebook_r)


def select_tab(message=None):
    tabid = notebook_r.select()
    tab = notebook_r.nametowidget(tabid)
    for item in editor.tabs:
        if editor.tabs[item].frame is tab:
            return(item)
    else:
        if message == 'apply_tab':
            msgboxes.apply_tab_calendar()
        elif message == 'close_tab':
            msgboxes.close_tab_calendar()
        elif message == 'editor':
            msgboxes.editor_calendar()
        return False
