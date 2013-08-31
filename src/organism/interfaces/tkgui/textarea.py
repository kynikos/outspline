# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import tkinter as _tk
from tkinter import N, E, S, W
import notebook
import editor
import items

textareas = {}


class TextArea():
    item = None
    area = None
    
    def __init__(self, item, text):
        # Notare che cut copy e paste nell'area di testo funzionano già **********
        #   con CTRL+X, C e V
        #   BUG: Se si tenta di incollare del testo su un testo selezionato,
        #     il testo selezionato non viene sostituito, ma il testo copiato
        #     viene incollato dopo il testo selezionato
        self.item = item
        self.area = _tk.Text(editor.tabs[item].frame, wrap='none', undo=True)
        
        area = self.area
        area.grid(column=0, row=0, sticky=(N, E, S, W))
        area.insert('1.0', text)
        area.edit_modified(False)
        area.edit_reset()

    def is_modified(self):
        if self.area.edit_modified():
            return True
        else:
            return False

    def apply(self):
        text = self.area.get('1.0', 'end-1c')
        return({'text': text})

    def refresh_mod_state(self):
        item = self.item
        title = items.Item.make_title(self.area.get('1.0', '1.end'))
        items.items[item].set(text=title)
        notebook.notebook_r.tab(editor.tabs[item].frame, text=title)
        self.area.edit_modified(False)

    def undo(self):
        try:
            self.area.edit_undo()
        except _tk.TclError:
            pass
    
    def redo(self):
        try:
            self.area.edit_redo()
        except _tk.TclError:
            pass

    def select_all(self):
        # Credo che prima bisogni cancellare il contenuto precedente di sel ******
        self.area.tag_add('sel', '1.0', 'end')
