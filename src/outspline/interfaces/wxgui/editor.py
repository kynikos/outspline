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

config = coreaux_api.get_interface_configuration('wxgui')

tabs = {}


class Editors(object):
    def __init__(self, nb):
        self.icon_index = nb.add_image(wx.ArtProvider.GetBitmap(
                                    '@editortab', wx.ART_TOOLBAR, (16, 16)))


class EditorPanel(wx.Panel):
    def __init__(self, parent, editor, item):
        wx.Panel.__init__(self, parent)
        self.editor = editor
        self.ctabmenu = TabContextMenu(item)

    def store_accelerators_table(self, acctable):
        self.acctable = acctable

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu

    def get_accelerators_table(self):
        return self.acctable

    def close_tab(self):
        self.editor.close()


class CaptionBarStyle(foldpanelbar.CaptionBarStyle):
    @staticmethod
    def compute_colors(panel):
        fgcolour = panel.GetForegroundColour()
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

        focuscolour = config["plugin_focus_color"]

        if focuscolour == "system":
            colourfocused = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        else:
            colourfocused = wx.Colour()
            colourfocused.SetFromString(config["plugin_focus_color"])

        return (colourtop, colourbottom, colourfocused, fgcolour)

    def __init__(self, style, colourtop, colourbottom, fgcolour):
        super(CaptionBarStyle, self).__init__()
        self.SetCaptionStyle(style)
        self.SetFirstColour(colourtop)
        self.SetSecondColour(colourbottom)
        self.SetCaptionColour(fgcolour)

    @classmethod
    def create_normal(cls, colourtop, colourbottom, fgcolour):
        return cls(foldpanelbar.CAPTIONBAR_GRADIENT_V, colourtop, colourbottom,
                                                                    fgcolour)

    @classmethod
    def create_focused(cls, colour, fgcolour):
        return cls(foldpanelbar.CAPTIONBAR_SINGLE, colour, colour, fgcolour)


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
        self.captionbars = []

        self.captionbar_keys = {
            wx.WXK_TAB: self._handle_tab_on_captionbar,
            wx.WXK_RETURN: self._handle_captionbar_key_toggle,
            wx.WXK_SPACE: self._handle_captionbar_key_toggle,
        }

        self.panel = EditorPanel(wx.GetApp().nb_right, self, item)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

    def _post_init(self):
        text = core_api.get_item_text(self.filename, self.id_)
        title = self.make_title(text)

        self.area = textarea.TextArea(self.filename, self.id_, self.item, text)
        self.pbox.Add(self.area.area, proportion=1, flag=wx.EXPAND)

        self.accelerators = {}

        open_editor_event.signal(filename=self.filename, id_=self.id_,
                                                    item=self.item, text=text)

        aconfig = config("ExtendedShortcuts")("RightNotebook")("Editor")
        self.accelerators.update({
            aconfig["apply"]: lambda event: self.apply(),
            aconfig["find"]: lambda event: self.find_in_tree(),
            aconfig["focus_text"]: lambda event: self.focus_text(),
        })
        self.accelerators.update(
                            wx.GetApp().nb_right.get_generic_accelerators())
        acctable = wx.GetApp().root.accmanager.generate_table(
                                    wx.GetApp().nb_right, self.accelerators)
        self.panel.store_accelerators_table(acctable)

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
        else:
            tabid = wx.GetApp().nb_right.GetPageIndex(tabs[item].panel)
            wx.GetApp().nb_right.select_page(tabid)

    def add_plugin_panel(self, caption):
        if self.fpbar == None:
            self.fpbar = FoldPanelBar(self.panel,
                                            agwStyle=foldpanelbar.FPB_VERTICAL)
            self.pbox.Prepend(self.fpbar, flag=wx.EXPAND)
            self.fpbar.MoveBeforeInTabOrder(self.area.area)

            colourtop, colourbottom, colourfocused, fgcolour = \
                                    CaptionBarStyle.compute_colors(self.panel)
            self.cbstyles = (
                CaptionBarStyle.create_normal(colourtop, colourbottom,
                                                                    fgcolour),
                CaptionBarStyle.create_focused(colourfocused, fgcolour),
            )

            self.panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                            self.handle_collapsiblepane)
            self.fpbar.Bind(foldpanelbar.EVT_CAPTIONBAR,
                            self.handle_captionbar)

        fpanel = self.fpbar.AddFoldPanel(caption=caption,
                                                    cbstyle=self.cbstyles[0])

        captionbar = self.get_captionbar(fpanel)
        self.captionbars.append(captionbar)
        captionbar.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        captionbar.Bind(wx.EVT_MOUSE_EVENTS,
                                        self.void_default_captionbar_behaviour)
        captionbar.Bind(wx.EVT_LEFT_DOWN, self.handle_mouse_click)
        captionbar.Bind(wx.EVT_KEY_DOWN, self._handle_key_down)
        captionbar.Bind(wx.EVT_SET_FOCUS, self._handle_set_focus)
        captionbar.Bind(wx.EVT_KILL_FOCUS, self._handle_kill_focus)

        return fpanel

    def _handle_key_down(self, event):
        try:
            self.captionbar_keys[event.GetKeyCode()](event)
        except KeyError:
            event.Skip()
        # Don't skip the event if the key action is done
        #event.Skip()

    def _handle_tab_on_captionbar(self, event):
        # This method must get the same arguments as
        #  _handle_captionbar_key_toggle
        captionbar = event.GetEventObject()
        index = self.captionbars.index(captionbar)

        if event.ShiftDown():
            if index > 0 and self.captionbars[index - 1].IsCollapsed():
                self.captionbars[index - 1].SetFocus()
            else:
                captionbar.Navigate(flags=wx.NavigationKeyEvent.IsBackward)
        else:
            if captionbar.IsCollapsed():
                if index < len(self.captionbars) - 1:
                    self.captionbars[index + 1].SetFocus()
                else:
                    self.area.area.SetFocus()
            else:
                captionbar.Navigate(flags=wx.NavigationKeyEvent.IsForward)

    def _handle_captionbar_key_toggle(self, event):
        # This method must get the same arguments as _handle_tab_on_captionbar
        captionbar = event.GetEventObject()

        if captionbar.IsCollapsed():
            self.expand_panel(captionbar.GetParent())
        else:
            self.collapse_panel(captionbar.GetParent())

    def _handle_set_focus(self, event):
        event.GetEventObject().SetCaptionStyle(self.cbstyles[1])
        event.Skip()

    def _handle_kill_focus(self, event):
        event.GetEventObject().SetCaptionStyle(self.cbstyles[0])
        event.Skip()

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

    def add_plugin_window(self, fpanel, window, accelerators):
        self.fpbar.AddFoldPanelWindow(fpanel, window)
        self.panel.Layout()

        self.accelerators.update(accelerators)

    def resize_fpb(self):
        sizeNeeded = self.fpbar.GetPanelsLength(0, 0)[2]
        self.fpbar.SetMinSize((0, sizeNeeded))
        self.panel.Layout()

    def collapse_panel(self, fpanel):
        self.fpbar.Collapse(fpanel)
        self.resize_fpb()

    def expand_panel(self, fpanel):
        self.fpbar.Expand(fpanel)
        self.resize_fpb()

    def focus_text(self):
        self.area.area.SetFocus()

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
        nb.select_page(tabid)
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
        treedb.select_item(self.id_)
        nb = wx.GetApp().nb_left
        nb.select_page(nb.GetPageIndex(treedb))

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    def get_plugin_captionbars(self):
        return self.captionbars

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
        self.close = wx.MenuItem(self,
                wx.GetApp().menu.view.rightnb_submenu.ID_CLOSE, "Cl&ose")

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
