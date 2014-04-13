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

        # TB_FLAT and BORDER_NONE seem to have no effect (bug #273)
        self.toolbar = wx.ToolBar(self.panel, style=wx.TB_VERTICAL |
                                                wx.TB_FLAT | wx.BORDER_NONE)
        self.box.Add(self.toolbar, flag=wx.EXPAND)

        self.logviews = []

        # Hide, otherwise the children windows will be shown even if panel is
        # hidden in the configuration
        self.panel.Show(False)

        self.toolbar.Bind(wx.EVT_TOOL, self._handle_tool)

    def _handle_tool(self, event):
        old_view = self.logviews[self.selection]
        view = self.logviews[event.GetId()]

        old_view.Show(False)
        self.box.Replace(old_view, view)
        view.Show()

        self.selection = event.GetId()

        self.panel.Layout()

    def get_panel(self):
        return self.panel

    def add_log(self, view, label, icon, menu_items, menu_update):
        self.logviews.append(view)
        view.Show(False)

        # Labels will appear for example in the dropdown menu that appears when
        # there's not enough room to display all the tools
        self.toolbar.AddLabelTool(len(self.logviews) - 1, label, icon,
                                                            shortHelp=label)
        self.toolbar.Realize()

        cmenu = ContextMenu(view, self.filename, menu_items, menu_update)

        return cmenu.get_items_and_popup()

    def initialize(self):
        self.selection = 0
        view = self.logviews[self.selection]
        self.box.Add(view, 1, flag=wx.EXPAND)
        view.Show()

        if len(self.logviews) < 2:
            self.toolbar.Show(False)


class DatabaseHistory(object):
    def __init__(self, logspanel, parent, filename, bgcolor):
        self.filename = filename
        self.config = coreaux_api.get_interface_configuration('wxgui')

        statusflags = 0 if self.config.get_bool('debug_history') else \
                                                wx.dataview.DATAVIEW_COL_HIDDEN

        self.view = wx.dataview.DataViewListCtrl(parent,
                        style=wx.dataview.DV_SINGLE |
                        wx.dataview.DV_ROW_LINES | wx.dataview.DV_NO_HEADER)
        self.view.AppendBitmapColumn('Icon', 0, width=wx.COL_WIDTH_AUTOSIZE)
        self.view.AppendTextColumn('Status', 1, width=wx.COL_WIDTH_AUTOSIZE,
                                                            flags=statusflags)
        self.view.AppendTextColumn('Description', 2)

        self._make_icons(bgcolor)

        menu_items, popup_cmenu = logspanel.add_log(self.view, "Items",
                                wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU),
                                self._init_context_menu_items(),
                                self._update_context_menu)
        self._store_context_menu_items(menu_items)

        self.view.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, popup_cmenu)
        self.view.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED,
                                                        self._handle_selection)
        self.view.Bind(wx.dataview.EVT_DATAVIEW_ITEM_START_EDITING,
                                                    self._handle_item_editing)

        self.refresh()

    def _make_icons(self, bgcolor):
        coldone = self.config['history_color_done']
        colundone = self.config['history_color_undone']
        colsaved = self.config['history_color_saved']

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

    def _handle_item_editing(self, event):
        event.Veto()

    def refresh(self):
        self.view.DeleteAllItems()

        descriptions = core_api.get_history_descriptions(self.filename)

        for row in descriptions:
            item = self.view.AppendItem((self.icons[row['H_status']],
                                    "".join(("[", str(row['H_status']), "]")),
                                    row['H_description']))


class ContextMenu(wx.Menu):
    def __init__(self, view, filename, items, update):
        wx.Menu.__init__(self)
        self.view = view
        self.filename = filename
        self._update = update
        self.added_items = []

        self.hide = wx.MenuItem(self, wx.GetApp().menu.logs.ID_LOGS,
                                                                "&Hide logs")
        self.hide.SetBitmap(wx.ArtProvider.GetBitmap('@logs', wx.ART_MENU))

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

        # Skipping the event lets right clicks behave correctly
        event.Skip()

    def get_items_and_popup(self):
        return (self.added_items, self._popup)
