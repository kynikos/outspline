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
import wx.lib.agw.foldpanelbar as foldpanelbar
from wx.lib.agw.foldpanelbar import FoldPanelBar

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


class Editors(object):
    def __init__(self, nb):
        self.icon_index = nb.add_image(wx.ArtProvider.GetBitmap(
                                'text-x-generic', wx.ART_TOOLBAR, (16, 16)))


class EditorPanel(wx.Panel):
    ctabmenu = None

    def __init__(self, parent, item):
        wx.Panel.__init__(self, parent)
        self.ctabmenu = TabContextMenu(item)

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu


class CaptionBarStyle(foldpanelbar.CaptionBarStyle):
    def __init__(self, panel):
        foldpanelbar.CaptionBarStyle.__init__(self)

        bgcolour = panel.GetBackgroundColour()

        avg = (bgcolour.Red() + bgcolour.Green() + bgcolour.Blue()) // 3

        if avg > 127:
            DIFF1 = 16
            DIFF2 = DIFF1 + 16
            colourtop = wx.Colour(max((bgcolour.Red() - DIFF1, 0)),
                                          max((bgcolour.Green() - DIFF1, 0)),
                                          max((bgcolour.Blue() - DIFF1, 0)))
            colourbottom = wx.Colour(max((bgcolour.Red() - DIFF2, 0)),
                                          max((bgcolour.Green() - DIFF2, 0)),
                                          max((bgcolour.Blue() - DIFF2, 0)))
        else:
            DIFF1 = 8
            DIFF2 = DIFF1 + 16
            colourtop = wx.Colour(min((bgcolour.Red() + DIFF2, 255)),
                                        min((bgcolour.Green() + DIFF2, 255)),
                                        min((bgcolour.Blue() + DIFF2, 255)))
            colourbottom = wx.Colour(min((bgcolour.Red() + DIFF1, 255)),
                                        min((bgcolour.Green() + DIFF1, 255)),
                                        min((bgcolour.Blue() + DIFF1, 255)))

        self.SetCaptionStyle(foldpanelbar.CAPTIONBAR_GRADIENT_V)
        self.SetFirstColour(colourtop)
        self.SetSecondColour(colourbottom)
        self.SetCaptionColour(panel.GetForegroundColour())


class Editor():
    filename = None
    id_ = None
    item = None
    panel = None
    pbox = None
    area = None
    fpbar = None
    cbstyle = None
    modstate = None

    def __init__(self, filename, id_, item):
        self.filename = filename
        self.id_ = id_
        self.item = item
        self.modstate = False

        self.panel = EditorPanel(wx.GetApp().nb_right, item)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

    def _post_init(self):
        filename = self.filename
        id_ = self.id_

        text = core_api.get_item_text(filename, id_)
        title = self.make_title(text)

        self.area = textarea.TextArea(self.filename, self.id_, self.item, text)
        self.pbox.Add(self.area.area, proportion=1, flag=wx.EXPAND)

        open_textctrl_event.signal(filename=filename, id_=id_, item=self.item,
                                   text=text)

        nb = wx.GetApp().nb_right
        nb.add_page(self.panel, title, select=True,
                                                imageId=nb.editors.icon_index)

    @classmethod
    def open(cls, filename, id_):
        item = cls.make_tabid(filename, id_)

        global tabs
        if item not in tabs:
            tabs[item] = cls(filename, id_, item)
            tabs[item]._post_init()
            open_editor_event.signal(filename=filename, id_=id_, item=item)
        else:
            tabid = wx.GetApp().nb_right.GetPageIndex(tabs[item].panel)
            wx.GetApp().nb_right.SetSelection(tabid)

    def add_plugin_panel(self, caption):
        if self.fpbar == None:
            self.fpbar = FoldPanelBar(self.panel,
                                            agwStyle=foldpanelbar.FPB_VERTICAL)
            self.pbox.Prepend(self.fpbar, flag=wx.EXPAND)

            self.cbstyle = CaptionBarStyle(self.panel)

            self.panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                            self.handle_collapsiblepane)
            self.fpbar.Bind(foldpanelbar.EVT_CAPTIONBAR,
                            self.handle_captionbar)

        fpanel = self.fpbar.AddFoldPanel(caption=caption, cbstyle=self.cbstyle)

        captionbar = self.get_captionbar(fpanel)
        captionbar.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        captionbar.Bind(wx.EVT_MOUSE_EVENTS,
                                        self.void_default_captionbar_behaviour)
        captionbar.Bind(wx.EVT_LEFT_DOWN, self.handle_mouse_click)

        return fpanel

    def get_captionbar(self, fpanel):
        try:
            return fpanel._captionBar
        except AttributeError:
            # Since I'm using a hidden attribute (_captionBar) be safe with a
            # fallback solution
            for child in fpanel.GetChildren():
                if child.__class__ is foldpanelbar.CaptionBar:
                    return child

    def void_default_captionbar_behaviour(self, event):
        # This lets override the default handling of EVT_MOUSE_EVENTS and
        # define a custom behaviour of CaptionBar
        # The default handling of EVT_MOUSE_EVENTS also resets the mouse
        # cursor, so this is also useful for setting a custom cursor
        # See http://xoomer.virgilio.it/infinity77/AGW_Docs/_modules/foldpanelbar.html#CaptionBar.OnMouseEvent
        # For these reasons, do not Skip this event!
        pass

    def handle_mouse_click(self, event):
        # This overrides the default behaviour of CaptionBar
        # See also self.void_default_captionbar_behaviour
        captionbar = event.GetEventObject()
        event = foldpanelbar.CaptionBarEvent(
                                            foldpanelbar.EVT_CAPTIONBAR.typeId)
        event.SetId(captionbar.GetId())
        event.SetEventObject(captionbar)
        event.SetBar(captionbar)
        captionbar.GetEventHandler().ProcessEvent(event)

    def handle_collapsiblepane(self, event):
        self.panel.Layout()

    def handle_captionbar(self, event):
        event.Skip()
        wx.CallAfter(self.resize_fpb)

    def add_plugin_window(self, fpanel, window):
        self.fpbar.AddFoldPanelWindow(fpanel, window)
        self.panel.Layout()

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

        tree.dbs[self.filename].dbhistory.refresh()

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

        nb.close_page(tabid)

        global tabs
        del tabs[item]

        return True

    def find_in_tree(self):
        treedb = tree.dbs[self.filename]
        treedb.select_item(treedb.find_item(self.id_))
        nb = wx.GetApp().nb_left
        nb.select_page(nb.GetPageIndex(treedb))

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


class TabContextMenu(wx.Menu):
    item = None
    find = None
    apply_ = None
    close = None

    def __init__(self, item):
        wx.Menu.__init__(self)
        self.item = item

        self.find = wx.MenuItem(self, wx.GetApp().menu.edit.ID_FIND,
                                                        "&Find in database")
        self.apply_ = wx.MenuItem(self, wx.GetApp().menu.edit.ID_APPLY,
                                                                    "&Apply")
        self.close = wx.MenuItem(self, wx.GetApp().menu.edit.ID_CLOSE,
                                                                    "Cl&ose")

        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
        self.apply_.SetBitmap(wx.ArtProvider.GetBitmap('@apply', wx.ART_MENU))
        self.close.SetBitmap(wx.ArtProvider.GetBitmap('@close', wx.ART_MENU))

        self.AppendItem(self.find)
        self.AppendSeparator()
        self.AppendItem(self.apply_)
        self.AppendItem(self.close)

    def update(self):
        if tabs[self.item].is_modified():
            self.apply_.Enable()
        else:
            self.apply_.Enable(False)
