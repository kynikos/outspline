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
import wx.lib.agw.foldpanelbar as foldpanelbar
from wx.lib.agw.foldpanelbar import FoldPanelBar, CaptionBarStyle

from outspline.coreaux_api import Event
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api

import msgboxes
import textarea
import tree

open_editor_event = Event()
apply_editor_event = Event()
check_modified_state_event = Event()
close_editor_event = Event()
open_textctrl_event = Event()

config = coreaux_api.get_interface_configuration('wxgui')

tabs = {}


class EditorPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)


class Editor():
    filename = None
    id_ = None
    item = None
    panel = None
    pbox = None
    area = None
    fpbar = None
    modstate = None
    accels = None

    def __init__(self, filename, id_, item):
        self.filename = filename
        self.id_ = id_
        self.item = item
        self.modstate = False

        self.panel = EditorPanel(wx.GetApp().nb_right)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

        self.accels = [(wx.wx.ACCEL_CTRL, wx.WXK_RETURN,
                        wx.GetApp().menu.edit.ID_APPLY),
                       (wx.wx.ACCEL_CTRL, wx.WXK_NUMPAD_ENTER,
                        wx.GetApp().menu.edit.ID_APPLY),
                       (wx.ACCEL_SHIFT | wx.wx.ACCEL_CTRL, wx.WXK_RETURN,
                        wx.GetApp().menu.edit.ID_APPLY_ALL),
                       (wx.ACCEL_SHIFT | wx.wx.ACCEL_CTRL, wx.WXK_NUMPAD_ENTER,
                        wx.GetApp().menu.edit.ID_APPLY_ALL),
                       (wx.wx.ACCEL_CTRL, ord('w'),
                        wx.GetApp().menu.edit.ID_CLOSE),
                       (wx.ACCEL_SHIFT | wx.wx.ACCEL_CTRL, ord('w'),
                        wx.GetApp().menu.edit.ID_CLOSE_ALL)]

        self.panel.SetAcceleratorTable(wx.AcceleratorTable(self.accels))

    def _post_init(self):
        filename = self.filename
        id_ = self.id_

        text = core_api.get_item_text(filename, id_)
        title = self.make_title(text)

        self.area = textarea.TextArea(self.filename, self.id_, self.item, text)
        self.pbox.Add(self.area.area, proportion=1, flag=wx.EXPAND | wx.ALL,
                      border=4)

        open_textctrl_event.signal(filename=filename, id_=id_, item=self.item,
                                   text=text)

        wx.GetApp().nb_right.add_page(self.panel, title, select=True)

    @classmethod
    def open(cls, filename, id_):
        item = cls.make_tabid(filename, id_)

        global tabs
        if item not in tabs:
            tabs[item] = cls(filename, id_, item)
            tabs[item]._post_init()
            open_editor_event.signal(filename=filename, id_=id_, item=item)
        else:
            wx.GetApp().nb_right.SetSelectionToWindow(tabs[item].panel)

    def add_plugin_panel(self, caption):
        if self.fpbar == None:
            separator = wx.StaticLine(self.panel, size=(1, 1),
                                      style=wx.LI_HORIZONTAL)
            self.pbox.Prepend(separator, flag=wx.EXPAND)

            self.fpbar = FoldPanelBar(self.panel,
                                      agwStyle=foldpanelbar.FPB_SINGLE_FOLD |
                                      foldpanelbar.FPB_HORIZONTAL)
            self.pbox.Prepend(self.fpbar, flag=wx.EXPAND)

            self.panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                            self.handle_collapsiblepane)
            self.fpbar.Bind(foldpanelbar.EVT_CAPTIONBAR,
                            self.handle_captionbar)

        cbstyle = CaptionBarStyle()

        return self.fpbar.AddFoldPanel(caption=caption, cbstyle=cbstyle)

    def add_plugin_window(self, fpanel, window):
        self.fpbar.AddFoldPanelWindow(fpanel, window)
        self.panel.Layout()

    def handle_collapsiblepane(self, event):
        self.panel.Layout()

    def handle_captionbar(self, event):
        event.Skip()
        wx.CallAfter(self.resize_fpb)

    def resize_fpb(self):
        sizeNeeded = self.fpbar.GetPanelsLength(0, 0)[2]
        self.fpbar.SetMinSize((0, sizeNeeded))
        self.panel.Layout()

    def collapse_panel(self, fpanel):
        self.fpbar.Collapse(fpanel)

    def expand_panel(self, fpanel):
        self.fpbar.Expand(fpanel)

    def apply(self):
        group = core_api.get_next_history_group(self.filename)
        description = 'Apply editor'

        # Note that apply_editor_event is also bound directly by the textarea
        apply_editor_event.signal(filename=self.filename, id_=self.id_,
                                    group=group, description=description)

        tree.dbs[self.filename].history.refresh()

    def set_modified(self):
        self.modstate = True

    def is_modified(self):
        self.modstate = False

        # Note that this event is also bound directly by the textarea
        check_modified_state_event.signal(filename=self.filename, id_=self.id_)

        return self.modstate

    def close(self, ask='apply'):
        nb = wx.GetApp().nb_right
        tabid = nb.GetPageIndex(self.panel)
        nb.SetSelection(tabid)
        item = self.item

        if ask != 'quiet' and self.is_modified():
            if ask == 'discard':
                if msgboxes.close_tab_without_saving().ShowModal() != wx.ID_OK:
                # Note that this if can't be merged with the one above, i.e.:
                #   if ask == 'discard' and msgboxes.close_tab_without_saving...
                # in fact if msgboxes...ShowModal() returned something different
                # from wx.ID_OK, the else clause below would be entered
                    return False
            else:
                # This is the condition that actually matches ask == 'apply',
                # but it must also be the fallback for any other value (hence
                # 'apply' is just a dummy value)
                save = msgboxes.close_tab_ask().ShowModal()
                if save == wx.ID_YES:
                    self.apply()
                elif save == wx.ID_CANCEL:
                    return False

        # Note that this event is also bound directly by the textarea
        close_editor_event.signal(filename=self.filename, id_=self.id_)

        nb.close_page(nb.GetPageIndex(self.panel))

        global tabs
        del tabs[item]

        return True

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    @staticmethod
    def make_title(text):
        max_ = config.get_int('max_editor_tab_length')
        title = text.partition('\n')[0]
        if len(title) > max_:
            title = title[:max_ - 3] + '...'
        return title

    @staticmethod
    def make_tabid(filename, id_):
        return '_'.join((filename, str(id_)))

    def add_accelerators(self, accels):
        self.accels.extend(accels)
        self.panel.SetAcceleratorTable(wx.AcceleratorTable(self.accels))
