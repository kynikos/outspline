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

import os
import wx
import wx.dataview as dv

from outspline.coreaux_api import Event
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api

import logs

creating_tree_event = Event()
reset_context_menu_event = Event()
popup_context_menu_event = Event()

dbs = {}


class Model(dv.PyDataViewModel):
    def __init__(self, filename):
        super(Model, self).__init__()
        self.filename = filename

    def IsContainer(self, item):
        return True

    def GetParent(self, item):
        if not item.IsOk():
            return dv.NullDataViewItem
        else:
            id_ = self.ItemToObject(item)
            pid = core_api.get_item_parent(self.filename, id_)

            if pid > 0:
                return self.ObjectToItem(pid)
            else:
                return dv.NullDataViewItem

    def GetChildren(self, parent, children):
        if not parent.IsOk():
            ids = core_api.get_root_items(self.filename)
        else:
            pid = self.ItemToObject(parent)
            ids = core_api.get_item_children(self.filename, pid)

        for id_ in ids:
            children.append(self.ObjectToItem(id_))

        return len(ids)

    def GetColumnCount(self):
        return 1

    def GetColumnType(self, col):
        # The native GTK widget used by DataViewCtrl would have an internal
        # "live" search feature which however unfortunately only seems to work
        # if the first column's type is purely string
        # https://groups.google.com/d/msg/wxpython-users/QvSesrnD38E/31l8f6AzIhAJ
        # Track as an upstream bug **********************************************************
        # Returning None seems to disable it
        # Are there any unwanted consequences? **********************************************
        #   https://groups.google.com/d/msg/wxpython-users/4nsv7x1DE-s/ljQHl9RTnuEJ *********
        return None

    def GetValue(self, item, col):
        id_ = self.ItemToObject(item)
        # For some reason Renderer needs a string *******************************************
        #   https://groups.google.com/forum/#!topic/wxpython-users/F9tqqwOcIFw **************
        return str(id_)


class Renderer(dv.PyDataViewCustomRenderer):
    def __init__(self, database, treec):
        super(Renderer, self).__init__()
        self.VMARGIN = 1
        self.GAP = 2
        self.ADDITIONAL_GAP = 4
        self.database = database

        self.deffont = treec.GetFont()
        self.fgcolor = treec.GetForegroundColour()
        self.iconfont = treec.GetFont()
        self.iconfont.SetWeight(wx.FONTWEIGHT_BOLD)

        dc = wx.MemoryDC()
        dc.SelectObject(wx.NullBitmap)
        dc.SetFont(self.deffont)
        # It shouldn't matter whether characters with descent are used or not,
        # but use "pb" for safety anyway
        extent = dc.GetTextExtent("pb")
        self.needed_height = extent[1] + self.VMARGIN * 2

    def SetValue(self, value):
        self.value = value
        self.label = self.database.get_item_label(int(value))
        self.teststr, self.strdata = self.database.get_item_properties(int(
                                                                        value))
        return True

    def GetValue(self):
        return self.value

    def GetSize(self):
        label = "".join((self.teststr, self.label))
        tsize = self.GetTextExtent(label)
        gapsw = (len(self.strdata)) * self.GAP + self.ADDITIONAL_GAP
        return wx.Size(tsize.GetWidth() + gapsw, self.needed_height)

    def Render(self, rect, dc, state):
        dc.SetFont(self.iconfont)
        xoffset = rect.GetX()

        for data in self.strdata:
            dc.SetTextForeground(data[1])
            dc.DrawText(data[0], xoffset, rect.GetY() + self.VMARGIN)
            xoffset += self.GetTextExtent(data[0])[0] + self.GAP

        xoffset += self.ADDITIONAL_GAP

        # Don't use self.RenderText as the official docs would suggest, because
        # it aligns vertically in a weird way
        dc.SetFont(self.deffont)
        dc.SetTextForeground(self.fgcolor)
        dc.DrawText(self.label, xoffset, rect.GetY() + self.VMARGIN)

        return True


class Database(wx.SplitterWindow):
    # Mark private methods **************************************************************
    # Addresses #260 ********************************************************************
    # Fixes #334 ************************************************************************
    # Addresses #336 ********************************************************************
    # Check all the upstream bugs now that the new wxPython version has been ************
    #   released ************************************************************************
    def __init__(self, filename):
        super(Database, self).__init__(wx.GetApp().nb_left,
                                                    style=wx.SP_LIVE_UPDATE)

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)

        self.filename = filename
        self.data = {}

    def _post_init(self):
        # The native GTK widget used by DataViewCtrl would have an internal
        # "live" search feature which steals some keyboard shortcuts: Ctrl+n,
        # Ctrl+p, Ctrl+f, Ctrl+a, Ctrl+Shift+a
        # https://groups.google.com/d/msg/wxpython-users/1sUPp766uXU/0J22mUrkzoAJ
        # Track as an upstream bug **********************************************************
        # Ctrl+f can be recovered with a hack explained above in the Model's
        # GetColumnType method
        # Show the natively working shortcuts in the menu, or in comments in ********************
        #   the config file (also for the other DataViewCtrl's) *********************************
        self.treec = dv.DataViewCtrl(self, style=dv.DV_MULTIPLE |
                                            dv.DV_ROW_LINES | dv.DV_NO_HEADER)

        # *****************************************************************************
        def test(event):
            print("TEEEEEEEEST")  # ***************************************************

        id_ = wx.NewId()
        accels = [
            (wx.ACCEL_NORMAL, ord("f"), id_),
            (wx.ACCEL_CTRL, ord("f"), id_),
            (wx.ACCEL_CTRL, ord("n"), id_),
            (wx.ACCEL_CTRL, ord("p"), id_),
        ]
        self.treec.Bind(wx.EVT_BUTTON, test, id=id_)
        acctable = wx.AcceleratorTable(accels)
        self.treec.SetAcceleratorTable(acctable)
        # *****************************************************************************

        self.cmenu = ContextMenu(self)
        self.ctabmenu = TabContextMenu(self.filename)

        self.logspanel = logs.LogsPanel(self, self.filename)
        self.dbhistory = logs.DatabaseHistory(self.logspanel,
                                    self.logspanel.get_panel(), self.filename,
                                    self.treec.GetBackgroundColour())

        self.properties = Properties(self.treec)
        self.base_properties = DBProperties(self.properties)

        creating_tree_event.signal(filename=self.filename)

        # Initialize the icons only *after* the various plugins have added
        # their properties
        self.properties.post_init()

        # Initialize the tree only *after* instantiating the class (and
        # initilizing the icons), because actions like the creation of item
        # images rely on the filename to be in the dictionary
        for row in core_api.get_all_items(self.filename):
            self._init_item_data(row["I_id"], row["I_text"])

        self.dvmodel = Model(self.filename)
        self.treec.AssociateModel(self.dvmodel)
        # DataViewModel is reference counted (derives from RefCounter), the
        # count needs to be decreased explicitly here to avoid memory leaks
        # This is bullshit, it crashes if closing all databases *****************************
        #self.dvmodel.DecRef()

        dvrenderer = Renderer(self, self.treec)
        dvcolumn = dv.DataViewColumn("Item", dvrenderer, 0,
                                                        align=wx.ALIGN_LEFT)
        self.treec.AppendColumn(dvcolumn)

        self.Initialize(self.treec)

        # Initialize the logs panel *after* signalling creating_tree_event,
        # which is used to add plugin logs
        self.logspanel.initialize()

        nb_left = wx.GetApp().nb_left
        nb_left.add_page(self, os.path.basename(self.filename), select=True)

        # The logs panel must be shown only *after* adding the page to the
        # notebook, otherwise *for*some*reason* the databases opened
        # automatically by the sessions manager (those opened manually aren't
        # affected) will have the sash of the SplitterWindow not correctly
        # positioned (only if using SetSashGravity)
        if wx.GetApp().logs_configuration.is_shown():
            self.show_logs()

        self.treec.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU,
                                                        self._popup_item_menu)

        core_api.bind_to_update_item(self._handle_update_item)
        core_api.bind_to_deleting_item(self._handle_deleting_item)
        core_api.bind_to_deleted_item_2(self._handle_deleted_item)
        core_api.bind_to_history_insert(self._handle_history_insert)
        core_api.bind_to_history_update(self._handle_history_update)
        core_api.bind_to_history_remove(self._handle_history_remove)

        # Check how this bug is currently tracked ****************************************************
        """self.treec.Bind(wx.EVT_LEFT_DOWN, self._unselect_on_empty_areas)

    def _unselect_on_empty_areas(self, event):
        if not self.treec.HitTest(event.GetPosition())[0].IsOk():
            self.treec.UnselectAll()

        # Skipping the event ensures correct left click behaviour
        event.Skip()"""

    def _handle_update_item(self, kwargs):
        # Check ***************************************************************************
        # Don't update an item label only when editing the text area, as there
        # may be other plugins that edit an item's text (e.g links)
        # kwargs['text'] could be None if the query updated the position of the
        # item and not its text
        if kwargs['filename'] == self.filename and kwargs['text'] is not None:
            self.set_item_label(kwargs['id_'], kwargs['text'])

    def _handle_deleting_item(self, kwargs):
        # Check ***************************************************************************
        if kwargs['filename'] == self.filename:
            item = self.get_tree_item(kwargs['id_'])
            pid = kwargs['parent']

            if pid > 0:
                parent = self.get_tree_item(pid)
            else:
                parent = self.get_root()

            self.dvmodel.ItemDeleted(parent, item)

    def _handle_deleted_item(self, kwargs):
        # Check ***************************************************************************
        if kwargs['filename'] == self.filename:
            self.remove_items([kwargs['id_'], ])

    def _handle_history_insert(self, kwargs):
        # Check ***************************************************************************
        filename = kwargs['filename']
        if filename == self.filename:
            id_ = kwargs['id_']
            parent = kwargs['parent']
            previous = kwargs['previous']
            text = kwargs['text']

            if previous == 0:
                pitem = self.get_tree_item(parent)
            else:
                # Must use parent DVitem *******************************************************
                pitem = self.get_tree_item(previous)

            self.insert_item(pitem, id_, text)

    def _handle_history_update(self, kwargs):
        # Check ***************************************************************************
        filename = kwargs['filename']
        if filename == self.filename:
            id_ = kwargs['id_']
            parent = kwargs['parent']
            previous = kwargs['previous']
            text = kwargs['text']

            item = self.find_item(id_)

            # Verify *******************************************************************************
            # Reset label and image before moving the item, otherwise the item
            # has to be found again, or the program crashes
            # set_item_label now takes an id_ *********************************************
            self.set_item_label(item, text)
            self.update_tree_item(id_)

            # get_item_id takes a DV item now ***********************************************
            if self.get_item_id(self.get_item_parent(item)) != parent or \
                                (self.get_item_previous(item).IsOk() and \
                                self.get_item_id(
                                self.get_item_previous(item)) != previous) or \
                                (not self.get_item_previous(item).IsOk() and \
                                previous != 0):
                if previous == 0:
                    par = self.find_item(parent)
                    # move_item has changed *********************************************
                    self.move_item(item, par, mode=0)
                else:
                    prev = self.find_item(previous)
                    # move_item has changed *********************************************
                    self.move_item(item, prev, mode='after')

    def _handle_history_remove(self, kwargs):
        # Check ***************************************************************************
        filename = kwargs['filename']
        id_ = kwargs['id_']

        if filename == self.filename:
            self.remove_items([id_, ])

    @classmethod
    def open(cls, filename):
        global dbs
        dbs[filename] = cls(filename)

        dbs[filename]._post_init()

    def insert_item(self, parent, id_, text):
        # Check ****************************************************************************
        # See if this can just handle the item insert event from core **********************
        self._init_item_data(id_, text)
        self.dvmodel.ItemAdded(parent, self.get_tree_item(id_))

    def insert_subtree(self, parent, previd=0):
        # Check ***************************************************************************
        # See if this can just handle the item insert event from core **********************

        # get_item_id takes a DV item now ***********************************************
        baseid = self.get_item_id(base)
        child = core_api.get_tree_item(self.filename, baseid, previd)

        if child:
            id_ = child['id_']

            self.insert_item(base, id_, child['text'])

            # titem is not returned anymore **********************************************
            self.insert_subtree(base=titem, previd=0)
            self.insert_subtree(base=base, previd=id_)

    def _init_item_data(self, id_, text):
        label = self._make_item_label(text)
        multiline_bits, multiline_mask = \
                    self.base_properties.get_item_multiline_state(text, label)
        properties = self._compute_property_bits(0, multiline_bits,
                                                                multiline_mask)
        self.data[id_] = [label, properties]

    def find_item(self, id_):
        # Re-implement if still needed ************************************************************
        return self.titems[id_].GetId()

    def get_selections(self, none=True, many=True, descendants=None):
        selection = self.treec.GetSelections()

        if (not none and len(selection) == 0) or (not many and
                                                        len(selection) > 1):
            return False
        elif descendants == True:
            for item in selection:
                id_ = self.get_item_id(item)

                for descid in core_api.get_item_descendants(self.filename,
                                                                        id_):
                    self.treec.Select(self.get_tree_item(descid))

            return self.treec.GetSelections()
        else:
            return selection

    def move_item(self, id_, item):
        pid = core_api.get_item_parent(self.filename, id_)

        if pid > 0:
            parent = self.get_tree_item(pid)
        else:
            parent = self.get_root()

        self.dvmodel.ItemDeleted(parent, item)
        self.dvmodel.ItemAdded(parent, item)
        self._move_subtree(id_, item)

    def move_item_to_parent(self, oldpid, id_, item):
        newpid = core_api.get_item_parent(self.filename, id_)

        # oldpid cannot be 0 here because core_api.move_item_to_parent
        # succeded, which means that it wasn't the root item
        oldparent = self.get_tree_item(oldpid)

        if newpid > 0:
            newparent = self.get_tree_item(newpid)
        else:
            newparent = self.get_root()

        self.dvmodel.ItemDeleted(oldparent, item)
        self.dvmodel.ItemAdded(newparent, item)
        self._move_subtree(id_, item)

        if not core_api.has_item_children(self.filename, oldpid):
            # This seems to be the only way to hide the arrow next to a parent
            # that has just lost its last child
            self.dvmodel.ItemDeleted(newparent, oldparent)
            self.dvmodel.ItemAdded(newparent, oldparent)

    def _move_subtree(self, id_, item):
        childids = core_api.get_item_children(self.filename, id_)

        for childid in childids:
            child = self.get_tree_item(childid)
            self.dvmodel.ItemAdded(item, child)
            self._move_subtree(childid, child)

    def remove_items(self, ids):
        # ********************************************************************************
        # All algorithms calling this method should clear the tree items *****************
        #   *beforehand* now, see how it's done in the menubar module ********************
        # Remove only 1 item? ************************************************************
        for id_ in ids:
            del self.data[id_]

        # ***********************************************************************************
        return False
        # When deleting items, make sure to delete first those without
        # children, otherwise crashes without exceptions or errors could occur
        while treeitems:
            for item in treeitems[:]:
                if not self.treec.ItemHasChildren(item):
                    del treeitems[treeitems.index(item)]
                    id_ = self.treec.GetItemPyData(item)[0]
                    self.treec.Delete(item)
                    del self.data[id_]

    def close(self):
        global dbs
        del dbs[self.filename]

    def show_logs(self):
        self.SplitHorizontally(self.treec, self.logspanel.get_panel())
        self.SetSashGravity(1.0)
        self.SetSashPosition(-80)

    def hide_logs(self):
        self.Unsplit(self.logspanel.get_panel())

    def get_filename(self):
        return self.filename

    def get_root(self):
        return dv.NullDataViewItem

    def get_item_id(self, item):
        return self.dvmodel.ItemToObject(item)

    def get_tree_item(self, id_):
        return self.dvmodel.ObjectToItem(id_)

    def get_item_index(self, treeitem):
        # Gonna be useless **************************************************************
        parent = self.get_item_parent(treeitem)
        siblings = self.get_item_children(parent)
        index = siblings.index(treeitem)
        return index

    def get_item_previous(self, treeitem):
        # Gonna be useless **************************************************************
        return self.treec.GetPrevSibling(treeitem)

    def get_item_parent(self, treeitem):
        # Gonna be useless **************************************************************
        return self.treec.GetItemParent(treeitem)

    @staticmethod
    def _make_item_label(text):
        return text.partition('\n')[0]

    def get_item_label(self, id_):
        return self.data[id_][0]

    def get_item_properties(self, id_):
        return self.properties.get(self.data[id_][1])

    def set_item_label(self, id_, text):
        label = self._make_item_label(text)
        self.data[id_][0] = label
        multiline_bits, multiline_mask = \
                    self.base_properties.get_item_multiline_state(text, label)
        self.update_item_properties(id_, multiline_bits, multiline_mask)
        self.update_tree_item(id_)

    def update_tree_item(self, id_):
        self.dvmodel.ItemChanged(self.get_tree_item(id_))

    @staticmethod
    def _compute_property_bits(old_property_bits, new_property_bits,
                                                                property_mask):
        return (old_property_bits & ~property_mask) | new_property_bits

    def update_item_properties(self, id_, property_bits, property_mask):
        self.data[id_][1] = self._compute_property_bits(self.data[id_][1],
                                                property_bits, property_mask)

    def get_properties(self):
        return self.properties

    def get_logs_panel(self):
        return self.logspanel

    def select_item(self, id_):
        self.treec.UnselectAll()
        self.treec.Select(self.get_tree_item(id_))

    def unselect_all_items(self):
        self.treec.UnselectAll()

    def add_item_to_selection(self, id_):
        self.treec.Select(self.get_tree_item(id_))

    def remove_item_from_selection(self, id_):
        self.treec.Unselect(self.get_tree_item(id_))

    def _popup_item_menu(self, event):
        self.cmenu.update_items()
        popup_context_menu_event.signal(filename=self.filename)
        self.treec.PopupMenu(self.cmenu, event.GetPosition())

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu


class DBProperties(object):
    def __init__(self, properties):
        config = coreaux_api.get_interface_configuration('wxgui')('TreeIcons')
        multichar = config['symbol']

        if multichar != '':
            bits_to_color = {
                1: wx.Colour(),
            }
            bits_to_color[1].SetFromString(config['color'])

            self.multiline_shift, self.multiline_mask = properties.add(1,
                                                    multichar, bits_to_color)

    def get_item_multiline_state(self, text, label):
        if text != label:
            bits = 1 << self.multiline_shift
        else:
            bits = 0

        return (bits, self.multiline_mask)


class Properties(object):
    def __init__(self, widget):
        self.widget = widget

        self.bitsn = 0
        self.data = []
        self.bits_to_chars = {}

    def add(self, bitsn, character, bits_to_color):
        shift = self.bitsn
        mask = int('1' * bitsn, 2) << shift
        self.bitsn += bitsn
        shifted_bits_to_colors = {}

        for bits in bits_to_color:
            shifted_bits_to_colors[bits << shift] = bits_to_color[bits]

        self.data.append((mask, character, shifted_bits_to_colors))

        return (shift, mask)

    def post_init(self):
        # char_data is empty if no properties have been added
        if len(self.data) < 1:
            self.get = self._get_dummy
        else:
            self.get = self._get_real

    def get(self, bits):
        # This method is re-assigned dynamically
        pass

    def _get_real(self, bits):
        try:
            return self.bits_to_chars[bits]
        except KeyError:
            teststr, strdata = self._compute_data(bits)
            self.bits_to_chars[bits] = teststr, strdata
            return teststr, strdata

    def _get_dummy(self, bits):
        # Used if no properties have been added
        return ("", [])

    def _compute_data(self, item_bits):
        teststr = ""
        strdata = []

        for property_bits, character, bits_to_colors in self.data:
            bits = (property_bits & item_bits)

            try:
                color = bits_to_colors[bits]
            except KeyError:
                pass
            else:
                teststr += character
                strdata.append((character, color))

        return (teststr, strdata)


class ContextMenu(wx.Menu):
    def __init__(self, parent):
        wx.Menu.__init__(self)

        self.sibling_label_1 = "Create &item"
        self.sibling_label_2 = "Create s&ibling"

        self.parent = parent

        self.sibling = wx.MenuItem(self, wx.GetApp().menu.database.ID_SIBLING,
                                                        self.sibling_label_1)
        self.child = wx.MenuItem(self, wx.GetApp().menu.database.ID_CHILD,
                                                            "Create c&hild")
        self.moveup = wx.MenuItem(self, wx.GetApp().menu.database.ID_MOVE_UP,
                                                            "&Move item up")
        self.movedn = wx.MenuItem(self, wx.GetApp().menu.database.ID_MOVE_DOWN,
                                                            "Mo&ve item down")
        self.movept = wx.MenuItem(self,
                                    wx.GetApp().menu.database.ID_MOVE_PARENT,
                                    "M&ove item to parent")
        self.edit = wx.MenuItem(self, wx.GetApp().menu.database.ID_EDIT,
                                                                "&Edit item")
        self.delete = wx.MenuItem(self, wx.GetApp().menu.database.ID_DELETE,
                                                            "&Delete items")

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

    def _reset_items(self):
        self.sibling.Enable(False)
        self.child.Enable(False)
        self.moveup.Enable(False)
        self.movedn.Enable(False)
        self.movept.Enable(False)
        self.edit.Enable(False)
        self.delete.Enable(False)
        self.sibling.SetItemLabel(self.sibling_label_1)

        reset_context_menu_event.signal(filename=self.parent.filename)

    def update_items(self):
        self._reset_items()

        sel = self.parent.get_selections()

        if len(sel) == 1:
            self.sibling.Enable()
            self.sibling.SetItemLabel(self.sibling_label_2)
            self.child.Enable()

            id_ = self.parent.get_item_id(sel[0])

            if core_api.get_item_previous(self.parent.filename, id_):
                self.moveup.Enable()

            if core_api.get_item_next(self.parent.filename, id_):
                self.movedn.Enable()

            if not core_api.is_item_root(self.parent.filename, id_):
                self.movept.Enable()

            self.edit.Enable()
            self.delete.Enable()

        elif len(sel) > 1:
            self.edit.Enable()
            self.delete.Enable()

        else:
            self.sibling.Enable()


class TabContextMenu(wx.Menu):
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
        self.properties = wx.MenuItem(self,
                            wx.GetApp().menu.file.ID_PROPERTIES, "&Properties")
        self.close = wx.MenuItem(self, wx.GetApp().menu.file.ID_CLOSE_DB,
                                                                      "&Close")

        self.undo.SetBitmap(wx.ArtProvider.GetBitmap('@undodb', wx.ART_MENU))
        self.redo.SetBitmap(wx.ArtProvider.GetBitmap('@redodb', wx.ART_MENU))
        self.save.SetBitmap(wx.ArtProvider.GetBitmap('@save', wx.ART_MENU))
        self.saveas.SetBitmap(wx.ArtProvider.GetBitmap('@saveas', wx.ART_MENU))
        self.backup.SetBitmap(wx.ArtProvider.GetBitmap('@backup', wx.ART_MENU))
        self.properties.SetBitmap(wx.ArtProvider.GetBitmap('@properties',
                                                                wx.ART_MENU))
        self.close.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))

        self.AppendItem(self.undo)
        self.AppendItem(self.redo)
        self.AppendSeparator()
        self.AppendItem(self.save)
        self.AppendItem(self.saveas)
        self.AppendItem(self.backup)
        self.AppendSeparator()
        self.AppendItem(self.properties)
        self.AppendSeparator()
        self.AppendItem(self.close)

    def update(self):
        if core_api.preview_undo_tree(self.filename):
            self.undo.Enable()
        else:
            self.undo.Enable(False)

        if core_api.preview_redo_tree(self.filename):
            self.redo.Enable()
        else:
            self.redo.Enable(False)

        if core_api.check_pending_changes(self.filename):
            self.save.Enable()
        else:
            self.save.Enable(False)
