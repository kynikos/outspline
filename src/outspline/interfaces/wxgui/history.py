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

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api

config = coreaux_api.get_interface_configuration('wxgui')

# Use a copy of the original constant, so that every time a database is opened
# it reads the current value, and not the one stored in the configuration
# Do not put this into the class, since it must be an instance-independent
# value
_show_history = config.get_bool('show_history')


class History():
    filename = None
    scwindow = None
    box = None
    cmenu = None

    def __init__(self, parent, filename):
        self.filename = filename

        self.scwindow = wx.ScrolledWindow(parent)
        self.scwindow.SetScrollRate(20, 20)
        self.scwindow.SetBackgroundColour(parent.treec.GetBackgroundColour())

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.scwindow.SetSizer(self.box)

        self.cmenu = ContextMenu(filename)

        self.scwindow.Bind(wx.EVT_CONTEXT_MENU, self.popup_context_menu)

        self.refresh()

    def refresh(self):
        # Don't use self.scwindow.DestroyChildren() because it wouldn't also
        # delete the spacer; moreover, while refreshing, all the StaticText
        # items would appear all overlapping until the Layout, which doesn't
        # happen with self.box.Clear(True)
        self.box.Clear(True)

        self.box.AddSpacer(4)

        descriptions = core_api.get_history_descriptions(self.filename)

        for row in descriptions:
            line = "".join(("[", str(row['H_status']), "] ",
                                                        row['H_description']))
            text = wx.StaticText(self.scwindow, label=line)
            self.box.Add(text, flag=wx.EXPAND | wx.LEFT, border=4)

        self.scwindow.Layout()

    def popup_context_menu(self, event):
        self.cmenu.update_items()
        self.scwindow.PopupMenu(self.cmenu)


class ContextMenu(wx.Menu):
    filename = None
    hide = None
    undo = None
    redo = None

    def __init__(self, filename):
        wx.Menu.__init__(self)
        self.filename = filename

        self.hide = wx.MenuItem(self, wx.GetApp().menu.view.ID_HISTORY,
                                                            "&Hide history")
        self.undo = wx.MenuItem(self, wx.GetApp().menu.database.ID_UNDO,
                                                                    "&Undo")
        self.redo = wx.MenuItem(self, wx.GetApp().menu.database.ID_REDO,
                                                                    "&Redo")

        self.hide.SetBitmap(wx.ArtProvider.GetBitmap('@history', wx.ART_MENU))
        self.undo.SetBitmap(wx.ArtProvider.GetBitmap('@undo', wx.ART_MENU))
        self.redo.SetBitmap(wx.ArtProvider.GetBitmap('@redo', wx.ART_MENU))

        self.AppendItem(self.hide)
        self.AppendSeparator()
        self.AppendItem(self.undo)
        self.AppendItem(self.redo)

    def reset_items(self):
        self.undo.Enable(False)
        self.redo.Enable(False)

    def update_items(self):
        self.reset_items()

        if core_api.preview_undo_tree(self.filename):
            self.undo.Enable()

        if core_api.preview_redo_tree(self.filename):
            self.redo.Enable()


def is_shown():
    return _show_history


def set_shown(flag=True):
    global _show_history
    _show_history = flag
