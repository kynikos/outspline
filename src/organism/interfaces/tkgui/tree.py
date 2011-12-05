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
import msgboxes
import items

tree = None

# Implementare i comportamenti standard del tree *********************************
#   ad esempio cliccando su un elemento selezionato, si dovrebbe
#     deselezionare
#     vedi Treeview.selection_toggle()


def initialize(parent):
    global tree
    tree = _ttk.Treeview(parent, show='tree')
    parent.add(tree, padding=(0, 3, 0, 0), text='Tree')


def select(none=True, many=True, root=True, dbs=True, descendants=None,
                                                                 message=None):
    selection = tree.selection()
    if not none and len(selection) == 0:
        if message == 'close_db':
            msgboxes.close_db_none()
        elif message == 'create_child':
            msgboxes.create_child_none()
        elif message == 'create_sibling':
            msgboxes.create_sibling_none()
        elif message == 'edit_item':
            msgboxes.edit_item_none()
        elif message == 'move_item':
            msgboxes.move_item_none()
        elif message == 'paste_items':
            msgboxes.paste_items_none()
        elif message == 'save_db':
            msgboxes.save_db_none()
        return False
    elif not many and len(selection) > 1:
        if message == 'create_child':
            msgboxes.create_child_many()
        elif message == 'create_subling':
            msgboxes.create_sibling_many()
        elif message == 'edit_item':
            msgboxes.edit_item_many()
        elif message == 'move_item':
            msgboxes.move_item_many()
        elif message == 'paste_items':
            msgboxes.paste_items_many()
        return False
    elif not root or not dbs or descendants != None:
        filename = items.items[selection[0]].get_filename()
        for item in selection:
            if not root and not items.items[item].get_parent():
                if message == 'copy_items':
                    msgboxes.copy_items_root()
                elif message == 'create_sibling':
                    msgboxes.create_sibling_root()
                elif message == 'delete_items':
                    msgboxes.delete_items_root()
                elif message == 'edit_item':
                    msgboxes.edit_item_root()
                elif message == 'move_item':
                    msgboxes.move_item_root()
                elif message == 'paste_items':
                    msgboxes.paste_items_root()
                return False
            if descendants == False:
                for ancestor in items.items[item].get_ancestors():
                    if ancestor in selection:
                        items.items[item].remove_selection()
                        break
            elif descendants == True:
                for descendant in items.items[item].get_descendants():
                    items.items[descendant].add_selection()
            if not dbs and items.items[item].get_filename() != filename:
                if message == 'close_db':
                    msgboxes.close_db_dbs()
                elif message == 'copy_items':
                    msgboxes.copy_items_dbs()
                elif message == 'delete_items':
                    msgboxes.delete_items_dbs()
                elif message == 'save_db':
                    msgboxes.save_db_dbs()
                return False
    # Do not use else here
    selection = tree.selection()
    return selection
