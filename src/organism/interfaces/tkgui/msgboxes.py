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

from tkinter import filedialog as _tkfile
from tkinter import messagebox as _tkmsg
import constants
import rootwindow


def create_db_ask():
    return _tkfile.asksaveasfilename(defaultextension='.' + constants._FILE_EXT,
                      filetypes=(('{} database'.format(constants._PROJECT_NAME),
                               '*.' + constants._FILE_EXT), ('All files', '*')))


def create_db_open(filename):
    _tkmsg.showerror(title='Create database',
                     message='{} seems to be already open.'.format(filename),
                     detail='Please close the file before overwriting it.',
                     parent=rootwindow.root)


def open_db_ask():
    return _tkfile.askopenfilename(filetypes=(
                                 ('{} database'.format(constants._PROJECT_NAME),
                               '*.' + constants._FILE_EXT), ('All files', '*')))


def open_db_open(filename):
    _tkmsg.showerror(title='Open database',
                     message='{} seems to be already open.'.format(filename),
                     detail='Please close the file before reopening it.',
                     parent=rootwindow.root)


def save_db_none():
    _tkmsg.showerror(title='Save database',
                     message='You haven\'t selected any database.',
                     parent=rootwindow.root)


def save_db_dbs():
    _tkmsg.showerror(title='Save database',
                     message='You cannot save multiple databases at once.',
                     parent=rootwindow.root)


def close_db_ask(filename):
    return _tkmsg.askyesnocancel(title='Save database',
                              message='Do you want to save {} before closing?'
                                                            ''.format(filename),
                              parent=rootwindow.root,
                              default='cancel')


def close_db_none():
    _tkmsg.showerror(title='Close database',
                     message='You haven\'t selected any database.',
                     parent=rootwindow.root)


def close_db_dbs():
    _tkmsg.showerror(title='Close database',
                     message='You cannot close multiple databases at once.',
                     parent=rootwindow.root)


def create_child_many():
    _tkmsg.showerror(title='Create child',
                     message='You have selected too many items.',
                     parent=rootwindow.root)


def create_child_none():
    _tkmsg.showerror(title='Create child',
                     message='You haven\'t selected any item.',
                     parent=rootwindow.root)


def create_sibling_root():
    _tkmsg.showerror(title='Create sibling',
                     message='You cannot create a sibling for the root item.',
                     detail='Please create a new database instead.',
                     parent=rootwindow.root)


def create_sibling_many():
    _tkmsg.showerror(title='Create sibling',
                     message='You have selected too many items.',
                     parent=rootwindow.root)


def create_sibling_none():
    _tkmsg.showerror(title='Create sibling',
                     message='You haven\'t selected any item.',
                     parent=rootwindow.root)


def copy_items_root():
    _tkmsg.showerror(title='Copy/Cut items',
                     message='The root item cannot be copied nor cut.',
                     parent=rootwindow.root)


def copy_items_dbs():
    _tkmsg.showerror(title='Copy/Cut items',
                     message='You cannot copy nor cut items from multiple '
                                                                   'databases.',
                     parent=rootwindow.root)


def paste_items_many():
    _tkmsg.showerror(title='Paste items',
                     message='You have selected too many items.',
                     parent=rootwindow.root)


def paste_items_none():
    _tkmsg.showerror(title='Paste items',
                     message='You haven\'t selected any item.',
                     parent=rootwindow.root)


def paste_items_root():
    _tkmsg.showerror(title='Paste items',
                     message='You cannot paste as a sibling of the root item.',
                     parent=rootwindow.root)


def move_item_many():
    _tkmsg.showerror(title='Move item',
                     message='You have selected too many items.',
                     parent=rootwindow.root)


def move_item_none():
    _tkmsg.showerror(title='Move item',
                     message='You haven\'t selected any item.',
                     parent=rootwindow.root)


def move_item_root():
    _tkmsg.showerror(title='Move item',
                     message='The root item has no parent.',
                     parent=rootwindow.root)


def edit_item_none():
    _tkmsg.showerror(title='Edit item',
                     message='You haven\'t selected any item.',
                     parent=rootwindow.root)


def edit_item_many():
    _tkmsg.showerror(title='Edit item',
                     message='You have selected too many items.',
                     parent=rootwindow.root)


def edit_item_root():
    _tkmsg.showerror(title='Edit item',
                     message='You cannot edit the root item.',
                     parent=rootwindow.root)


def delete_items_root():
    _tkmsg.showerror(title='Delete items',
                     message='You cannot delete the root item.',
                     parent=rootwindow.root)


def delete_items_dbs():
    _tkmsg.showerror(title='Delete items',
                     message='You cannot delete items from multiple databases.',
                     parent=rootwindow.root)


def delete_items_confirm(n):
    return _tkmsg.askokcancel(title='Delete items',
                              message='{} item(s) is/are going to be deleted.'
                                                                   ''.format(n),
                              parent=rootwindow.root,
                              default='cancel',
                              icon='warning')


def apply_tab_calendar():
    _tkmsg.showerror(title='Apply editor',
                     message='You must select an item editor.',
                     parent=rootwindow.root)


def close_tab_calendar():
    _tkmsg.showerror(title='Close editor',
                     message='You must select an item editor.',
                     parent=rootwindow.root)


def editor_calendar():
    _tkmsg.showerror(title='Editor',
                     message='You must select an item editor.',
                     parent=rootwindow.root)


def close_tab_ask():
    return _tkmsg.askyesnocancel(title='Close editor',
                              message='Do you want to apply the changes to the '
                                             ' item before closing the editor?',
                              parent=rootwindow.root,
                              default='cancel')


def close_tab_cut():
    return _tkmsg.askokcancel(title='Cut items',
                              message='This editor must be closed without '
                                                   'saving in order to cut the '
                                                             'respective item.',
                              parent=rootwindow.root,
                              default='cancel')


def close_tab_delete():
    return _tkmsg.askokcancel(title='Delete items',
                              message='This editor must be closed without '
                                                'saving in order to delete the '
                                                             'respective item.',
                              parent=rootwindow.root,
                              default='cancel')


def close_tab_history():
    return _tkmsg.askokcancel(title='Undo/Redo',
                              message='This editor must be closed without '
                                                 'saving in order to undo/redo '
                                                           ' the last command.',
                              parent=rootwindow.root,
                              default='cancel')
