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

import os
import wx

from outspline.coreaux_api import Event
import outspline.core_api as core_api

import history

reset_context_menu_event = Event()
popup_context_menu_event = Event()

dbs = {}


class Tree(wx.TreeCtrl):
    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent, wx.ID_ANY, style=wx.TR_HAS_BUTTONS |
                             wx.TR_HIDE_ROOT | wx.TR_MULTIPLE |
                             wx.TR_EXTENDED | wx.TR_FULL_ROW_HIGHLIGHT)


class Database(wx.SplitterWindow):
    treec = None
    filename = None
    root = None
    titems = None
    cmenu = None
    ctabmenu = None
    hpanel = None
    history = None

    def __init__(self, filename, parent):
        wx.SplitterWindow.__init__(self, parent, style=wx.SP_LIVE_UPDATE)

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)

        self.filename = filename

        self.treec = Tree(self)
        data = wx.TreeItemData(0)
        self.root = self.treec.AddRoot(text='root', data=data)
        self.titems = {0: data}

        self.cmenu = ContextMenu(self)
        self.ctabmenu = TabContextMenu(self.filename)

        self.hpanel = wx.Panel(self)
        bs = wx.BoxSizer(wx.VERTICAL)
        self.hpanel.SetSizer(bs)

        self.history = history.HistoryWindow(self.hpanel, self.filename)

        line = wx.StaticLine(self.hpanel, size=(1, 1), style=wx.LI_HORIZONTAL)

        bs.Add(line, flag=wx.EXPAND)
        bs.Add(self.history, 1, flag=wx.EXPAND)

        self.hpanel.Show(False)
        self.Initialize(self.treec)

        self.create()

        self.treec.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.veto_label_edit)
        self.treec.Bind(wx.EVT_TREE_ITEM_MENU, self.popup_item_menu)
        self.treec.Bind(wx.EVT_RIGHT_DOWN, self.popup_window_menu)
        self.treec.Bind(wx.EVT_LEFT_DOWN, self.unselect_on_empty_areas)

        core_api.bind_to_update_item(self.handle_update_item)
        core_api.bind_to_history_insert(self.handle_history_insert)
        core_api.bind_to_history_update(self.handle_history_update)
        core_api.bind_to_history_remove(self.handle_history_remove)

    def veto_label_edit(self, event):
        event.Veto()

    def handle_update_item(self, kwargs):
        # Don't update an item label only when editing the text area, as there
        # may be other plugins that edit an item's text (e.g links)
        # kwargs['text'] could be None if the query updated the position of the
        # item and not its text
        if kwargs['filename'] == self.filename and kwargs['text'] is not None:
            treeitem = self.find_item(kwargs['id_'])
            title = self.make_item_title(kwargs['text'])
            self.set_item_title(treeitem, title)

    def handle_history_insert(self, kwargs):
        filename = kwargs['filename']
        if filename == self.filename:
            id_ = kwargs['id_']
            parent = kwargs['parent']
            previous = kwargs['previous']
            text = kwargs['text']

            if previous == 0:
                par = self.find_item(parent)
                label = self.make_item_title(text)
                self.insert_item(par, 0, label=label, id_=id_)
            else:
                prev = self.find_item(previous)
                label = self.make_item_title(text)
                self.insert_item(prev, 'after', label=label, id_=id_)

    def handle_history_update(self, kwargs):
        filename = kwargs['filename']
        if filename == self.filename:
            id_ = kwargs['id_']
            parent = kwargs['parent']
            previous = kwargs['previous']
            text = kwargs['text']

            item = self.find_item(id_)

            # Reset the label before moving the item, otherwise the item has to
            # be found again, or the program crashes
            label = self.make_item_title(text)
            self.set_item_title(item, label)

            if self.get_item_id(
                                self.get_item_parent(item)) != parent or \
                                (self.get_item_previous(item).IsOk() and \
                                self.get_item_id(
                                self.get_item_previous(item)) != previous) or \
                                (not self.get_item_previous(item).IsOk() and \
                                previous != 0):
                if previous == 0:
                    par = self.find_item(parent)
                    self.move_item(item, par, mode=0)
                else:
                    prev = self.find_item(previous)
                    self.move_item(item, prev, mode='after')

    def handle_history_remove(self, kwargs):
        filename = kwargs['filename']
        id_ = kwargs['id_']

        if filename == self.filename:
            item = self.find_item(id_)
            self.remove_items([item, ])

    @classmethod
    def open(cls, filename):
        nb_left = wx.GetApp().nb_left
        global dbs
        dbs[filename] = cls(filename, nb_left)

        nb_left.add_page(dbs[filename], os.path.basename(filename),
                         select=True)

        # The history panel must be shown only *after* adding the page to the
        # notebook, otherwise *for*some*reason* the databases opened
        # automatically by the wxsession plugin (those opened manually aren't
        # affected) will have the sash of the SplitterWindow not correctly
        # positioned (only if using SetSashGravity)
        if history.is_shown():
            dbs[filename].show_history()

    def insert_item(self, base, mode, label=None, data=None, id_=None):
        # The empty string is a valid label
        if not label and label != '':
            label = self.make_item_title(core_api.get_item_text(self.filename,
                                                                id_))

        if not data:
            data = wx.TreeItemData(id_)

        if id_ == None:
            id_ = data.GetData()

        self.titems[id_] = data

        if mode == 'append':
            return self.treec.AppendItem(base, text=label, data=data)
        elif mode == 'after':
            return self.treec.InsertItem(self.get_item_parent(base),
                                         idPrevious=base,
                                         text=label, data=data)
        elif mode == 'before':
            return self.treec.InsertItemBefore(self.get_item_parent(base),
                                         self.get_item_index(base), text=label,
                                         data=data)
        elif isinstance(mode, int):
            return self.treec.InsertItemBefore(base, mode, text=label,
                                               data=data)
        else:
            return False

    def create(self, base=None, previd=0):
        if not base:
            base = self.treec.GetRootItem()
        baseid = self.get_item_id(base)

        child = core_api.get_tree_item(self.filename, baseid, previd)
        if child:
            id_ = child['id_']
            title = self.make_item_title(child['text'])

            titem = self.insert_item(base, 'append', label=title, id_=id_)

            self.create(base=titem, previd=0)
            self.create(base=base, previd=id_)

    def find_item(self, id_):
        return self.titems[id_].GetId()

    def get_selections(self, none=True, many=True, descendants=None):
        selection = self.treec.GetSelections()

        if (not none and len(selection) == 0) or (not many and
                                                  len(selection) > 1):
            return False
        elif descendants == False:
            for item in selection:
                for ancestor in self.get_item_ancestors(item):
                    if ancestor in selection:
                        # Note that UnselectItem may actually select if the item
                        # is not selected, see
                        # http://trac.wxwidgets.org/ticket/11157
                        # However in this case the item has just been checked if
                        # selected, so no further checks must be done
                        self.treec.UnselectItem(item)
        elif descendants == True:
            for item in selection:
                for descendant in self.get_item_descendants(item):
                    # If the descendant is already selected, SelectItem would
                    # actually deselect it, see
                    # http://trac.wxwidgets.org/ticket/11157
                    # This would e.g. generate the following bug: create an item
                    # (A), create a sibling (B) of A, create a child (C) of B,
                    # select *all* three items (thus expanding B) and try to
                    # delete them: without the IsSelected check it would go in
                    # an infinite loop since C gets deselected and the function
                    # that deletes items has to start from the items that do not
                    # have children
                    if not self.treec.IsSelected(descendant):
                        self.treec.SelectItem(descendant)

        return self.treec.GetSelections()

    def move_item(self, treeitem, base, mode='append'):
        title = self.treec.GetItemText(treeitem)
        # Do not just copy data with self.treec.GetItemData() because it causes
        # crashes even without throwing exceptions or errors in console!
        data = wx.TreeItemData(self.treec.GetPyData(treeitem))

        if mode in ('append', 'after', 'before') or isinstance(mode, int):
            # When moving down, add 1 to the destination index, because the
            # move method first copies the item, and only afterwards deletes it
            newtreeitem = self.insert_item(base, mode, label=title, data=data)
        else:
            raise ValueError()

        while self.treec.ItemHasChildren(treeitem):
            first = self.treec.GetFirstChild(treeitem)
            # Always use append mode for the descendants
            self.move_item(first[0], newtreeitem)

        # Do not use remove_items, as self.titems has already been updated
        # here, and using remove_items would remove the moved item from
        # self.titems
        self.treec.Delete(treeitem)

        return newtreeitem

    def remove_items(self, treeitems):
        # When deleting items, make sure to delete first those without
        # children, otherwise crashes without exceptions or errors could occur
        while treeitems:
            for item in treeitems:
                if not self.treec.ItemHasChildren(item):
                    del treeitems[treeitems.index(item)]
                    id_ = self.treec.GetPyData(item)
                    self.treec.Delete(item)
                    del self.titems[id_]

    def close(self):
        self.treec.DeleteAllItems()
        self.titems = {}

        global dbs
        del dbs[self.filename]

    def show_history(self):
        self.SplitHorizontally(self.treec, self.hpanel)
        self.SetSashGravity(1.0)

        # The same workaround for http://trac.wxwidgets.org/ticket/9821
        # (self.SendSizeEvent()) used in rootw, here would set sash position to
        # min pane size

        self.SetSashPosition(-80)

    def hide_history(self):
        self.Unsplit(self.hpanel)

    def get_filename(self):
        return self.filename

    def get_root(self):
        return self.treec.GetRootItem()

    def get_item_id(self, treeitem):
        return self.treec.GetPyData(treeitem)

    def get_item_index(self, treeitem):
        parent = self.get_item_parent(treeitem)
        siblings = self.get_item_children(parent)
        index = siblings.index(treeitem)
        return index

    def get_item_previous(self, treeitem):
        return self.treec.GetPrevSibling(treeitem)

    def get_item_next(self, treeitem):
        return self.treec.GetNextSibling(treeitem)

    def get_item_parent(self, treeitem):
        return self.treec.GetItemParent(treeitem)

    def get_item_ancestors(self, treeitem):
        ancestors = []

        def recurse(treeitem):
            parent = self.get_item_parent(treeitem)
            if parent:
                ancestors.append(parent)
                recurse(parent)

        recurse(treeitem)
        return ancestors

    def get_item_children(self, treeitem):
        child = self.treec.GetFirstChild(treeitem)
        children = []
        while child[0].IsOk():
            children.append(child[0])
            child = self.treec.GetNextChild(treeitem, cookie=child[1])
        return children

    def get_item_descendants(self, treeitem):
        descendants = []

        def recurse(treeitem):
            children = self.get_item_children(treeitem)
            descendants.extend(children)
            for child in children:
                recurse(child)

        recurse(treeitem)
        return descendants

    def set_item_title(self, treeitem, title):
        self.treec.SetItemText(treeitem, title)

    def set_item_font(self, treeitem, wxfont):
        self.treec.SetItemFont(treeitem, wxfont)

    def select_item(self, treeitem):
        self.treec.UnselectAll()
        # Note that SelectItem may actually unselect if the item is selected,
        # see http://trac.wxwidgets.org/ticket/11157
        # However in this case all the items have just been deselected, so no
        # check must be done
        self.treec.SelectItem(treeitem)

    def unselect_all_items(self):
        self.treec.UnselectAll()

    def add_item_to_selection(self, treeitem):
        # If the item is already selected, SelectItem would actually deselect
        # it, see http://trac.wxwidgets.org/ticket/11157
        if not self.treec.IsSelected(treeitem):
            self.treec.SelectItem(treeitem)

    def remove_item_from_selection(self, treeitem):
        # If the item is not selected, UnselectItem may actually select it, see
        # http://trac.wxwidgets.org/ticket/11157
        if self.treec.IsSelected(treeitem):
            self.treec.UnselectItem(treeitem)

    @staticmethod
    def make_item_title(text):
        title = text.partition('\n')[0]
        return title

    def is_database_root(self, treeitem):
        return self.treec.GetItemParent(treeitem) == self.treec.GetRootItem()

    def popup_item_menu(self, event):
        # Using a separate procedure for EVT_TREE_ITEM_MENU (instead of always
        # using EVT_RIGHT_DOWN) ensures a standard behaviour, e.g. selecting
        # the item if not selected unselecting all the others, or leaving the
        # selection untouched if clicking on an already selected item
        self._popup_context_menu(event.GetPoint())

    def popup_window_menu(self, event):
        # Use EVT_RIGHT_DOWN when clicking in areas without items, because in
        # that case EVT_TREE_ITEM_MENU is not triggered
        if not self.treec.HitTest(event.GetPosition())[0].IsOk():
            self.treec.UnselectAll()
            self._popup_context_menu(event.GetPosition())

        # Skip the event so that self.popup_item_menu can work correctly
        event.Skip()

    def _popup_context_menu(self, point):
        self.cmenu.update_items()
        popup_context_menu_event.signal(filename=self.filename)
        self.treec.PopupMenu(self.cmenu, point)

    def unselect_on_empty_areas(self, event):
        if not self.treec.HitTest(event.GetPosition())[0].IsOk():
            self.treec.UnselectAll()

        # Skipping the event ensures correct left click behaviour
        event.Skip()

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu


class ContextMenu(wx.Menu):
    parent = None
    sibling = None
    child = None
    moveup = None
    movedn = None
    movept = None
    edit = None
    delete = None

    def __init__(self, parent):
        wx.Menu.__init__(self)

        self.parent = parent

        self.sibling = wx.MenuItem(self, wx.GetApp().menu.database.ID_SIBLING,
                                   "Create s&ibling",
                                   "Create a sibling after the selected item")
        self.child = wx.MenuItem(self, wx.GetApp().menu.database.ID_CHILD,
                                 "Create &sub-item",
                                 "Create a child for the selected item")
        self.moveup = wx.MenuItem(self, wx.GetApp().menu.database.ID_MOVE_UP,
                                  "&Move item up",
                                  "Swap the selected item with the one above")
        self.movedn = wx.MenuItem(self, wx.GetApp().menu.database.ID_MOVE_DOWN,
                                  "Mo&ve item down",
                                  "Swap the selected item with the one below")
        self.movept = wx.MenuItem(self, wx.GetApp().menu.database.ID_MOVE_PARENT,
                                  "M&ove item to parent",
                           "Move the selected item as a sibling of its parent")
        self.edit = wx.MenuItem(self, wx.GetApp().menu.database.ID_EDIT,
                                "&Edit item",
                                "Open the selected item in the editor")
        self.delete = wx.MenuItem(self, wx.GetApp().menu.database.ID_DELETE,
                                  "&Delete items", "Delete the selected items")

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

    def reset_items(self):
        self.sibling.Enable(False)
        self.child.Enable(False)
        self.moveup.Enable(False)
        self.movedn.Enable(False)
        self.movept.Enable(False)
        self.edit.Enable(False)
        self.delete.Enable(False)

        reset_context_menu_event.signal(filename=self.parent.filename)

    def update_items(self):
        self.reset_items()

        sel = self.parent.get_selections()

        if len(sel) == 1:
            self.sibling.Enable()
            self.child.Enable()

            if self.parent.get_item_previous(sel[0]).IsOk():
                self.moveup.Enable()

            if self.parent.get_item_next(sel[0]).IsOk():
                self.movedn.Enable()

            if not self.parent.is_database_root(sel[0]):
                self.movept.Enable()

            self.edit.Enable()
            self.delete.Enable()

        elif len(sel) > 1:
            self.edit.Enable()
            self.delete.Enable()

        else:
            self.sibling.Enable()


class TabContextMenu(wx.Menu):
    filename = None
    save = None
    saveas = None
    backup = None
    close = None

    def __init__(self, filename):
        wx.Menu.__init__(self)
        self.filename = filename

        self.undo = wx.MenuItem(self, wx.GetApp().menu.database.ID_UNDO,
                                                                       "&Undo")
        self.redo = wx.MenuItem(self, wx.GetApp().menu.database.ID_REDO,
                                                                       "&Redo")
        self.save = wx.MenuItem(self, wx.GetApp().menu.file.ID_SAVE, "&Save")
        self.saveas = wx.MenuItem(self, wx.GetApp().menu.file.ID_SAVE_AS,
                                                                 "Sav&e as...")
        self.backup = wx.MenuItem(self, wx.GetApp().menu.file.ID_BACKUP,
                                                             "Save &backup...")
        self.close = wx.MenuItem(self, wx.GetApp().menu.file.ID_CLOSE_DB,
                                                                      "&Close")

        self.undo.SetBitmap(wx.ArtProvider.GetBitmap('@undodb', wx.ART_MENU))
        self.redo.SetBitmap(wx.ArtProvider.GetBitmap('@redodb', wx.ART_MENU))
        self.save.SetBitmap(wx.ArtProvider.GetBitmap('@save', wx.ART_MENU))
        self.saveas.SetBitmap(wx.ArtProvider.GetBitmap('@saveas', wx.ART_MENU))
        self.backup.SetBitmap(wx.ArtProvider.GetBitmap('@backup', wx.ART_MENU))
        self.close.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))

        self.AppendItem(self.undo)
        self.AppendItem(self.redo)
        self.AppendSeparator()
        self.AppendItem(self.save)
        self.AppendItem(self.saveas)
        self.AppendItem(self.backup)
        self.AppendSeparator()
        self.AppendItem(self.close)

    def update(self):
        self.undo.Enable(False)
        self.redo.Enable(False)
        self.save.Enable(False)

        if core_api.preview_undo_tree(self.filename):
            self.undo.Enable()

        if core_api.preview_redo_tree(self.filename):
            self.redo.Enable()

        if core_api.check_pending_changes(self.filename):
            self.save.Enable()
