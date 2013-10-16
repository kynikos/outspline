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

import wx

from wxgui import rootw, editor, menubar, tree, databases


### DATABASE ###

def open_database(filename, startup=False):
    return databases.open_database(filename, startup=startup)


def get_open_databases():
    return databases.get_open_databases()


### EDITOR ###

def open_editor(filename, id_):
    return editor.Editor.open(filename, id_)


def get_textctrl(filename, id_):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)].area.area


def close_editor(filename, id_, ask='apply'):
    tab = editor.Editor.make_tabid(filename, id_)
    if tab in editor.tabs and not editor.tabs[tab].close(ask=ask):
        return False
    else:
        return True


def add_plugin_to_editor(filename, id_, caption):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)
                       ].add_plugin_panel(caption)


def add_window_to_plugin(filename, id_, fpanel, window):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)
                       ].add_plugin_window(fpanel, window)


def resize_foldpanelbar(filename, id_):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)].resize_fpb()


def collapse_panel(filename, id_, fpanel):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)
                       ].collapse_panel(fpanel)


def expand_panel(filename, id_, fpanel):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)
                       ].expand_panel(fpanel)


def set_editor_modified(filename, id_):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)].set_modified()


def add_editor_accelerators(filename, id_, accels):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)
                       ].add_accelerators(accels)


def bind_to_open_editor(handler, bind=True):
    return editor.open_editor_event.bind(handler, bind)


def bind_to_apply_editor(handler, bind=True):
    return editor.apply_editor_event.bind(handler, bind)


def bind_to_check_editor_modified_state(handler, bind=True):
    return editor.check_modified_state_event.bind(handler, bind)


def bind_to_close_editor(handler, bind=True):
    return editor.close_editor_event.bind(handler, bind)


def bind_to_open_textctrl(handler, bind=True):
    return editor.open_textctrl_event.bind(handler, bind)


def simulate_replace_editor_text(text):
    tab = wx.GetApp().nb_right.get_selected_editor()
    if tab:
        last = editor.tabs[tab].area.area.GetLastPosition()
        return editor.tabs[tab].area.area.Replace(0, last, text)
    else:
        return False


def simulate_apply_editor():
    return wx.GetApp().menu.edit.apply_tab(None)


def simulate_apply_all_editors():
    return wx.GetApp().menu.edit.apply_all_tabs(None)


def simulate_close_editor(ask='apply'):
    return wx.GetApp().menu.edit.close_tab(None, ask=ask)


def simulate_close_all_editors(ask='apply'):
    return wx.GetApp().menu.edit.close_all_tabs(None, ask=ask)


### MENUBAR ###

def get_menu():
    return wx.GetApp().menu


def insert_menu_main_item(title, before, menu):
    return wx.GetApp().menu.Insert(wx.GetApp().menu.FindMenu(before),
                                      menu, title)


def insert_menu_item(menu, pos, item, id_=wx.ID_ANY, help='', sep='none',
                     kind='normal', sub=None, icon=None):
    return wx.GetApp().menu.insert_item(menu, pos, item, id_, help, sep, kind,
                                        sub, icon)


def bind_to_reset_menu_items(handler, bind=True):
    return menubar.reset_menu_items_event.bind(handler, bind)


def bind_to_enable_tree_menus(handler, bind=True):
    return menubar.enable_tree_menus_event.bind(handler, bind)


def bind_to_enable_textarea_menus(handler, bind=True):
    return menubar.enable_textarea_menus_event.bind(handler, bind)


def bind_to_open_database(handler, bind=True):
    return databases.open_database_event.bind(handler, bind)


def bind_to_close_database(handler, bind=True):
    return databases.close_database_event.bind(handler, bind)


def bind_to_undo_tree(handler, bind=True):
    return menubar.undo_tree_event.bind(handler, bind)


def bind_to_redo_tree(handler, bind=True):
    return menubar.redo_tree_event.bind(handler, bind)


def bind_to_move_item(handler, bind=True):
    return menubar.move_item_event.bind(handler, bind)


def bind_to_delete_items(handler, bind=True):
    return menubar.delete_items_event.bind(handler, bind)


def simulate_create_database(filename):
    return wx.GetApp().menu.file.new_database(None, filename)


def simulate_open_database(filename):
    return wx.GetApp().menu.file.open_database(None, filename)


def simulate_save_database():
    return wx.GetApp().menu.file.save_database(None)


def simulate_save_all_databases():
    return wx.GetApp().menu.file.save_all_databases(None)


def simulate_close_database(no_confirm=False):
    return wx.GetApp().menu.file.close_database(None, no_confirm=no_confirm)


def simulate_close_all_databases(no_confirm=False):
    return wx.GetApp().menu.file.close_all_databases(None,
                                                          no_confirm=no_confirm)


def simulate_undo_tree(no_confirm=False):
    return wx.GetApp().menu.database.undo_tree(None, no_confirm=no_confirm)


def simulate_redo_tree(no_confirm=False):
    return wx.GetApp().menu.database.redo_tree(None, no_confirm=no_confirm)


def simulate_create_sibling():
    return wx.GetApp().menu.database.create_sibling(None)


def simulate_create_child():
    return wx.GetApp().menu.database.create_child(None)


def simulate_move_item_up():
    return wx.GetApp().menu.database.move_item_up(None)


def simulate_move_item_down():
    return wx.GetApp().menu.database.move_item_down(None)


def simulate_move_item_to_parent():
    return wx.GetApp().menu.database.move_item_to_parent(None)


def simulate_edit_item():
    return wx.GetApp().menu.database.edit_item(None)


def simulate_delete_items(no_confirm=False):
    return wx.GetApp().menu.database.delete_items(None, no_confirm=no_confirm)


### NOTEBOOKS ###

def select_database_tab_index(index):
    return wx.GetApp().nb_left.select_page(index)


def get_selected_database_tab_index():
    # Returns -1 if there's no tab
    return wx.GetApp().nb_left.get_selected_tab_index()


def get_active_database():
    return wx.GetApp().nb_left.get_selected_tab()


def get_right_nb():
    return wx.GetApp().nb_right


def select_editor_tab_index(index):
    return wx.GetApp().nb_right.select_page(index)


def get_selected_editor_tab_index():
    # Returns -1 if there's no tab
    return wx.GetApp().nb_right.get_selected_tab_index()


def get_active_editor():
    item = wx.GetApp().nb_right.get_selected_editor()
    tab = editor.tabs[item]
    return (tab.get_filename(), tab.get_id())


def get_active_editor_tag():
    return wx.GetApp().nb_right.get_selected_editor()


def get_open_editors_tab_indexes():
    return wx.GetApp().nb_right.get_open_editors()


def add_plugin_to_right_nb(window, caption, close=True):
    return wx.GetApp().nb_right.add_plugin(window, caption=caption,
                                              close=close)


### ROOTW ###

def get_main_frame():
    return wx.GetApp().root


def get_main_icon_bundle():
    return wx.GetApp().get_main_icon_bundle()


def is_shown():
    return wx.GetApp().root.IsShown()


def bind_to_menu(handler, button):
    return wx.GetApp().root.Bind(wx.EVT_MENU, handler, button)


def bind_to_exit_application(handler, bind=True):
    return rootw.exit_application_event.bind(handler, bind)


### TREE ###

def get_tree_selections(filename, none=True, many=True, descendants=None):
    return tree.dbs[filename].get_selections(none=none, many=many,
                                             descendants=descendants)


def append_item(filename, baseid, id_, text):
    label = tree.dbs[filename].make_item_title(text)
    base = tree.dbs[filename].find_item(baseid)
    return tree.dbs[filename].insert_item(base, 'append', label=label, id_=id_)


def insert_item_after(filename, baseid, id_, text):
    label = tree.dbs[filename].make_item_title(text)
    base = tree.dbs[filename].find_item(baseid)
    return tree.dbs[filename].insert_item(base, 'after', label=label, id_=id_)


def set_item_font(filename, id_, wxfont):
    try:
        treeitem = tree.dbs[filename].find_item(id_)
    except KeyError:
        return False
    else:
        return tree.dbs[filename].set_item_font(treeitem, wxfont)


def insert_tree_context_menu_item(filename, pos, item, id_=wx.ID_ANY, help='',
                                  sep='none', kind='normal', sub=None,
                                  icon=None):
    return tree.dbs[filename].cmenu.insert_item(pos, item, id_, help, sep,
                                                kind, sub, icon)


def refresh_history(filename):
    return tree.dbs[filename].history.refresh()


def add_database_accelerators(filename, accels):
    return tree.dbs[filename].add_accelerators(accels)


def add_database_tree_accelerators(filename, accels):
    return tree.dbs[filename].add_tree_accelerators(accels)


def bind_to_reset_tree_context_menu(handler, bind=True):
    return tree.reset_context_menu_event.bind(handler, bind)


def bind_to_popup_tree_context_menu(handler, bind=True):
    return tree.popup_context_menu_event.bind(handler, bind)


def simulate_unselect_all_items(filename):
    return tree.dbs[filename].unselect_all_items()


def simulate_add_items_to_selection(filename, ids):
    for id_ in ids:
        item = tree.dbs[filename].find_item(id_)
        tree.dbs[filename].add_item_to_selection(item)


def simulate_remove_items_from_selection(filename, ids):
    for id_ in ids:
        item = tree.dbs[filename].find_item(id_)
        tree.dbs[filename].remove_item_from_selection(item)
