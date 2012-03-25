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

import os
import wx

from organism.coreaux_api import Event 
import organism.core_api as core_api

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
    hpanel = None
    history = None
    accels = None
    accelstree = None
    
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
        
        self.hpanel = wx.Panel(self)
        bs = wx.BoxSizer(wx.VERTICAL)
        self.hpanel.SetSizer(bs)
        
        self.history = history.HistoryWindow(self.hpanel, self.filename)
        
        line = wx.StaticLine(self.hpanel, size=(1, 1), style=wx.LI_HORIZONTAL)
        
        bs.Add(line, flag=wx.EXPAND)
        bs.Add(self.history, 1, flag=wx.EXPAND)
        
        self.hpanel.Show(False)
        self.Initialize(self.treec)
        
        if history.is_shown():
            self.show_history()
        
        self.create()
        
        self.accels = [(wx.ACCEL_SHIFT | wx.ACCEL_CTRL, ord('s'), 
                        wx.GetApp().menu.file.ID_SAVE),
                       (wx.ACCEL_SHIFT | wx.ACCEL_CTRL, ord('a'),
                        wx.GetApp().menu.file.ID_SAVE_ALL),
                       (wx.ACCEL_CTRL, ord('w'),
                        wx.GetApp().menu.file.ID_CLOSE_DB),
                       (wx.ACCEL_SHIFT | wx.ACCEL_CTRL, ord('w'),
                        wx.GetApp().menu.file.ID_CLOSE_DB_ALL),
                       (wx.ACCEL_CTRL, ord('z'),
                        wx.GetApp().menu.database.ID_UNDO),
                       (wx.ACCEL_CTRL, ord('y'),
                        wx.GetApp().menu.database.ID_REDO)]
        
        self.accelstree = [(wx.ACCEL_NORMAL, wx.WXK_INSERT,
                            wx.GetApp().menu.database.ID_SIBLING),
                           (wx.ACCEL_SHIFT, wx.WXK_INSERT,
                            wx.GetApp().menu.database.ID_CHILD),
                           (wx.ACCEL_SHIFT, wx.WXK_UP,
                            wx.GetApp().menu.database.ID_MOVE_UP),
                           (wx.ACCEL_SHIFT, wx.WXK_DOWN,
                            wx.GetApp().menu.database.ID_MOVE_DOWN),
                           (wx.ACCEL_SHIFT, wx.WXK_LEFT,
                            wx.GetApp().menu.database.ID_MOVE_PARENT),
                           (wx.ACCEL_NORMAL, wx.WXK_RETURN,
                            wx.GetApp().menu.database.ID_EDIT),
                           (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ENTER,
                            wx.GetApp().menu.database.ID_EDIT),
                           (wx.ACCEL_NORMAL, wx.WXK_DELETE,
                            wx.GetApp().menu.database.ID_DELETE)]
        
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))
        self.treec.SetAcceleratorTable(wx.AcceleratorTable(self.accelstree))
        
        self.treec.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.veto_label_edit)
        self.treec.Bind(wx.EVT_TREE_ITEM_MENU, self.popup_item_menu)
        
        core_api.bind_to_history_insert(self.handle_history_insert)
        core_api.bind_to_history_update(self.handle_history_update)
        core_api.bind_to_history_remove(self.handle_history_remove)
        
    def veto_label_edit(self, event):
        event.Veto()

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
    
    def insert_item(self, base, mode, label=None, data=None, id_=None):
        # The empty string is a valid label
        if not label and label != '':
            label = self.make_item_title(core_api.get_item_text(self.filename,
                                                                id_))
        
        if not data:
            data = wx.TreeItemData(int(id_))
        
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
        elif descendants != None:
            for item in selection:
                if descendants == False:
                    for ancestor in self.get_item_ancestors(item):
                        if ancestor in selection:
                            self.treec.UnselectItem(ancestor)
                elif descendants == True:
                    for descendant in self.get_item_descendants(item):
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
        # (self.SendSizeEvent()) used in rootw, here sets sash position to
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
        return(children)

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

    def select_item(self, treeitem):
        self.treec.UnselectAll()
        self.add_item_to_selection(treeitem)
    
    @staticmethod
    def make_item_title(text):
        title = text.partition('\n')[0]
        return title

    def remove_item_from_selection(self, treeitem):
        self.treec.UnselectItem(treeitem)
    
    def add_item_to_selection(self, treeitem):
        self.treec.SelectItem(treeitem)
    
    def is_database_root(self, treeitem):
        return self.treec.GetItemParent(treeitem) == self.treec.GetRootItem()
        
    def popup_item_menu(self, event):
        self.treec.SetFocus()
        
        self.cmenu.update_items()
        popup_context_menu_event.signal(filename=self.filename)
        
        self.treec.PopupMenu(self.cmenu, event.GetPoint())
    
    def add_accelerators(self, accels):
        self.accels.extend(accels)
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))
    
    def add_tree_accelerators(self, accels):
        self.accelstree.extend(accels)
        self.treec.SetAcceleratorTable(wx.AcceleratorTable(self.accelstree))


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
                                 "Switch the selected item with the one above")
        self.movedn = wx.MenuItem(self, wx.GetApp().menu.database.ID_MOVE_DOWN,
                                  "Mo&ve item down",
                                 "Switch the selected item with the one below")
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
    
    def insert_item(self, pos, text, id_=wx.ID_ANY, help='', sep='none',
                    kind='normal', sub=None, icon=None):
        kinds = {'normal': wx.ITEM_NORMAL,
                 'check': wx.ITEM_CHECK,
                 'radio': wx.ITEM_RADIO}
        
        item = wx.MenuItem(parentMenu=self, id=id_, text=text, help=help,
                           kind=kinds[kind], subMenu=sub)
        
        if icon is not None:
            item.SetBitmap(wx.ArtProvider.GetBitmap(icon, wx.ART_MENU))
        
        if pos == -1:
            if sep in ('up', 'both'):
                self.AppendSeparator()
            self.AppendItem(item)
            if sep in ('down', 'both'):
                self.AppendSeparator()
        else:
            # Start from bottom, so that it's always possible to use pos
            if sep in ('down', 'both'):
                self.InsertSeparator(pos)
            self.InsertItem(pos, item)
            if sep in ('up', 'both'):
                self.InsertSeparator(pos)
        return item
    
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
            self.delete.Enable()
        
        else:
            self.sibling.Enable()
