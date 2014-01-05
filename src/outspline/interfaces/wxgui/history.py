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


class HistoryWindow(wx.ScrolledWindow):
    filename = None
    events = None
    box = None
    cmenu = None

    def __init__(self, parent, filename):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetScrollRate(20, 20)

        self.filename = filename
        self.events = {}

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.box)

        self.cmenu = ContextMenu(filename)

        self.Bind(wx.EVT_CONTEXT_MENU, self.popup_context_menu)

        self.refresh()

    def refresh(self):
        self.box.Clear(True)

        descriptions = core_api.get_history_descriptions(self.filename)
        for row in descriptions:
            st = wx.StaticText(self, label=''.join(('[', str(row['H_status']),
                                                    '] ',
                                                    row['H_description'])))
            self.events[row['H_group']] = {'status': row['H_status'],
                                            'st': st}
            self.box.Add(st)

        self.Layout()
        self.box.FitInside(self)

    def popup_context_menu(self, event):
        self.cmenu.update_items()
        self.PopupMenu(self.cmenu)


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
