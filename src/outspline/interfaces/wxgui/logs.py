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
import wx.dataview
import time as time_

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api


class LogsConfiguration(object):
    def __init__(self):
        config = coreaux_api.get_interface_configuration('wxgui')

        # Use a copy of the original constant, so that every time a database is
        # opened it reads the current value, and not the one stored in the
        # configuration
        # Do not put this into the DatabaseHistory class, since it must be a
        # database-independent value
        self.show_status = config.get_bool('show_logs')

    def is_shown(self):
        return self.show_status

    def set_shown(self, flag=True):
        self.show_status = flag


class LogsPanel(object):
    def __init__(self, parent, filename):
        self.filename = filename

        self.panel = wx.Panel(parent)
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.box)

        # The tools are not TAB-traversable (bug #335)
        self.toolbar = wx.ToolBar(self.panel, style=wx.TB_VERTICAL)
        self.box.Add(self.toolbar, flag=wx.EXPAND)

        self.logviews = []

        # Hide, otherwise the children windows will be shown even if panel is
        # hidden in the configuration
        self.panel.Show(False)

        self.toolbar.Bind(wx.EVT_TOOL, self._handle_tool)

    def _handle_tool(self, event):
        self.select_log(event.GetId())

    def select_log(self, selection):
        old_view = self.logviews[self.selection]
        view = self.logviews[selection]
        has_focus = old_view.HasFocus()

        old_view.Show(False)
        self.box.Replace(old_view, view)
        view.Show()

        if has_focus:
            view.SetFocus()

        self.selection = selection

        self.toolbar.ToggleTool(selection, True)

        self.panel.Layout()

    def get_panel(self):
        return self.panel

    def add_log(self, view, label, icon, menu_items, menu_update):
        self.logviews.append(view)
        view.Show(False)
        tool_id = len(self.logviews) - 1

        # Labels will appear for example in the dropdown menu that appears when
        # there's not enough room to display all the tools
        self.toolbar.AddRadioLabelTool(tool_id, label, icon, shortHelp=label)
        self.toolbar.Realize()

        cmenu = ContextMenu(view, self.filename, menu_items, menu_update)

        menu_items, popup_cmenu = cmenu.get_items_and_popup()
        return (tool_id, menu_items, popup_cmenu)

    def initialize(self):
        self.selection = 0
        view = self.logviews[self.selection]
        self.box.Add(view, 1, flag=wx.EXPAND)
        view.Show()

        if len(self.logviews) < 2:
            self.toolbar.Show(False)

    def focus_selected(self):
        self.logviews[self.selection].SetFocus()

    def advance_selection(self):
        newsel = self.selection + 1

        if newsel >= len(self.logviews):
            newsel = 0

        self.select_log(newsel)

    def reverse_selection(self):
        newsel = self.selection - 1

        # Don't rely on the support for negative indices in lists because the
        # new index is also the id of the respective toolbar tool
        if newsel < 0:
            newsel = len(self.logviews) - 1

        self.select_log(newsel)


class DatabaseHistoryModel(wx.dataview.PyDataViewIndexListModel):
    def __init__(self, data):
        # Using a model is necessary to disable the native "live" search
        # See bugs #349 and #351
        super(DatabaseHistoryModel, self).__init__()
        self.data = data

        # The wxPython demo uses weak references for the item objects: see if
        # it can be used also in this case (bug #348)
        #self.objmapper.UseWeakRefs(True)

    def GetValueByRow(self, row, col):
        return self.data[row][col]

    def GetColumnCount(self):
        return 4

    def GetCount(self):
        return len(self.data)

    '''def GetColumnType(self, col):
        # It seems not needed to override this method, it's not done in the
        # demos either
        # Besides, returning "string" here would activate the "live" search
        # feature that belongs to the native GTK widget used by DataViewCtrl
        # See also bug #349
        # https://groups.google.com/d/msg/wxpython-users/QvSesrnD38E/31l8f6AzIhAJ
        # https://groups.google.com/d/msg/wxpython-users/4nsv7x1DE-s/ljQHl9RTnuEJ
        return None'''


class DatabaseHistory(object):
    def __init__(self, logspanel, parent, filename, bgcolor):
        self.logspanel = logspanel
        self.filename = filename
        self.config = coreaux_api.get_interface_configuration('wxgui')

        statusflags = 0 if self.config('History').get_bool('debug') else \
                                                wx.dataview.DATAVIEW_COL_HIDDEN

        self.view = wx.dataview.DataViewCtrl(parent,
                        style=wx.dataview.DV_SINGLE |
                        wx.dataview.DV_ROW_LINES | wx.dataview.DV_NO_HEADER)

        self.data = []
        self.dvmodel = DatabaseHistoryModel(self.data)
        self.view.AssociateModel(self.dvmodel)
        # According to DataViewModel's documentation (as of September 2014)
        # its reference count must be decreased explicitly to avoid memory
        # leaks; the wxPython demo, however, doesn't do it, and if done here,
        # the application crashes with a segfault when closing all databases
        # See also bug #104
        #self.dvmodel.DecRef()

        self.view.AppendBitmapColumn('Icon', 0, width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Status', 1, width=wx.COL_WIDTH_AUTOSIZE,
                                                            flags=statusflags)
        self.view.AppendTextColumn('Timestamp', 2, width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Description', 3)

        self._make_icons(bgcolor)

        self.tool_id, menu_items, popup_cmenu = self.logspanel.add_log(
                                self.view, "Items",
                                wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU),
                                self._init_context_menu_items(),
                                self._update_context_menu)
        self._store_context_menu_items(menu_items)

        self.view.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, popup_cmenu)
        self.view.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED,
                                                        self._handle_selection)

        self.refresh()

    def _make_icons(self, bgcolor):
        coldone = self.config('History')['color_done']
        colundone = self.config('History')['color_undone']
        colsaved = self.config('History')['color_saved']

        if coldone == 'none':
            colordone = bgcolor
        else:
            colordone = wx.Colour()
            colordone.SetFromString(coldone)

        if colundone == 'none':
            colorundone = bgcolor
        else:
            colorundone = wx.Colour()
            colorundone.SetFromString(colundone)

        if colsaved == 'none':
            colorsaved = bgcolor
        else:
            colorsaved = wx.Colour()
            colorsaved.SetFromString(colsaved)

        height = self.view.GetFont().GetPixelSize().GetHeight()

        dc = wx.MemoryDC()

        self.icons = {
            0: self._make_bitmap(dc, height, colorundone),
            1: self._make_bitmap(dc, height, colordone),
            2: self._make_bitmap(dc, height, colorundone),
            3: self._make_bitmap(dc, height, colordone),
            4: self._make_bitmap(dc, height, colorundone),
            5: self._make_bitmap(dc, height, colorsaved),
        }

        dc.SelectObject(wx.NullBitmap)

    def _make_bitmap(self, dc, height, color):
        bitmap = wx.EmptyBitmap(6, height)

        dc.SelectObject(bitmap)
        dc.SetBackground(wx.Brush(color))
        dc.Clear()

        return bitmap

    def _init_context_menu_items(self):
        return ((wx.GetApp().menu.database.ID_UNDO, "&Undo",
                            wx.ArtProvider.GetBitmap('@undo', wx.ART_MENU)),
                (wx.GetApp().menu.database.ID_REDO, "&Redo",
                            wx.ArtProvider.GetBitmap('@redo', wx.ART_MENU)))

    def _update_context_menu(self):
        self.undo.Enable(False)
        self.redo.Enable(False)

        if core_api.preview_undo_tree(self.filename):
            self.undo.Enable()

        if core_api.preview_redo_tree(self.filename):
            self.redo.Enable()

    def _store_context_menu_items(self, items):
        self.undo, self.redo = items

    def _handle_selection(self, event):
        self.view.UnselectAll()

    def refresh(self):
        del self.data[:]
        descriptions = core_api.get_history_descriptions(self.filename)

        for row in descriptions:
            tstamp = time_.strftime('%Y-%m-%d %H:%M', time_.localtime(
                                                            row['H_tstamp']))
            self.data.append((self.icons[row['H_status']],
                                    "".join(("[", str(row['H_status']), "]")),
                                    tstamp, row['H_description']))

        self.dvmodel.Reset(len(self.data))

    def select(self):
        self.logspanel.select_log(self.tool_id)


class ContextMenu(wx.Menu):
    def __init__(self, view, filename, items, update):
        wx.Menu.__init__(self)
        self.view = view
        self.filename = filename
        self._update = update
        self.added_items = []

        self.hide = wx.MenuItem(self,
                    wx.GetApp().menu.view.logs_submenu.ID_SHOW, "&Hide logs")
        self.hide.SetBitmap(wx.ArtProvider.GetBitmap('@hide', wx.ART_MENU))

        self.AppendItem(self.hide)
        self.AppendSeparator()

        for id_, label, icon in items:
            item = wx.MenuItem(self, id_, label)
            item.SetBitmap(icon)
            self.AppendItem(item)
            self.added_items.append(item)

    def _popup(self, event):
        self._update()
        self.view.PopupMenu(self)

        # Skipping the event would change the current selection after the
        # click and only select the item under the cursor
        #event.Skip()

    def get_items_and_popup(self):
        return (self.added_items, self._popup)
