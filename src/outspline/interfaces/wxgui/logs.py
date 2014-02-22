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

        self.toolbar = wx.ToolBar(self.panel, style=wx.TB_VERTICAL |
                                                wx.TB_FLAT | wx.BORDER_NONE)
        self.box.Add(self.toolbar, flag=wx.EXPAND)

        self.scwindow = wx.ScrolledWindow(self.panel, style=wx.BORDER_THEME)
        self.scwindow.SetScrollRate(20, 20)
        self.box.Add(self.scwindow, 1, flag=wx.EXPAND)

        self.box2 = wx.BoxSizer(wx.HORIZONTAL)
        self.scwindow.SetSizer(self.box2)

        self.logwindows = []

        # Hide, otherwise the children windows will be shown even if panel is
        # hidden in the configuration
        self.panel.Show(False)

        self.toolbar.Bind(wx.EVT_TOOL, self._handle_tool)

    def _handle_tool(self, event):
        old_window = self.logwindows[self.selection]
        window = self.logwindows[event.GetId()]

        old_window.Show(False)
        self.box2.Replace(old_window, window)
        window.Show()

        self.scwindow.SetBackgroundColour(window.GetBackgroundColour())

        self.selection = event.GetId()

        # Update scroll bars
        self.scwindow.SetVirtualSize(window.GetVirtualSize())

    def get_panel(self):
        return self.panel

    def get_window(self):
        return self.scwindow

    def add_log(self, window, label, icon, menu_items, menu_update):
        self.logwindows.append(window)
        window.Show(False)

        # Labels will appear for example in the dropdown menu that appears when
        # there's not enough room to display all the tools
        self.toolbar.AddLabelTool(len(self.logwindows) - 1, label, icon,
                                                            shortHelp=label)
        self.toolbar.Realize()

        cmenu = ContextMenu(window, self.filename, menu_items, menu_update)

        return cmenu.get_added_items()

    def initialize(self):
        self.selection = 0
        window = self.logwindows[self.selection]
        self.box2.Add(window, 1, flag=wx.EXPAND)
        window.Show()

        self.scwindow.SetBackgroundColour(window.GetBackgroundColour())

        if len(self.logwindows) < 2:
            self.toolbar.Show(False)


class DatabaseHistory(object):
    def __init__(self, parent, filename, bgcolor):
        self.filename = filename
        self.config = coreaux_api.get_interface_configuration('wxgui')

        self.panel = wx.Panel(parent)
        self.panel.SetBackgroundColour(bgcolor)
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.box)

        self._set_colors(bgcolor)

        if self.config.get_bool('debug_history'):
            self._format_action = lambda row: "".join(("[",
                            str(row['H_status']), "] ", row['H_description']))
        else:
            self._format_action = lambda row: row['H_description']

        self.panel.Bind(wx.EVT_PAINT, self._handle_paint)

        self.refresh()

    def _set_colors(self, bgcolor):
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

        self.colors = {
            0: colorundone,
            1: colordone,
            2: colorundone,
            3: colordone,
            4: colorundone,
            5: colorsaved,
        }

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

    def _handle_paint(self, event):
        dc = wx.PaintDC(self.panel)
        gc = wx.GraphicsContext.Create(dc)
        ypos = self.statusheights['total']

        for status in (5, 4, 3, 2, 1, 0):
            height = self.statusheights[status]
            ypos -= height
            gc.SetBrush(gc.CreateBrush(wx.Brush(self.colors[status])))
            gc.DrawRectangle(0, ypos, 6, height)

    @classmethod
    def create(cls, logspanel, filename, bgcolor):
        obj = cls(logspanel.get_window(), filename, bgcolor)
        menu_items = logspanel.add_log(obj.panel, "Items",
                                wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU),
                                obj._init_context_menu_items(),
                                obj._update_context_menu)
        obj._store_context_menu_items(menu_items)

        return obj

    def refresh(self):
        # Don't use self.panel.DestroyChildren() because it wouldn't also
        # delete the spacer; moreover, while refreshing, all the StaticText
        # items would appear all overlapping until the Layout, which doesn't
        # happen with self.box.Clear(True)
        self.box.Clear(True)

        descriptions = core_api.get_history_descriptions(self.filename)

        self.statusheights = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for row in descriptions:
            text = wx.StaticText(self.panel, label=self._format_action(row))
            self.box.Add(text, flag=wx.LEFT, border=10)
            # Some of the platforms supported by wxPython (most notably GTK),
            # do not consider StaticText as a separate widget; instead, the
            # label is just drawn on its parent window. For this reason it's
            # impossible to drawn on StaticText and e.g. GenStaticText should
            # be used.
            self.statusheights[row['H_status']] += text.GetRect().GetHeight()

        self.statusheights['total'] = sum(self.statusheights.values())

        self.panel.Layout()


class ContextMenu(wx.Menu):
    def __init__(self, window, filename, items, update):
        wx.Menu.__init__(self)
        self.window = window
        self.filename = filename
        self._update = update
        self.added_items = []

        self.hide = wx.MenuItem(self, wx.GetApp().menu.view.ID_LOGS,
                                                                "&Hide logs")
        self.hide.SetBitmap(wx.ArtProvider.GetBitmap('@logs', wx.ART_MENU))

        self.AppendItem(self.hide)
        self.AppendSeparator()

        for id_, label, icon in items:
            item = wx.MenuItem(self, id_, label)
            item.SetBitmap(icon)
            self.AppendItem(item)
            self.added_items.append(item)

        self.window.Bind(wx.EVT_CONTEXT_MENU, self._popup)

    def _popup(self, event):
        self._update()
        self.window.PopupMenu(self)

    def get_added_items(self):
        return self.added_items
