# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
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
import databases
import queries
import notebook
import textarea
import scheduler
import msgboxes
import items
import timer

tabs = {}


class Editor():
    filename = None
    id_ = None
    item = None
    frame = None
    
    def __init__(self, item):
        self.filename = items.items[item].get_filename()
        self.id_ = items.items[item].get_id()
        self.item = item
        self.frame = _ttk.Frame(notebook.notebook_r)
        
        frame = self.frame
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
    
    def _post_init(self):
        filename = self.filename
        id_ = self.id_
        item = self.item
        
        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_editor, (id_, ))
        text = cursor.fetchone()['I_text']
        databases.dbs[filename].connection.give(qconn)
        title = items.Item.make_title(text)
        
        textarea.textareas[item] = textarea.TextArea(item, text)
        scheduler.Scheduler.open(item)
        
        notebook.notebook_r.add(self.frame, padding=(0, 3, 0, 0), text=title)
    
    @classmethod
    def open(cls, item):
        global tabs
        if item not in tabs:
            tabs[item] = cls(item)
            tabs[item]._post_init()
        notebook.notebook_r.select(tabs[item].frame)

    def apply(self, textbool=None, schedbool=None):
        item = self.item
        if textbool == None:
            textbool = textarea.textareas[item].is_modified()
        if schedbool == None:
            schedbool = scheduler.panels[item].is_modified()
        kwargs = {}
        if textbool:
            kwargs.update(textarea.textareas[item].apply())
        if schedbool:
            kwargs.update(scheduler.panels[item].apply())
        if textbool or schedbool:
            filename = items.items[item].get_filename()
            id_ = items.items[item].get_id()
            group = databases.memory.get_next_history_group()
            items.items[items.Item.make_tree_id(filename, id_)].update(group,
                                                                      **kwargs)
        if textbool:
            textarea.textareas[item].refresh_mod_state()
        if schedbool:
            timer.refresh_timer()
            scheduler.panels[item].refresh_originals()

    def close_if_needed(self, message=None):
        tab = self.frame
        notebook.notebook_r.select(tab)
        if message == 'save_db_as' and self.close():
            return True
        elif (message == 'cut_item' and msgboxes.close_tab_cut()) or\
             (message == 'delete_item' and msgboxes.close_tab_delete()) or\
             (message == 'undo/redo' and msgboxes.close_tab_history()):
            self.close(ask=False)
            return True
        else:
            return False

    def close(self, ask=True):
        global tabs
        item = self.item
        if ask:
            textbool = textarea.textareas[item].is_modified()
            schedbool = scheduler.panels[item].is_modified()
            if textbool or schedbool:
                save = msgboxes.close_tab_ask()
                if save == True:
                    self.apply(textbool, schedbool)
                    del textarea.textareas[item]
                    del scheduler.panels[item]
                elif save == None:
                    return False
        notebook.notebook_r.forget(self.frame)
        del tabs[item]
        return True
