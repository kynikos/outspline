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

import wx

import outspline.core_api as core_api

from wxgui import rootw, notebooks, editor, menubar, tree, databases, dbprops


### DATABASE ###

def get_open_databases():
    return databases.get_open_databases()


def get_databases_count():
    return len(tree.dbs)


def register_aborted_save_warning(exception, message):
    return databases.register_aborted_save_warning(exception, message)


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


def collapse_panel(filename, id_, fpanel):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)].collapse_panel(
                                                                        fpanel)


def expand_panel(filename, id_, fpanel):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)].expand_panel(
                                                                        fpanel)


def toggle_panel(filename, id_, fpanel):
    if fpanel.IsExpanded():
        collapse_panel(filename, id_, fpanel)
        return False
    else:
        expand_panel(filename, id_, fpanel)
        return True


def set_editor_modified(filename, id_):
    return editor.tabs[editor.Editor.make_tabid(filename, id_)].set_modified()


def bind_to_open_editor(handler, bind=True):
    return editor.open_editor_event.bind(handler, bind)


def bind_to_apply_editor(handler, bind=True):
    return editor.apply_editor_event.bind(handler, bind)


def bind_to_check_editor_modified_state(handler, bind=True):
    return editor.check_modified_state_event.bind(handler, bind)


def bind_to_close_editor(handler, bind=True):
    return editor.close_editor_event.bind(handler, bind)


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
    tab = wx.GetApp().nb_right.get_selected_editor()
    if tab:
        return editor.tabs[tab].close(ask=ask)
    else:
        return False


def simulate_close_all_editors(ask='apply'):
    for item in editor.tabs.keys():
        editor.tabs[item].close(ask=ask)


### MENUBAR ###

def get_menu_file():
    return wx.GetApp().menu.file


def get_menu_database():
    return wx.GetApp().menu.database


def get_menu_editor():
    return wx.GetApp().menu.edit


def get_menu_view():
    return wx.GetApp().menu.view


def get_menu_view_editors():
    return wx.GetApp().menu.view.editors_submenu


def get_menu_logs():
    return wx.GetApp().menu.view.logs_submenu


def get_menu_view_position():
    return wx.GetApp().menu.FindMenu('View')


def get_menu_help_position():
    return wx.GetApp().menu.FindMenu('Help')


def get_menu_view_close_tab_id():
    return wx.GetApp().menu.view.rightnb_submenu.ID_CLOSE


def insert_menu_main_item(title, position, menu):
    return wx.GetApp().menu.Insert(position, menu, title)


def add_menu_file_item(item):
    position = wx.GetApp().menu.file.GetMenuItemCount() - 1
    return wx.GetApp().menu.file.InsertItem(position, item)


def add_menu_database_item(item):
    return wx.GetApp().menu.database.InsertItem(6, item)


def add_menu_editor_item(item):
    return wx.GetApp().menu.edit.InsertItem(0, item)


def add_menu_view_item(item):
    return wx.GetApp().menu.view.append_plugin_item(item)


def add_menu_editor_plugin(item):
    return wx.GetApp().menu.view.editors_submenu.append_plugin_item(item)


def insert_menu_right_tab_group(menu):
    return wx.GetApp().menu.view.insert_tab_group(menu)


def add_menu_logs_item(item):
    return wx.GetApp().menu.view.logs_submenu.AppendItem(item)


def bind_to_update_menu_items(handler, bind=True):
    return menubar.update_menu_items_event.bind(handler, bind)


def bind_to_reset_menu_items(handler, bind=True):
    return menubar.reset_menu_items_event.bind(handler, bind)


def bind_to_menu_database_update(handler, bind=True):
    return menubar.menu_database_update_event.bind(handler, bind)


def bind_to_menu_edit_update(handler, bind=True):
    return menubar.menu_edit_update_event.bind(handler, bind)


def bind_to_menu_view_update(handler, bind=True):
    return menubar.menu_view_update_event.bind(handler, bind)


def bind_to_menu_view_logs_disable(handler, bind=True):
    return menubar.menu_view_logs_disable_event.bind(handler, bind)


def bind_to_menu_view_logs_update(handler, bind=True):
    return menubar.menu_view_logs_update_event.bind(handler, bind)


def bind_to_menu_view_editors_disable(handler, bind=True):
    return menubar.menu_view_editors_disable_event.bind(handler, bind)


def bind_to_open_database(handler, bind=True):
    return databases.open_database_event.bind(handler, bind)


def bind_to_close_database(handler, bind=True):
    return databases.close_database_event.bind(handler, bind)


def bind_to_undo_tree(handler, bind=True):
    return menubar.undo_tree_event.bind(handler, bind)


def bind_to_redo_tree(handler, bind=True):
    return menubar.redo_tree_event.bind(handler, bind)


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


def select_database_tab(filename):
    index = wx.GetApp().nb_left.GetPageIndex(tree.dbs[filename])
    return select_database_tab_index(index)


def get_selected_database_tab_index():
    # Returns -1 if there's no tab
    return wx.GetApp().nb_left.get_selected_tab_index()


def get_selected_database_filename():
    dbtab = wx.GetApp().nb_left.get_selected_tab()

    if dbtab:
        return dbtab.get_filename()
    else:
        return False


def get_right_nb():
    return wx.GetApp().nb_right


def get_right_nb_generic_accelerators():
    return wx.GetApp().nb_right.get_generic_accelerators()


def select_right_nb_tab(window):
    nb = wx.GetApp().nb_right
    return nb.SetSelection(nb.GetPageIndex(window))


def is_page_in_right_nb(window):
    nb = wx.GetApp().nb_right
    tabid = nb.GetPageIndex(window)
    return True if tabid > -1 else False


def select_editor_tab_index(index):
    return wx.GetApp().nb_right.select_page(index)


def get_selected_editor_tab_index():
    # Returns -1 if there's no tab
    return wx.GetApp().nb_right.get_selected_tab_index()


def get_selected_editor_identification():
    item = wx.GetApp().nb_right.get_selected_editor()

    if item:
        tab = editor.tabs[item]
        return (tab.get_filename(), tab.get_id())
    else:
        return (False, False)


def get_selected_right_nb_tab():
    return wx.GetApp().nb_right.get_selected_tab()


def get_selected_editor():
    return wx.GetApp().nb_right.get_selected_editor()


def get_open_editors_tab_indexes():
    return wx.GetApp().nb_right.get_open_editors()


def add_right_nb_image(image):
    return wx.GetApp().nb_right.add_image(image)


# wx.NO_IMAGE, which is used in the docs, seems not to exist...
def add_plugin_to_right_nb(window, caption, close, closeArgs=(), select=True,
                                                        imageId=wx.NOT_FOUND):
    return wx.GetApp().nb_right.add_plugin(window, caption=caption,
            close=close, closeArgs=closeArgs, select=select, imageId=imageId)


# wx.NO_IMAGE, which is used in the docs, seems not to exist...
def add_page_to_right_nb(window, caption, close, closeArgs=(), select=True,
                                                        imageId=wx.NOT_FOUND):
    return wx.GetApp().nb_right.add_page(window, caption=caption, close=close,
                        closeArgs=closeArgs, select=select, imageId=imageId)


def hide_right_nb_page(window):
    nb = wx.GetApp().nb_right
    tabid = nb.GetPageIndex(window)
    return nb.hide_page(tabid)


def close_right_nb_page(window):
    nb = wx.GetApp().nb_right
    tabid = nb.GetPageIndex(window)
    return nb.close_page(tabid)


def set_right_nb_page_title(window, title):
    return wx.GetApp().nb_right.set_page_title(window, title)


def set_right_nb_page_image(page, index):
    return wx.GetApp().nb_right.set_page_image(page, index)


def bind_to_plugin_close_event(handler, bind=True):
    return notebooks.plugin_close_event.bind(handler, bind)


### ROOTW ###

def get_main_frame():
    return wx.GetApp().root


def get_main_icon_bundle():
    return wx.GetApp().get_main_icon_bundle()


def show_main_window():
    return wx.GetApp().root.show()


def hide_main_window():
    return wx.GetApp().root.hide()


def toggle_main_window():
    return wx.GetApp().root.toggle_shown()


def is_shown():
    return wx.GetApp().root.IsShown()


def generate_right_nb_accelerators(accelsconf):
    return wx.GetApp().root.accmanager.generate_table(wx.GetApp().nb_right,
                                                                    accelsconf)


def install_accelerators(window, accelsconf):
    return wx.GetApp().root.accmanager.create_manager(window, accelsconf)


def register_text_ctrl(window):
    return wx.GetApp().root.accmanager.register_text_ctrl(window)


def exit_application(event):
    return wx.GetApp().exit_app(event)


def bind_to_menu(handler, button):
    return wx.GetApp().root.Bind(wx.EVT_MENU, handler, button)


def bind_to_application_loaded(handler, bind=True):
    return rootw.application_loaded_event.bind(handler, bind)


def bind_to_show_main_window(handler, bind=True):
    return rootw.show_main_window_event.bind(handler, bind)


def bind_to_hide_main_window(handler, bind=True):
    return rootw.hide_main_window_event.bind(handler, bind)


def bind_to_close_window(handler):
    return wx.GetApp().root.bind_to_close_event(handler)


### TREE ###

def get_tree_selections(filename, none=True, many=True, descendants=None):
    return tree.dbs[filename].get_selections(none=none, many=many,
                                             descendants=descendants)


def unselect_all_items(filename):
    return tree.dbs[filename].unselect_all_items()


def add_item_to_selection(filename, id_):
    return tree.dbs[filename].add_item_to_selection(id_)


def get_tree_item_id(filename, item):
    return tree.dbs[filename].get_item_id(item)


def delete_items(filename, ids, description="Delete items"):
    return tree.dbs[filename].delete_items(ids, description=description)


def get_tree_context_menu(filename):
    return tree.dbs[filename].cmenu


def add_tree_context_menu_item(filename, item):
    return tree.dbs[filename].cmenu.InsertItem(3, item)


def add_item_property(filename, bitsn, character, bits_to_colour):
    return tree.dbs[filename].add_property(bitsn, character, bits_to_colour)


def update_item_properties(filename, id_, property_bits, property_mask):
    tree.dbs[filename].update_item_properties(id_, property_bits,
                                                                property_mask)


def update_tree_item(filename, id_):
    tree.dbs[filename].update_tree_item(id_)


def request_tree_item_refresh(filename, id_):
    return tree.dbs[filename].request_item_refresh(id_)


def get_logs_parent(filename):
    return tree.dbs[filename].get_logs_panel().get_panel()


def add_log(filename, sizer, label, icon, menu_items, menu_update):
    return tree.dbs[filename].get_logs_panel().add_log(sizer, label, icon,
                                                    menu_items, menu_update)


def select_log(tool_id):
    treedb = wx.GetApp().nb_left.get_selected_tab()
    return treedb.get_logs_panel().select_log(tool_id)


def refresh_history(filename):
    return tree.dbs[filename].dbhistory.refresh()


def bind_to_creating_tree(handler, bind=True):
    return tree.creating_tree_event.bind(handler, bind)


def bind_to_reset_tree_context_menu(handler, bind=True):
    return tree.reset_context_menu_event.bind(handler, bind)


def bind_to_popup_tree_context_menu(handler, bind=True):
    return tree.popup_context_menu_event.bind(handler, bind)


def simulate_unselect_all_items(filename):
    return tree.dbs[filename].unselect_all_items()


def simulate_add_items_to_selection(filename, ids):
    for id_ in ids:
        tree.dbs[filename].add_item_to_selection(id_)


def simulate_remove_items_from_selection(filename, ids):
    for id_ in ids:
        tree.dbs[filename].remove_item_from_selection(id_)


### PROPERTIES ###

def add_property_option(filename, property_, action):
    manager = databases.dbpropmanager.get_open_tab(filename)
    return manager.add_option(property_, action)


def bind_to_load_property_options(handler, bind=True):
    return dbprops.load_options_event.bind(handler, bind)


### TEMPORARY CODE ###

class Bug332Workaround(object):
    # Temporary workaround for bug #332
    # Note that simply using the Window.Navigate or Window.NavigateIn methods
    #  doesn't work :(
    # Also note that DatePickerCtrl doesn't seem to respond to EVT_KEY_DOWN
    #  nor EVT_CHAR, so an AcceleratorTable must be used :((
    def __init__(self, datepicker, previous, next_):
        self.previous = previous
        self.datepicker = datepicker
        self.next = next_

        ID_PREVIOUS = wx.NewId()
        ID_NEXT = wx.NewId()
        datepicker.Bind(wx.EVT_BUTTON, self._focus_previous, id=ID_PREVIOUS)
        datepicker.Bind(wx.EVT_BUTTON, self._focus_next, id=ID_NEXT)

        accels = [
            wx.AcceleratorEntry(wx.ACCEL_SHIFT, wx.WXK_TAB, ID_PREVIOUS),
            wx.AcceleratorEntry(wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_TAB,
                                                                ID_PREVIOUS),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_TAB, ID_NEXT),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_TAB, ID_NEXT),
        ]

        acctable = wx.AcceleratorTable(accels)
        datepicker.SetAcceleratorTable(acctable)

    def _focus_previous(self, event):
        try:
            self.previous.SetFocus()
        except AttributeError:
            # self.previous could be a callable
            self.previous().SetFocus()
        except wx.PyAssertionError:
            # PyAssertionError is raised if, when Tab is pressed, the
            # DatePickerCtrl has been cleared with e.g. Del (it has no content)
            pass
        # Do not Skip the event, or the focus will be moved 2 widgets ahead

    def _focus_next(self, event):
        try:
            self.next.SetFocus()
        except AttributeError:
            # self.previous could be a callable
            self.next().SetFocus()
        except wx.PyAssertionError:
            # PyAssertionError is raised if, when Tab is pressed, the
            # DatePickerCtrl has been cleared with e.g. Del (it has no content)
            pass
        # Do not Skip the event, or the focus will be moved 2 widgets ahead
