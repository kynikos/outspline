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

from outspline.coreaux_api import Event
import outspline.core_api as core_api

import databases
import notebooks
import editor
import textarea
import msgboxes
import logs
import tree
import about

update_menu_items_event = Event()
reset_menu_items_event = Event()
menu_database_update_event = Event()
menu_edit_update_event = Event()
menu_logs_update_event = Event()
undo_tree_event = Event()
redo_tree_event = Event()
move_item_event = Event()
delete_items_event = Event()


class RootMenu(wx.MenuBar):
    def __init__(self):
        # Note that the menu can be accessed through F10, which is an
        # accelerator that doesn't seem to be overridable neither through
        # menu shortcuts nor through accelerators
        wx.MenuBar.__init__(self)

        self.file = MenuFile()
        self.database = MenuDatabase()
        self.edit = MenuEdit()
        self.logs = MenuLogs()
        self.help = MenuHelp()

        self.Append(self.file, "&File")
        self.Append(self.database, "&Database")
        self.Append(self.edit, "&Editor")
        self.Append(self.logs, "&Logs")
        self.Append(self.help, "&Help")

    def update_menus(self, event):
        menu = event.GetMenu()

        if menu is self.file:
            self.file.update_items()
        elif menu is self.database:
            self.database.update_items()
        elif menu is self.edit:
            self.edit.update_items()
        elif menu is self.logs:
            self.logs.update_items()
        else:
            update_menu_items_event.signal(menu=menu)

    def reset_menus(self, event):
        # Reset the menus only if the closed menu is a top-level one, in fact
        # EVT_MENU_CLOSE is signalled also for sub-menus, but in those cases
        # the menus must not be reset
        if event.GetMenu().GetParent() is None:
            # Re-enable all the actions so they are available for their
            # accelerators
            # EVT_MENU_CLOSE is signalled only for the last-closed menu, but since
            # all the others opened have been updated, all the menus have to be
            # reset (don't check event.GetMenu() is menu)
            self.file.reset_items()
            self.database.reset_items()
            self.edit.reset_items()

            reset_menu_items_event.signal()


class MenuFile(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_SAVE = wx.NewId()
        self.ID_SAVE_AS = wx.NewId()
        self.ID_BACKUP = wx.NewId()
        self.ID_SAVE_ALL = wx.NewId()
        self.ID_CLOSE_DB = wx.NewId()
        self.ID_CLOSE_DB_ALL = wx.NewId()

        self.new_ = wx.MenuItem(self, wx.ID_NEW, "&New...\tCTRL+n",
                                "Create a new database")
        self.open_ = wx.MenuItem(self, wx.ID_OPEN, "&Open...\tCTRL+o",
                                "Open a database")
        self.save = wx.MenuItem(self, self.ID_SAVE, "&Save\tCTRL+s",
                                "Save the selected database")
        self.saveas = wx.MenuItem(self, self.ID_SAVE_AS, "Sav&e as...",
                                "Save the selected database with another name")
        self.backup = wx.MenuItem(self, self.ID_BACKUP, "Save &backup...",
                                "Create a backup of the selected database")
        self.saveall = wx.MenuItem(self, self.ID_SAVE_ALL,
                        "Save &all\tCTRL+SHIFT+s", "Save all open databases")
        self.close_ = wx.MenuItem(self, self.ID_CLOSE_DB, "&Close\tCTRL+w",
                                "Close the selected database")
        self.closeall = wx.MenuItem(self, self.ID_CLOSE_DB_ALL,
                            "C&lose all\tCTRL+SHIFT+w", "Close all databases")
        self.exit_ = wx.MenuItem(self, wx.ID_EXIT, "E&xit\tCTRL+q",
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
        self.AppendSeparator()
        self.AppendItem(self.exit_)

        wx.GetApp().Bind(wx.EVT_MENU, self.new_database, self.new_)
        wx.GetApp().Bind(wx.EVT_MENU, self.open_database, self.open_)
        wx.GetApp().Bind(wx.EVT_MENU, self.save_database, self.save)
        wx.GetApp().Bind(wx.EVT_MENU, self._save_database_as, self.saveas)
        wx.GetApp().Bind(wx.EVT_MENU, self.save_all_databases, self.saveall)
        wx.GetApp().Bind(wx.EVT_MENU, self._save_database_backup, self.backup)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_database, self.close_)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_all_databases, self.closeall)
        wx.GetApp().Bind(wx.EVT_MENU, wx.GetApp().exit_app, self.exit_)

    def update_items(self):
        self.save.Enable(False)
        self.saveas.Enable(False)
        self.backup.Enable(False)
        self.saveall.Enable(False)
        self.close_.Enable(False)
        self.closeall.Enable(False)

        if tree.dbs:
            for dbname in tuple(tree.dbs.keys()):
                if core_api.check_pending_changes(dbname):
                    self.saveall.Enable()
                    break

            tab = wx.GetApp().nb_left.get_selected_tab()
            filename = tab.get_filename()

            if core_api.check_pending_changes(filename):
                self.save.Enable()

            self.saveas.Enable()
            self.backup.Enable()

            self.close_.Enable()
            self.closeall.Enable()

    def reset_items(self):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.save.Enable()
        self.saveas.Enable()
        self.backup.Enable()
        self.saveall.Enable()
        self.close_.Enable()
        self.closeall.Enable()

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

        if treedb:
            filename = treedb.get_filename()

            if core_api.check_pending_changes(filename):
                core_api.save_database(filename)
                treedb.dbhistory.refresh()

        core_api.release_databases()

    def save_all_databases(self, event):
        core_api.block_databases()

        for filename in tuple(tree.dbs.keys()):
            if core_api.check_pending_changes(filename):
                core_api.save_database(filename)
                tree.dbs[filename].dbhistory.refresh()

        core_api.release_databases()

    def _save_database_as(self, event):
        core_api.block_databases()
        treedb = wx.GetApp().nb_left.get_selected_tab()

        if treedb:
            databases.save_database_as(treedb.get_filename())

        core_api.release_databases()

    def _save_database_backup(self, event):
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

        self.sibling_label_1 = "Create &item\tCTRL+INSERT"
        self.sibling_help_1 = "Create a root item"
        self.sibling_label_2 = "Create s&ibling\tCTRL+INSERT"
        self.sibling_help_2 = "Create a sibling below the selected item"

        self.undo = wx.MenuItem(self, self.ID_UNDO, "&Undo\tCTRL+SHIFT+z",
                                "Undo the previous database edit in history")
        self.redo = wx.MenuItem(self, self.ID_REDO, "&Redo\tCTRL+SHIFT+y",
                                    "Redo the next database edit in history")
        self.sibling = wx.MenuItem(self, self.ID_SIBLING, self.sibling_label_1,
                                                        self.sibling_help_1)
        self.child = wx.MenuItem(self, self.ID_CHILD,
                                        "Create c&hild\tCTRL+SHIFT+INSERT",
                                        "Create a child for the selected item")
        self.moveup = wx.MenuItem(self, self.ID_MOVE_UP,
                                "&Move item up\tCTRL+k",
                                "Swap the selected item with the one above")
        self.movedn = wx.MenuItem(self, self.ID_MOVE_DOWN,
                                  "Mo&ve item down\tCTRL+j",
                                  "Swap the selected item with the one below")
        self.movept = wx.MenuItem(self, self.ID_MOVE_PARENT,
                        "M&ove item to parent\tCTRL+h",
                        "Move the selected item as a sibling of its parent")
        self.edit = wx.MenuItem(self, self.ID_EDIT, "&Edit item\tCTRL+ENTER",
                                "Open the selected item in the editor")
        self.delete = wx.MenuItem(self, self.ID_DELETE,
                                                "&Delete items\tCTRL+DELETE",
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

    def update_items(self):
        self.undo.Enable(False)
        self.redo.Enable(False)
        self.sibling.Enable(False)
        self.child.Enable(False)
        self.moveup.Enable(False)
        self.movedn.Enable(False)
        self.movept.Enable(False)
        self.edit.Enable(False)
        self.delete.Enable(False)
        self.sibling.SetItemLabel(self.sibling_label_1)
        self.sibling.SetHelp(self.sibling_help_1)

        tab = wx.GetApp().nb_left.get_selected_tab()

        if tab:
            filename = tab.get_filename()
            sel = tab.get_selections()

            if core_api.preview_undo_tree(filename):
                self.undo.Enable()

            if core_api.preview_redo_tree(filename):
                self.redo.Enable()

            if len(sel) == 1:
                self.sibling.Enable()
                self.sibling.SetItemLabel(self.sibling_label_2)
                self.sibling.SetHelp(self.sibling_help_2)
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

            menu_database_update_event.signal(filename=filename)
        else:
            # Signal the event even if there are no databases (tabs) open
            menu_database_update_event.signal(filename=None)


    def reset_items(self):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.undo.Enable()
        self.redo.Enable()
        self.sibling.Enable()
        self.child.Enable()
        self.moveup.Enable()
        self.movedn.Enable()
        self.movept.Enable()
        self.edit.Enable()
        self.delete.Enable()

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
                    tab.dbhistory.refresh()
                    undo_tree_event.signal(filename=filename, items=read)

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
                    tab.dbhistory.refresh()
                    redo_tree_event.signal(filename=filename, items=read)

        core_api.release_databases()

    def create_sibling(self, event):
        core_api.block_databases()

        treedb = wx.GetApp().nb_left.get_selected_tab()
        if treedb:
            filename = treedb.get_filename()

            # Do not use none=False in order to allow the creation of the first
            # item
            selection = treedb.get_selections(many=False)

            # If multiple items are selected, selection will be bool (False)
            if isinstance(selection, list):
                text = 'New item'

                if len(selection) > 0:
                    base = selection[0]
                    baseid = treedb.get_item_id(base)

                    id_ = core_api.create_sibling(filename=filename,
                                                    baseid=baseid,
                                                    text=text,
                                                    description='Insert item')

                    item = treedb.insert_item(base, 'after', id_, text=text)
                else:
                    base = treedb.get_root()
                    baseid = None

                    id_ = core_api.create_child(filename=filename,
                                                    baseid=baseid,
                                                    text=text,
                                                    description='Insert item')

                    item = treedb.insert_item(base, 'append', id_, text=text)

                treedb.select_item(item)

                treedb.dbhistory.refresh()

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
                text = 'New item'

                id_ = core_api.create_child(filename=filename, baseid=baseid,
                                            text=text,
                                            description='Insert sub-item')

                item = treedb.insert_item(base, 'append', id_, text=text)

                treedb.select_item(item)

                treedb.dbhistory.refresh()

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

                    treedb.dbhistory.refresh()

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
                    # When moving down, increase the index by 2, because the
                    # move method first copies the item, and only afterwards
                    # deletes it
                    newitem = treedb.move_item(item,
                                                treedb.get_item_parent(item),
                                        mode=treedb.get_item_index(item) + 2)

                    treedb.select_item(newitem)

                    treedb.dbhistory.refresh()

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

                    treedb.dbhistory.refresh()

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
            if selection:
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
                treedb.dbhistory.refresh()
                delete_items_event.signal()

        core_api.release_databases()


class MenuEdit(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_SELECT_ALL = wx.NewId()
        self.ID_CUT = wx.NewId()
        self.ID_COPY = wx.NewId()
        self.ID_PASTE = wx.NewId()
        self.ID_FIND = wx.NewId()
        self.ID_APPLY = wx.NewId()
        self.ID_APPLY_ALL = wx.NewId()
        self.ID_CLOSE = wx.NewId()
        self.ID_CLOSE_ALL = wx.NewId()

        self.select = wx.MenuItem(self, self.ID_SELECT_ALL,
                        "&Select all\tCTRL+a", "Select all text in the editor")
        self.cut = wx.MenuItem(self, self.ID_CUT, "Cu&t\tCTRL+x",
                                            "Cut selected text in the editor")
        self.copy = wx.MenuItem(self, self.ID_COPY, "&Copy\tCTRL+c",
                                            "Copy selected text in the editor")
        self.paste = wx.MenuItem(self, self.ID_PASTE, "&Paste\tCTRL+v",
                                                    "Paste text at the cursor")
        self.find = wx.MenuItem(self, self.ID_FIND,
                                "&Find in database\tF2",
                                "Find the edited item in the database tree")
        self.apply = wx.MenuItem(self, self.ID_APPLY, "&Apply\tF3",
                                 "Apply the focused editor")
        self.applyall = wx.MenuItem(self, self.ID_APPLY_ALL,
                            "App&ly all\tCTRL+F3", "Apply all open editors")
        self.close_ = wx.MenuItem(self, self.ID_CLOSE, "Cl&ose\tF4",
                                  "Close the focused editor")
        self.closeall = wx.MenuItem(self, self.ID_CLOSE_ALL,
                                    "Clos&e all\tCTRL+F4", "Close all editors")

        self.select.SetBitmap(wx.ArtProvider.GetBitmap('@selectall',
                                                       wx.ART_MENU))
        self.cut.SetBitmap(wx.ArtProvider.GetBitmap('@cut', wx.ART_MENU))
        self.copy.SetBitmap(wx.ArtProvider.GetBitmap('@copy', wx.ART_MENU))
        self.paste.SetBitmap(wx.ArtProvider.GetBitmap('@paste', wx.ART_MENU))
        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
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
        self.AppendItem(self.find)
        self.AppendSeparator()
        self.AppendItem(self.apply)
        self.AppendItem(self.applyall)
        self.AppendSeparator()
        self.AppendItem(self.close_)
        self.AppendItem(self.closeall)

        wx.GetApp().Bind(wx.EVT_MENU, self._select_all_text, self.select)
        wx.GetApp().Bind(wx.EVT_MENU, self._cut_text, self.cut)
        wx.GetApp().Bind(wx.EVT_MENU, self._copy_text, self.copy)
        wx.GetApp().Bind(wx.EVT_MENU, self._paste_text, self.paste)
        wx.GetApp().Bind(wx.EVT_MENU, self._find_item, self.find)
        wx.GetApp().Bind(wx.EVT_MENU, self.apply_tab, self.apply)
        wx.GetApp().Bind(wx.EVT_MENU, self.apply_all_tabs, self.applyall)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_tab, self.close_)
        wx.GetApp().Bind(wx.EVT_MENU, self.close_all_tabs, self.closeall)

    def update_items(self):
        self.select.Enable(False)
        self.cut.Enable(False)
        self.copy.Enable(False)
        self.paste.Enable(False)
        self.find.Enable(False)
        self.apply.Enable(False)
        self.applyall.Enable(False)
        self.close_.Enable(False)
        self.closeall.Enable(False)

        if editor.tabs:
            for i in tuple(editor.tabs.keys()):
                if editor.tabs[i].is_modified():
                    self.applyall.Enable()
                    break

            self.closeall.Enable()

            item = wx.GetApp().nb_right.get_selected_editor()

            if item:
                filename = editor.tabs[item].get_filename()
                id_ = editor.tabs[item].get_id()

                self.select.Enable()

                if editor.tabs[item].area.can_cut():
                    self.cut.Enable()

                if editor.tabs[item].area.can_copy():
                    self.copy.Enable()

                if editor.tabs[item].area.can_paste():
                    self.paste.Enable()

                self.find.Enable()

                if editor.tabs[item].is_modified():
                    self.apply.Enable()

                self.close_.Enable()

                menu_edit_update_event.signal(filename=filename, id_=id_,
                                                                    item=item)
            else:
                # Signal the event even if there are no editor tabs open
                menu_edit_update_event.signal(filename=None, id_=None,
                                                                    item=None)
        else:
            # Signal the event even if there are no tabs open
            menu_edit_update_event.signal(filename=None, id_=None, item=None)

    def reset_items(self):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.select.Enable()
        self.cut.Enable()
        self.copy.Enable()
        self.paste.Enable()
        self.find.Enable()
        self.apply.Enable()
        self.applyall.Enable()
        self.close_.Enable()
        self.closeall.Enable()

    def _select_all_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.select_all()

    def _cut_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.cut()

    def _copy_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.copy()

    def _paste_text(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].area.paste()

    def _find_item(self, event):
        tab = wx.GetApp().nb_right.get_selected_editor()
        if tab:
            editor.tabs[tab].find_in_tree()

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


class MenuLogs(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.ID_LOGS = wx.NewId()

        self.logs = self.AppendCheckItem(self.ID_LOGS,
                                            "Show &panel\tCTRL+SHIFT+l",
                                            "Show logs panel")

        wx.GetApp().Bind(wx.EVT_MENU, self._toggle_logs, self.logs)

    def update_items(self):
        self.logs.Check(check=wx.GetApp().logs_configuration.is_shown())
        menu_logs_update_event.signal()

    def _toggle_logs(self, event):
        # Set logs_configuration.set_shown() here, and not in each
        # tree.dbs[].show_logs()... so that this method works also if there
        # aren't open databases
        if wx.GetApp().logs_configuration.is_shown():
            for filename in tree.dbs:
                tree.dbs[filename].hide_logs()
            wx.GetApp().logs_configuration.set_shown(False)
        else:
            for filename in tree.dbs:
                tree.dbs[filename].show_logs()
            wx.GetApp().logs_configuration.set_shown(True)


class MenuHelp(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)

        self.about = self.Append(wx.ID_ABOUT, '&About Outspline',
                    'Information about Outspline and the installed add-ons')

        wx.GetApp().Bind(wx.EVT_MENU, self._show_about, self.about)

    def _show_about(self, event):
        about.AboutWindow()
