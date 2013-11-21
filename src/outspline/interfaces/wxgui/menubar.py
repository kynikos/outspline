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

from outspline.coreaux_api import Event
import outspline.core_api as core_api

import databases
import notebooks
import editor
import textarea
import msgboxes
import history
import tree
import about

reset_menu_items_event = Event()
enable_tree_menus_event = Event()
enable_textarea_menus_event = Event()
undo_tree_event = Event()
redo_tree_event = Event()
move_item_event = Event()
delete_items_event = Event()


class RootMenu(wx.MenuBar):
    file = None
    database = None
    edit = None
    view = None
    dev = None
    help = None

    def __init__(self):
        wx.MenuBar.__init__(self)

        self.file = MenuFile()
        self.database = MenuDatabase()
        self.edit = MenuEdit()
        self.view = MenuView()
        self.help = MenuHelp()

        self.Append(self.file, "&File")
        self.Append(self.database, "&Database")
        self.Append(self.edit, "&Editor")
        self.Append(self.view, "&View")
        self.Append(self.dev, "&Dev")
        self.Append(self.help, "&Help")

        self.set_top_menus()

    def insert_item(self, menu, pos, text, id_=wx.ID_ANY, help='', sep='none',
                    kind='normal', sub=None, icon=None):
        menuw = self.GetMenu(self.FindMenu(menu))

        kinds = {'normal': wx.ITEM_NORMAL,
                 'check': wx.ITEM_CHECK,
                 'radio': wx.ITEM_RADIO}

        item = wx.MenuItem(parentMenu=menuw, id=id_, text=text,
                           help=help, kind=kinds[kind], subMenu=sub)

        if icon is not None:
            item.SetBitmap(wx.ArtProvider.GetBitmap(icon, wx.ART_MENU))

        if pos == -1:
            if sep in ('up', 'both'):
                menuw.AppendSeparator()
            menuw.AppendItem(item)
            if sep in ('down', 'both'):
                menuw.AppendSeparator()
        else:
            # Start from bottom, so that it's always possible to use pos
            if sep in ('down', 'both'):
                menuw.InsertSeparator(pos)
            menuw.InsertItem(pos, item)
            if sep in ('up', 'both'):
                menuw.InsertSeparator(pos)
        return item

    def set_top_menus(self):
        self.EnableTop(self.FindMenu('Database'), False)
        self.EnableTop(self.FindMenu('Editor'), False)

        focus = self.FindFocus()

        while focus:
            if focus.__class__ is notebooks.LeftNotebook:
                self.EnableTop(self.FindMenu('Database'), True)
                break
            elif focus.__class__ is editor.EditorPanel or (
                                 focus.__class__ is notebooks.RightNotebook and
                                   wx.GetApp().nb_right.get_selected_editor()):
                self.EnableTop(self.FindMenu('Editor'), True)
                break

            focus = focus.GetParent()

    def update_menus(self, menu):
        reset_menu_items_event.signal(menu=menu)

        focus = self.FindFocus()

        if menu is self.file:
            self.file.update_items(focus)
        elif menu is self.database:
            self.database.update_items(focus)
        elif menu is self.edit:
            self.edit.update_items(focus)
        elif menu is self.view:
            self.view.reset_items()

        self.set_top_menus()


class MenuFile(wx.Menu):
    new_ = None
    open_ = None
    ID_SAVE = None
    save = None
    ID_SAVE_AS = None
    saveas = None
    ID_BACKUP = None
    backup = None
    ID_SAVE_ALL = None
    saveall = None
    ID_CLOSE_DB = None
    close_ = None
    ID_CLOSE_DB_ALL = None
    closeall = None
    exit_ = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_SAVE = wx.NewId()
        self.ID_SAVE_AS = wx.NewId()
        self.ID_BACKUP = wx.NewId()
        self.ID_SAVE_ALL = wx.NewId()
        self.ID_CLOSE_DB = wx.NewId()
        self.ID_CLOSE_DB_ALL = wx.NewId()

        self.new_ = wx.MenuItem(self, wx.ID_NEW, "&New...\tCtrl+N",
                                "Create a new database")
        self.open_ = wx.MenuItem(self, wx.ID_OPEN, "&Open...\tCtrl+O",
                                 "Open a database")
        self.save = wx.MenuItem(self, self.ID_SAVE, "&Save",
                                "Save the selected database")
        self.saveas = wx.MenuItem(self, self.ID_SAVE_AS, "Sav&e as...",
                                 "Save the selected database with another name")
        self.backup = wx.MenuItem(self, self.ID_BACKUP, "Save &backup...",
                                  "Create a backup of the selected database")
        self.saveall = wx.MenuItem(self, self.ID_SAVE_ALL, "Save &all",
                                   "Save all open databases")
        self.close_ = wx.MenuItem(self, self.ID_CLOSE_DB, "&Close",
                                  "Close the selected database")
        self.closeall = wx.MenuItem(self, self.ID_CLOSE_DB_ALL, "C&lose all",
                                    "Close all databases")
        self.exit_ = wx.MenuItem(self, wx.ID_EXIT, "E&xit\tCtrl+Q",
                                 "Terminate the program")

        self.save.SetBitmap(wx.ArtProvider.GetBitmap('@save', wx.ART_MENU))
        self.saveas.SetBitmap(wx.ArtProvider.GetBitmap('@saveas', wx.ART_MENU))
        self.backup.SetBitmap(wx.ArtProvider.GetBitmap('@backup', wx.ART_MENU))
        self.saveall.SetBitmap(wx.ArtProvider.GetBitmap('@saveall',
                                                        wx.ART_MENU))
        self.close_.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))
        self.closeall.SetBitmap(wx.ArtProvider.GetBitmap('@closeall',
                                                         wx.ART_MENU))

        self.AppendItem(self.new_)
        self.AppendItem(self.open_)
        self.AppendSeparator()
        self.AppendItem(self.save)
        self.AppendItem(self.saveas)
        self.AppendItem(self.backup)
        self.AppendItem(self.saveall)
        self.AppendSeparator()
        self.AppendItem(self.close_)
        self.AppendItem(self.closeall)
        self.AppendItem(self.exit_)

        wx.GetApp().Bind(wx.EVT_MENU, self.new_database, self.new_)
        wx.GetApp().Bind(wx.EVT_MENU, self.open_database, self.open_)
        wx.GetApp().Bind(wx.EVT_MENU, self.save_database, self.save)
        wx.GetApp().Bind(wx.EVT_MENU, self.save_database_as, self.saveas)
        wx.GetApp().Bind(wx.EVT_MENU, self.save_all_databases, self.saveall)
        wx.GetApp().Bind(wx.EVT_MENU, self.save_database_backup, self.backup)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_database, self.close_)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_all_databases, self.closeall)
        wx.GetApp().Bind(wx.EVT_MENU, wx.GetApp().exit_app, self.exit_)

        self.reset_items()

    def reset_items(self):
        self.save.Enable(False)
        self.saveas.Enable(False)
        self.backup.Enable(False)
        self.saveall.Enable(False)
        self.close_.Enable(False)
        self.closeall.Enable(False)

    def update_items(self, focus):
        self.reset_items()

        if tree.dbs:
            for dbname in tuple(tree.dbs.keys()):
                if core_api.check_pending_changes(dbname):
                    self.saveall.Enable()
                    break

            self.closeall.Enable()

        while focus:
            if focus.__class__ is notebooks.LeftNotebook:
                tab = wx.GetApp().nb_left.get_selected_tab()
                filename = tab.get_filename()

                if core_api.check_pending_changes(filename):
                    self.save.Enable()

                self.saveas.Enable()
                self.backup.Enable()

                self.close_.Enable()

                # Break in order to speed up, but if an "elif focus.__class__"
                # is added, this break must be removed or left only at the
                # block for the most basic class
                break

            focus = focus.GetParent()

    def new_database(self, event, filename=None):
        core_api.block_databases()
        fn = databases.create_database(filename=filename)
        if fn:
            databases.open_database(fn)
        core_api.release_databases()

    def open_database(self, event, filename=None):
        core_api.block_databases()
        databases.open_database(filename)
        core_api.release_databases()

    def save_database(self, event):
        core_api.block_databases()
        treedb = wx.GetApp().nb_left.get_selected_tab()
        filename = treedb.get_filename()
        if treedb and core_api.check_pending_changes(filename):
            core_api.save_database(filename)
            treedb.history.refresh()
        core_api.release_databases()

    def save_all_databases(self, event):
        core_api.block_databases()
        for filename in tuple(tree.dbs.keys()):
            if core_api.check_pending_changes(filename):
                core_api.save_database(filename)
                tree.dbs[filename].history.refresh()
        core_api.release_databases()

    def save_database_as(self, event):
        core_api.block_databases()
        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            databases.save_database_as(treedb.get_filename())
        core_api.release_databases()

    def save_database_backup(self, event):
        core_api.block_databases()
        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            databases.save_database_backup(treedb.get_filename())
        core_api.release_databases()

    def close_database(self, event, no_confirm=False):
        core_api.block_databases()
        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            databases.close_database(treedb.get_filename(),
                                                          no_confirm=no_confirm)
        core_api.release_databases()

    def close_all_databases(self, event, no_confirm=False, exit_=False):
        core_api.block_databases()
        for filename in tuple(tree.dbs.keys()):
            if databases.close_database(filename, no_confirm=no_confirm,
                                                          exit_=exit_) == False:
                core_api.release_databases()
                return False
        else:
            core_api.release_databases()
            return True


class MenuDatabase(wx.Menu):
    ID_UNDO = None
    undo = None
    ID_REDO = None
    redo = None
    ID_SIBLING = None
    sibling = None
    ID_CHILD = None
    child = None
    ID_MOVE_UP = None
    moveup = None
    ID_MOVE_DOWN = None
    movedn = None
    ID_MOVE_PARENT = None
    movept = None
    ID_EDIT = None
    edit = None
    ID_DELETE = None
    delete = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_UNDO = wx.NewId()
        self.ID_REDO = wx.NewId()
        self.ID_SIBLING = wx.NewId()
        self.ID_CHILD = wx.NewId()
        self.ID_MOVE_UP = wx.NewId()
        self.ID_MOVE_DOWN = wx.NewId()
        self.ID_MOVE_PARENT = wx.NewId()
        self.ID_EDIT = wx.NewId()
        self.ID_DELETE = wx.NewId()

        self.undo = wx.MenuItem(self, self.ID_UNDO, "&Undo",
                                "Undo the previous database edit in history")
        self.redo = wx.MenuItem(self, self.ID_REDO, "&Redo",
                                "Redo the next database edit in history")
        self.sibling = wx.MenuItem(self, self.ID_SIBLING, "Create &item",
                                   "Create a sibling after the selected item")
        self.child = wx.MenuItem(self, self.ID_CHILD, "Create &sub-item",
                                 "Create a child for the selected item")
        self.moveup = wx.MenuItem(self, self.ID_MOVE_UP, "&Move item up",
                                  "Switch the selected item with the one above")
        self.movedn = wx.MenuItem(self, self.ID_MOVE_DOWN,
                                  "Mo&ve item down",
                                  "Switch the selected item with the one below")
        self.movept = wx.MenuItem(self, self.ID_MOVE_PARENT,
                                  "M&ove item to parent",
                            "Move the selected item as a sibling of its parent")
        self.edit = wx.MenuItem(self, self.ID_EDIT, "&Edit item",
                                "Open the selected item in the editor")
        self.delete = wx.MenuItem(self, self.ID_DELETE, "&Delete items",
                                  "Delete the selected items")

        self.undo.SetBitmap(wx.ArtProvider.GetBitmap('@undodb', wx.ART_MENU))
        self.redo.SetBitmap(wx.ArtProvider.GetBitmap('@redodb', wx.ART_MENU))
        self.sibling.SetBitmap(wx.ArtProvider.GetBitmap('@newitem',
                                                        wx.ART_MENU))
        self.child.SetBitmap(wx.ArtProvider.GetBitmap('@newsubitem',
                                                      wx.ART_MENU))
        self.moveup.SetBitmap(wx.ArtProvider.GetBitmap('@moveup', wx.ART_MENU))
        self.movedn.SetBitmap(wx.ArtProvider.GetBitmap('@movedown',
                                                       wx.ART_MENU))
        self.movept.SetBitmap(wx.ArtProvider.GetBitmap('@movetoparent',
                                                       wx.ART_MENU))
        self.edit.SetBitmap(wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU))
        self.delete.SetBitmap(wx.ArtProvider.GetBitmap('@delete', wx.ART_MENU))

        self.AppendItem(self.undo)
        self.AppendItem(self.redo)
        self.AppendSeparator()
        self.AppendItem(self.sibling)
        self.AppendItem(self.child)
        self.AppendSeparator()
        self.AppendItem(self.moveup)
        self.AppendItem(self.movedn)
        self.AppendItem(self.movept)
        self.AppendSeparator()
        self.AppendItem(self.edit)
        self.AppendSeparator()
        self.AppendItem(self.delete)

        wx.GetApp().Bind(wx.EVT_MENU, self.undo_tree, self.undo)
        wx.GetApp().Bind(wx.EVT_MENU, self.redo_tree, self.redo)
        wx.GetApp().Bind(wx.EVT_MENU, self.create_child, self.child)
        wx.GetApp().Bind(wx.EVT_MENU, self.create_sibling, self.sibling)
        wx.GetApp().Bind(wx.EVT_MENU, self.move_item_up, self.moveup)
        wx.GetApp().Bind(wx.EVT_MENU, self.move_item_down, self.movedn)
        wx.GetApp().Bind(wx.EVT_MENU, self.move_item_to_parent, self.movept)
        wx.GetApp().Bind(wx.EVT_MENU, self.edit_item, self.edit)
        wx.GetApp().Bind(wx.EVT_MENU, self.delete_items, self.delete)

        self.reset_items()

    def reset_items(self):
        self.undo.Enable(False)
        self.redo.Enable(False)
        self.sibling.Enable(False)
        self.child.Enable(False)
        self.moveup.Enable(False)
        self.movedn.Enable(False)
        self.movept.Enable(False)
        self.edit.Enable(False)
        self.delete.Enable(False)

    def update_items(self, focus):
        self.reset_items()

        tab = wx.GetApp().nb_left.get_selected_tab()
        filename = tab.get_filename()

        while focus:
            if focus.__class__ is notebooks.LeftNotebook:
                sel = tab.get_selections()

                if core_api.preview_undo_tree(filename):
                    self.undo.Enable()

                if core_api.preview_redo_tree(filename):
                    self.redo.Enable()

                if len(sel) == 1:
                    self.sibling.Enable()
                    self.child.Enable()

                    if tab.get_item_previous(sel[0]).IsOk():
                        self.moveup.Enable()

                    if tab.get_item_next(sel[0]).IsOk():
                        self.movedn.Enable()

                    if not tab.is_database_root(sel[0]):
                        self.movept.Enable()

                    self.edit.Enable()
                    self.delete.Enable()

                elif len(sel) > 1:
                    self.edit.Enable()
                    self.delete.Enable()

                else:
                    self.sibling.Enable()

                enable_tree_menus_event.signal(filename=filename)

                # Break in order to speed up, but if an "elif focus.__class__"
                # is added, this break must be removed or left only at the
                # block for the most basic class
                break

            focus = focus.GetParent()

    def undo_tree(self, event, no_confirm=False):
        core_api.block_databases()

        tab = wx.GetApp().nb_left.get_selected_tab()
        if tab:
            read = core_api.preview_undo_tree(tab.get_filename())
            if read:
                for id_ in read:
                    item = editor.Editor.make_tabid(tab.get_filename(), id_)
                    if item in editor.tabs and not editor.tabs[item].close(
                                      ask='quiet' if no_confirm else 'discard'):
                        break
                else:
                    filename = tab.get_filename()
                    core_api.undo_tree(filename)
                    tab.history.refresh()
                    undo_tree_event.signal(filename=filename)

        core_api.release_databases()

    def redo_tree(self, event, no_confirm=False):
        core_api.block_databases()

        tab = wx.GetApp().nb_left.get_selected_tab()
        if tab:
            read = core_api.preview_redo_tree(tab.get_filename())
            if read:
                for id_ in read:
                    item = editor.Editor.make_tabid(tab.get_filename(), id_)
                    if item in editor.tabs and not editor.tabs[item].close(
                                      ask='quiet' if no_confirm else 'discard'):
                        break
                else:
                    filename = tab.get_filename()
                    core_api.redo_tree(filename)
                    tab.history.refresh()
                    redo_tree_event.signal(filename=filename)

        core_api.release_databases()

    def create_sibling(self, event):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            filename = treedb.get_filename()

            # Do not use none=False in order to allow the creation of the first
            # item
            selection = treedb.get_selections(many=False)
            if selection:
                base = selection[0]
                baseid = treedb.get_item_id(base)

                id_ = core_api.create_sibling(filename=filename, baseid=baseid,
                                              text='New item',
                                              description='Insert item')

                item = treedb.insert_item(base, 'after', id_=id_)
            else:
                base = treedb.get_root()
                baseid = None

                id_ = core_api.create_child(filename=filename, baseid=baseid,
                                            text='New item',
                                            description='Insert item')

                item = treedb.insert_item(base, 'append', id_=id_)

            treedb.select_item(item)

            treedb.history.refresh()

        core_api.release_databases()

    def create_child(self, event):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            selection = treedb.get_selections(none=False, many=False)
            if selection:
                base = selection[0]
                filename = treedb.get_filename()
                baseid = treedb.get_item_id(base)

                id_ = core_api.create_child(filename=filename, baseid=baseid,
                                            text='New item',
                                            description='Insert sub-item')

                item = treedb.insert_item(base, 'append', id_=id_)

                treedb.select_item(item)

                treedb.history.refresh()

        core_api.release_databases()

    def move_item_up(self, event):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            selection = treedb.get_selections(none=False, many=False)
            if selection:
                item = selection[0]

                filename = treedb.get_filename()
                id_ = treedb.get_item_id(item)

                if core_api.move_item_up(filename, id_,
                                                    description='Move item up'):
                    newitem = treedb.move_item(item,
                                                   treedb.get_item_parent(item),
                                           mode=treedb.get_item_index(item) - 1)

                    treedb.select_item(newitem)

                    treedb.history.refresh()

                    move_item_event.signal(filename=filename)

        core_api.release_databases()

    def move_item_down(self, event):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            selection = treedb.get_selections(none=False, many=False)
            if selection:
                item = selection[0]

                filename = treedb.get_filename()
                id_ = treedb.get_item_id(item)

                if core_api.move_item_down(filename, id_,
                                                  description='Move item down'):
                    # When moving down, increase the index by 2, because the move
                    # method first copies the item, and only afterwards deletes it
                    newitem = treedb.move_item(item,
                                                   treedb.get_item_parent(item),
                                           mode=treedb.get_item_index(item) + 2)

                    treedb.select_item(newitem)

                    treedb.history.refresh()

                    move_item_event.signal(filename=filename)

        core_api.release_databases()

    def move_item_to_parent(self, event):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            selection = treedb.get_selections(none=False, many=False)
            if selection:
                item = selection[0]
                filename = treedb.get_filename()
                id_ = treedb.get_item_id(item)

                if core_api.move_item_to_parent(filename, id_,
                                             description='Move item to parent'):
                    newitem = treedb.move_item(item, treedb.get_item_parent(
                                                  treedb.get_item_parent(item)))

                    treedb.select_item(newitem)

                    treedb.history.refresh()

                    move_item_event.signal(filename=filename)

        core_api.release_databases()

    def edit_item(self, event):
        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            selection = treedb.get_selections(none=False)
            if selection:
                filename = treedb.get_filename()

                for sel in selection:
                    id_ = treedb.get_item_id(sel)
                    editor.Editor.open(filename, id_)

    def delete_items(self, event, no_confirm=False):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            selection = treedb.get_selections(none=False, descendants=True)
            if selection and (no_confirm or msgboxes.delete_items_confirm(
                                       len(selection)).ShowModal() == wx.ID_OK):
                filename = treedb.get_filename()
                for item in selection:
                    id_ = treedb.get_item_id(item)
                    tab = editor.Editor.make_tabid(filename, id_)
                    if tab in editor.tabs and not editor.tabs[tab].close(
                                          'quiet' if no_confirm else 'discard'):
                        core_api.release_databases()
                        return False

                items = []
                for item in selection:
                    id_ = treedb.get_item_id(item)
                    items.append(id_)

                core_api.delete_items(filename, items,
                                      description='Delete {} items'
                                      ''.format(len(items)))

                treedb.remove_items(selection)
                treedb.history.refresh()
                delete_items_event.signal()

        core_api.release_databases()


class MenuEdit(wx.Menu):
    ID_SELECT_ALL = None
    select = None
    ID_CUT = None
    cut = None
    ID_COPY = None
    copy = None
    ID_PASTE = None
    paste = None
    ID_APPLY = None
    apply = None
    ID_APPLY_ALL = None
    applyall = None
    ID_CLOSE = None
    close_ = None
    ID_CLOSE_ALL = None
    closeall = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_SELECT_ALL = wx.NewId()
        self.ID_CUT = wx.NewId()
        self.ID_COPY = wx.NewId()
        self.ID_PASTE = wx.NewId()
        self.ID_APPLY = wx.NewId()
        self.ID_APPLY_ALL = wx.NewId()
        self.ID_CLOSE = wx.NewId()
        self.ID_CLOSE_ALL = wx.NewId()

        self.select = wx.MenuItem(self, self.ID_SELECT_ALL, "&Select all",
                                  "Select all text in the editor")
        self.cut = wx.MenuItem(self, self.ID_CUT, "Cu&t",
                               "Cut selected text in the editor")
        self.copy = wx.MenuItem(self, self.ID_COPY, "&Copy",
                                "Copy selected text in the editor")
        self.paste = wx.MenuItem(self, self.ID_PASTE, "&Paste",
                                 "Paste text at the cursor")
        self.apply = wx.MenuItem(self, self.ID_APPLY, "&Apply",
                                 "Apply the focused editor")
        self.applyall = wx.MenuItem(self, self.ID_APPLY_ALL, "App&ly all",
                                    "Apply all open editors")
        self.close_ = wx.MenuItem(self, self.ID_CLOSE, "Cl&ose",
                                  "Close the focused editor")
        self.closeall = wx.MenuItem(self, self.ID_CLOSE_ALL, "Clos&e all",
                                    "Close all editors")

        self.select.SetBitmap(wx.ArtProvider.GetBitmap('@selectall',
                                                       wx.ART_MENU))
        self.cut.SetBitmap(wx.ArtProvider.GetBitmap('@cut', wx.ART_MENU))
        self.copy.SetBitmap(wx.ArtProvider.GetBitmap('@copy', wx.ART_MENU))
        self.paste.SetBitmap(wx.ArtProvider.GetBitmap('@paste', wx.ART_MENU))
        self.apply.SetBitmap(wx.ArtProvider.GetBitmap('@apply', wx.ART_MENU))
        self.applyall.SetBitmap(wx.ArtProvider.GetBitmap('@apply',
                                                         wx.ART_MENU))
        self.close_.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))
        self.closeall.SetBitmap(wx.ArtProvider.GetBitmap('@closeall',
                                                         wx.ART_MENU))

        self.AppendItem(self.select)
        self.AppendItem(self.cut)
        self.AppendItem(self.copy)
        self.AppendItem(self.paste)
        self.AppendSeparator()
        self.AppendItem(self.apply)
        self.AppendItem(self.applyall)
        self.AppendSeparator()
        self.AppendItem(self.close_)
        self.AppendItem(self.closeall)

        wx.GetApp().Bind(wx.EVT_MENU, self.select_all_text, self.select)
        wx.GetApp().Bind(wx.EVT_MENU, self.cut_text, self.cut)
        wx.GetApp().Bind(wx.EVT_MENU, self.copy_text, self.copy)
        wx.GetApp().Bind(wx.EVT_MENU, self.paste_text, self.paste)
        wx.GetApp().Bind(wx.EVT_MENU, self.apply_tab, self.apply)
        wx.GetApp().Bind(wx.EVT_MENU, self.apply_all_tabs, self.applyall)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_tab, self.close_)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_all_tabs, self.closeall)

        self.reset_items()

    def reset_items(self):
        self.select.Enable(False)
        self.cut.Enable(False)
        self.copy.Enable(False)
        self.paste.Enable(False)
        self.apply.Enable(False)
        self.applyall.Enable(False)
        self.close_.Enable(False)
        self.closeall.Enable(False)

    def update_items(self, focus):
        self.reset_items()

        item = wx.GetApp().nb_right.get_selected_editor()
        filename = editor.tabs[item].get_filename()
        id_ = editor.tabs[item].get_id()

        if editor.tabs:
            for i in tuple(editor.tabs.keys()):
                if editor.tabs[i].is_modified():
                    self.applyall.Enable()
                    break

            self.closeall.Enable()

        while focus:
            if focus.__class__ is editor.EditorPanel or (
                                 focus.__class__ is notebooks.RightNotebook and
                                   wx.GetApp().nb_right.get_selected_editor()):
                self.select.Enable()

                if editor.tabs[item].area.can_cut():
                    self.cut.Enable()

                if editor.tabs[item].area.can_copy():
                    self.copy.Enable()

                if editor.tabs[item].area.can_paste():
                    self.paste.Enable()

                if editor.tabs[item].is_modified():
                    self.apply.Enable()

                self.close_.Enable()

                enable_textarea_menus_event.signal(filename=filename, id_=id_,
                                                   item=item)

                # Break in order to speed up, but if an "elif focus.__class__"
                # is added, this break must be removed or left only at the
                # block for the most basic class
                break

            focus = focus.GetParent()

    def select_all_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.select_all()

    def cut_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.cut()

    def copy_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.copy()

    def paste_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.paste()

    def apply_tab(self, event):
        core_api.block_databases()

        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].apply()

        core_api.release_databases()

    def apply_all_tabs(self, event):
        core_api.block_databases()

        for item in editor.tabs:
            editor.tabs[item].apply()

        core_api.release_databases()

    def close_tab(self, event, ask='apply'):
        core_api.block_databases()

        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].close(ask=ask)

        core_api.release_databases()

    def close_all_tabs(self, event, ask='apply'):
        core_api.block_databases()

        for item in tuple(editor.tabs.keys()):
            editor.tabs[item].close(ask=ask)

        core_api.release_databases()


class MenuView(wx.Menu):
    ID_HISTORY = None
    history = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_HISTORY = wx.NewId()

        self.history = self.AppendCheckItem(self.ID_HISTORY,
                                            "Show &history\tCtrl+H",
                                            "Show history frame")

        wx.GetApp().Bind(wx.EVT_MENU, self.toggle_history, self.history)

        self.reset_items()

    def reset_items(self):
        self.history.Check(check=history.is_shown())

    def toggle_history(self, event):
        # Set history.set_shown() here, and not in each
        # tree.dbs[].show_history()... so that this method works also if there
        # aren't open databases
        if history.is_shown():
            for filename in tree.dbs:
                tree.dbs[filename].hide_history()
            history.set_shown(False)
        else:
            for filename in tree.dbs:
                tree.dbs[filename].show_history()
            history.set_shown(True)


class MenuHelp(wx.Menu):
    about = None

    def __init__(self):
        wx.Menu.__init__(self)

        self.about = self.Append(wx.ID_ABOUT, '&About Outspline',
                                 'Information about Outspline and its license')

        wx.GetApp().Bind(wx.EVT_MENU, self.show_about, self.about)

    def show_about(self, event):
        about.AboutWindow()
