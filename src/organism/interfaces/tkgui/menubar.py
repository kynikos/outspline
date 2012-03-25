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
import constants
import development
from menucommands import *

menubar = None

# Cliccando su una voce cascade un'altra volta (dopo averla già ******************
#     aperta) bisognerebbe che si richiudesse
# Settare i menu specifici per Windows e Mac OS X ********************************


def initialize(root):
    global menubar
    
    # Remove dashed line from menus
    root.option_add('*tearOff', _tk.FALSE)
    
    menubar = _tk.Menu(root)
    
    root['menu'] = menubar
    
    menu_file = _tk.Menu(menubar)
    menubar.add_cascade(menu=menu_file,
                        label='File',
                        underline=0)
    menu_file.add_command(label='New database...',
                          command=new_database,
                          underline=0)
    menu_file.add_command(label='Open database...',
                          command=open_database,
                          underline=0)
    menu_file.add_separator()
    menu_file.add_command(label='Save database',
                          command=save_database,
                          underline=0)
    menu_file.add_command(label='Save database as...',
                          command=save_database_as,
                          underline=0)
    menu_file.add_command(label='Save all databases',
                          command=save_all_databases,
                          underline=0)
    menu_file.add_command(label='Create backup...',
                          underline=0,
                          state='disabled')
    menu_file.add_command(label='Export to text file...',
                          underline=0,
                          state='disabled')
    menu_file.add_separator()
    menu_file.add_command(label='Close database',
                          command=close_database,
                          underline=0)
    menu_file.add_command(label='Close all databases',
                          command=close_all_databases,
                          underline=0)
    menu_file.add_command(label='Exit',
                          command=exit_,
                          underline=0)
    
    menu_tree = _tk.Menu(menubar)
    menubar.add_cascade(menu=menu_tree,
                        label='Tree',
                        underline=0)
    menu_tree.add_command(label='Undo tree',
                          command=undo_tree,
                          underline=0)
    menu_tree.add_command(label='Redo tree',
                          command=redo_tree,
                          underline=0)
    menu_tree.add_separator()
    menu_tree.add_command(label='Create child',
                          command=create_child,
                          underline=7)
    menu_tree.add_command(label='Create sibling',
                          command=create_sibling,
                          underline=7)
    menu_tree.add_separator()
    menu_tree.add_command(label='Cut items',
                          command=cut_items,
                          underline=2)
    menu_tree.add_command(label='Copy items',
                          command=copy_items,
                          underline=3)
    menu_tree.add_command(label='Paste items as children',
                          command=paste_items_as_children,
                          underline=0)
    menu_tree.add_command(label='Paste items as siblings',
                          command=paste_items_as_siblings,
                          underline=1)
    menu_tree.add_separator()
    menu_tree.add_command(label='Move item up',
                          command=move_item_up,
                          underline=0)
    menu_tree.add_command(label='Move item down',
                          command=move_item_down,
                          underline=2)
    menu_tree.add_command(label='Move item to parent',
                          command=move_item_to_parent,
                          underline=1)
    menu_tree.add_separator()
    menu_tree.add_command(label='Edit item',
                          command=edit_item,
                          underline=0)
    menu_tree.add_command(label='Search...',
                          underline=0,
                          state='disabled')
    menu_tree.add_separator()
    menu_tree.add_command(label='Delete items',
                          command=delete_items,
                          underline=0)
    
    menu_edit = _tk.Menu(menubar)
    menubar.add_cascade(menu=menu_edit,
                        label='Edit',
                        underline=0)
    menu_edit.add_command(label='Undo',
                          command=undo_text,
                          underline=0)
    menu_edit.add_command(label='Redo',
                          command=redo_text,
                          underline=0)
    menu_edit.add_separator()
    menu_edit.add_command(label='Select all',
                          command=select_all_text,
                          underline=0)
    menu_edit.add_command(label='Cut',
                          command=cut_text,
                          underline=0)
    menu_edit.add_command(label='Copy',
                          command=copy_text,
                          underline=0)
    menu_edit.add_command(label='Paste',
                          command=paste_text,
                          underline=0)
    menu_edit.add_separator()
    menu_edit.add_command(label='Find/Replace...',
                          underline=0,
                          state='disabled')
    menu_compare = _tk.Menu(menu_edit)
    menu_edit.add_cascade(menu=menu_compare,
                          label='Compare',
                          underline=0)
    menu_compare.add_command(label='Two items',
                             underline=0,
                             state='disabled')
    menu_compare.add_command(label='Editor with item',
                             underline=0,
                             state='disabled')
    menu_compare.add_command(label='Editor with original',
                             underline=0,
                             state='disabled')
    menu_edit.add_separator()
    menu_edit.add_command(label='Apply',
                          command=apply_tab,
                          underline=0)
    menu_edit.add_command(label='Apply all',
                          command=apply_all_tabs,
                          underline=0)
    menu_edit.add_separator()
    menu_edit.add_command(label='Close',
                          command=close_tab,
                          underline=0)
    menu_edit.add_command(label='Close all',
                          command=close_all_tabs,
                          underline=0)
    
    menu_view = _tk.Menu(menubar)
    menubar.add_cascade(menu=menu_view,
                        label='View',
                        underline=0)
    menu_view.add_command(label='Show alarms',
                          command=show_alarms,
                          underline=0)
    menu_view.add_command(label='Show history',
                          underline=0,
                          state='disabled')
    menu_view.add_command(label='Show log',
                          underline=0,
                          state='disabled')
    menu_view.add_separator()
    menu_view.add_command(label='Preferences',
                          underline=0,
                          state='disabled')
    
    menu_development = _tk.Menu(menubar)
    menubar.add_cascade(menu=menu_development,
                        label='Development',
                        underline=0)
    menu_development.add_command(label='Populate tree',
                                 command=development.populate_tree,
                                 underline=0)
    menu_development.add_command(label='Print tables',
                                 command=development.print_db,
                                 underline=0)
    
    menu_help = _tk.Menu(menubar,
                         name='help')
    menubar.add_cascade(menu=menu_help,
                        label='Help',
                        underline=0)
    menu_help.add_command(label='Report bugs...',
                          underline=0,
                          state='disabled')
    menu_help.add_command(label='About {}'.format(constants._PROJECT_NAME),
                          underline=0,
                          state='disabled')
    
    # ****************************************************************************
    """# Mac OS X
    apple = Menu(menubar, name='apple')
    help = Menu(menubar, name='help')
    menubar.add_cascade(menu=apple)
    menubar.add_cascade(menu=help)
    
    # Windows
    sysmenu = Menu(menubar, name='system')
    menubar.add_cascade(menu=sysmenu)
    """
