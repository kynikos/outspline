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
    def __init__(self, database, filename):
        super(Model, self).__init__()
        self.database = database
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
        # The internal search doesn't work with IconText items ****************************
        #   Returning None seems to disable it ********************************************
        #     Ask for other possible unwanted consequences ********************************
        #   https://groups.google.com/d/msg/wxpython-users/QvSesrnD38E/31l8f6AzIhAJ *******
        return None#"string"  # ***********************************************************

    def GetValue(self, item, col):
        id_ = self.ItemToObject(item)
        label = self.database.get_item_label(id_)
        icon = self.database.get_item_icon(id_)
        return dv.DataViewIconText(label, icon)


class Database(wx.SplitterWindow):
    # Mark private methods **************************************************************
    # Addresses #260 ********************************************************************
    # Fixes #334 ************************************************************************
    # Addresses #336 ********************************************************************
    def __init__(self, filename):
        super(Database, self).__init__(wx.GetApp().nb_left,
                                                    style=wx.SP_LIVE_UPDATE)

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)

        self.filename = filename
        self.data = {}

    def _post_init(self):
        # Is DataViewCtrl stealing Ctrl+n, Ctrl+p, Ctrl+f and others? *********************************
        #   All the other DataViewCtrl's are doing the same... ****************************************
        #   Also, the text search doesn't work ********************************************************
        #   https://groups.google.com/d/msg/wxpython-users/1sUPp766uXU/0J22mUrkzoAJ *******************
        #   Try to use a custom renderer for the items ************************************************
        #     Also use it to draw variable-width icons! ***********************************************
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

        # Merge into the Properties constructor? ******************************************************
        creating_tree_event.signal(filename=self.filename)

        # Store an ImageList only *after* instantiating the class, because its
        # size must be calculated after the various plugins have added their
        # properties, which requires the filename to be in the dictionary
        # Use a separate ImageList for each database, as they may support a
        # different subset of the installed plugins
        # Merge into the Properties constructor? ******************************************************
        self.properties.init_image_list()

        # Initialize the tree only *after* instantiating the class (and storing
        # an ImageList), because actions like the creation of item images rely
        # on the filename to be in the dictionary
        # Also maybe initialize the properties from the plugins directly here ************************
        #   instead of handling the open_database_event **********************************************
        for row in core_api.get_all_items(self.filename):
            self._init_item_data(row["I_id"], row["I_text"])

        self.dvmodel = Model(self, self.filename)
        self.treec.AssociateModel(self.dvmodel)
        # DataViewModel is reference counted (derives from RefCounter), the
        # count needs to be decreased explicitly here to avoid memory leaks
        # This is bullshit, it crashes if closing all databases *****************************
        #self.dvmodel.DecRef()

        self.treec.AppendIconTextColumn('Item', 0)

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
                    self.move_item(item, par, mode=0)
                else:
                    prev = self.find_item(previous)
                    self.move_item(item, prev, mode='after')

    def _handle_history_remove(self, kwargs):
        # Check ***************************************************************************
        filename = kwargs['filename']
        id_ = kwargs['id_']

        if filename == self.filename:
            item = self.find_item(id_)
            self.remove_items([item, ])

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

    def create(self, base=None, previd=0):
        # Rename to create_subtree if still needed ****************************************
        # Check ***************************************************************************
        # See if this can just handle an event from core **********************************
        if not base:
            base = self.treec.GetRootItem()

        # get_item_id takes a DV item now ***********************************************
        baseid = self.get_item_id(base)
        child = core_api.get_tree_item(self.filename, baseid, previd)

        if child:
            id_ = child['id_']

            self.insert_item(base, id_, child['text'])

            # titem is not returned anymore **********************************************
            self.create(base=titem, previd=0)
            self.create(base=base, previd=id_)

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

                for descid in core_api.get_item_descendants(id_):
                    self.treec.Select(self.get_tree_item(descid))

            return self.treec.GetSelections()
        else:
            return selection

    def move_item(self, treeitem, base, mode='append'):
        # Check ***************************************************************************
        # See if this can just handle the item update event from core *********************
        label = self.treec.GetItemText(treeitem)
        id_, properties = self.treec.GetItemPyData(treeitem)
        imageindex = self.treec.GetItemImage(treeitem)

        if mode in ('append', 'after', 'before') or isinstance(mode, int):
            # When moving down, add 1 to the destination index, because the ***************
            # move method first copies the item, and only afterwards deletes it
            self.data[id_] = [label, properties]
            # Must use the parent DVitem ****************************************************
            self.dvmodel.ItemAdded(base, self.get_tree_item(id_))
        else:
            raise ValueError()

        while self.treec.ItemHasChildren(treeitem):
            first = self.treec.GetFirstChild(treeitem)
            # Always use append mode for the descendants
            # newtreeitem is not returned anymore *****************************************
            self.move_item(first[0], newtreeitem)

        # Verify *******************************************************************************
        # Do not use remove_items, as self.titems has already been updated
        # here, and using remove_items would remove the moved item from
        # self.titems
        self.treec.Delete(treeitem)

        return newtreeitem

    def remove_items(self, treeitems):
        # Re-implement using the event from core ******************************************************
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

    def get_item_icon(self, id_):
        return self.properties.get_icon(self.data[id_][1])

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
            bits_to_colour = {
                1: wx.Colour(),
            }
            bits_to_colour[1].SetFromString(config['color'])

            self.multiline_shift, self.multiline_mask = properties.add(1,
                                                    multichar, bits_to_colour)

    def get_item_multiline_state(self, text, label):
        if text != label:
            bits = 1 << self.multiline_shift
        else:
            bits = 0

        return (bits, self.multiline_mask)


class Properties(object):
    def __init__(self, widget):
        self.widget = widget

        self.SPACING = 2
        self.bitsn = 0
        # Use a list also to preserve the order of the properties
        self.char_data = []
        self.bits_to_image = {}

        self._init_font()
        self._compute_off_colour()

    def _init_font(self):
        self.font = self.widget.GetFont()
        self.font.SetWeight(wx.FONTWEIGHT_BOLD)

    def _compute_off_colour(self):
        self.bgcolour = self.widget.GetBackgroundColour()
        avg = (self.bgcolour.Red() + self.bgcolour.Green() +
                                                    self.bgcolour.Blue()) // 3
        DIFF = 16

        if avg > 127:
            self.off_colour = wx.Colour(max((self.bgcolour.Red() - DIFF, 0)),
                                      max((self.bgcolour.Green() - DIFF, 0)),
                                      max((self.bgcolour.Blue() - DIFF, 0)))
        else:
            self.off_colour = wx.Colour(min((self.bgcolour.Red() + DIFF, 255)),
                                    min((self.bgcolour.Green() + DIFF, 255)),
                                    min((self.bgcolour.Blue() + DIFF, 255)))

    def add(self, bitsn, character, bits_to_colour):
        dc = wx.MemoryDC()
        dc.SelectObject(wx.NullBitmap)
        dc.SetFont(self.font)
        extent = dc.GetTextExtent(character)

        # Be safe and only check the width, because if in future versions of
        # wxPython, dc.GetTextExtent returned a Size object instead of a tuple,
        # it would never match (0, 0)
        if extent[0] != 0:
            shift = self.bitsn
            mask = int('1' * bitsn, 2) << shift
            self.bitsn += bitsn
            shifted_bits_to_colour = {}

            for bits in bits_to_colour:
                shifted_bits_to_colour[bits << shift] = bits_to_colour[bits]

            self.char_data.append((mask, character, extent,
                                                    shifted_bits_to_colour))

        return (shift, mask)

    def _compute_required_size(self):
        width = 0
        height = 0

        for data in self.char_data:
            width += data[2][0] + self.SPACING
            height = max((height, data[2][1]))

        width -= self.SPACING

        return (width, height)

    def init_image_list(self):
        # Sort char_data by character to make sure that the icons always appear
        # in the same order regardless of race conditions when loading the
        # plugins
        self.char_data.sort(key=lambda data: data[1])

        self.required_size = self._compute_required_size()

        # required_size is 0 if no properties have been added, or if they've
        # been added with empty strings
        if self.required_size == (0, 0):
            self.get_icon = self._get_icon_dummy
        else:
            self.get_icon = self._get_icon_real

        self.imagelist = wx.ImageList(*self.required_size)

    def get_icon(self, bits):
        # This method is re-assigned dynamically
        pass

    def _get_icon_real(self, bits):
        try:
            imageindex = self.bits_to_image[bits]
        except KeyError:
            bitmap = self._make_image(bits)
            imageindex = self.imagelist.Add(bitmap)
            self.bits_to_image[bits] = imageindex

        return self.imagelist.GetIcon(imageindex)

    def _get_icon_dummy(self, bits):
        # Used if no properties have been added
        # Test ****************************************************************************
        return wx.NullIcon

    def _make_image(self, item_bits):
        bitmap = wx.EmptyBitmap(*self.required_size, depth=32)

        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        dc.SetBackground(wx.Brush(self.bgcolour))
        dc.Clear()

        gc = wx.GraphicsContext.Create(dc)

        x = 0

        for property_bits, character, extent, bits_to_colour in self.char_data:
            bits = (property_bits & item_bits)

            try:
                colour = bits_to_colour[bits]
            except KeyError:
                colour = self.off_colour

            gc.SetFont(gc.CreateFont(self.font, colour))

            y = self.required_size[1] - extent[1]
            gc.DrawText(character, x, y)

            x += extent[0] + self.SPACING

        bitmap.SetMaskColour(self.bgcolour)
        dc.SelectObject(wx.NullBitmap)

        return bitmap


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
