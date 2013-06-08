# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import wx
from threading import Timer

import organism.coreaux_api as coreaux_api
import organism.core_api as core_api

import editor
import tree

config = coreaux_api.get_interface_configuration('wxgui')


class TextCtrl(wx.TextCtrl):
    urlstart = None
    urlend = None

    def __init__(self, parent, text):
        wx.TextCtrl.__init__(self, parent, value=text, style=wx.BORDER_NONE |
                             wx.TE_PROCESS_TAB | wx.TE_MULTILINE |
                             wx.TE_AUTO_URL | wx.TE_NOHIDESEL | wx.TE_DONTWRAP)

        self.Bind(wx.EVT_TEXT_URL, self.launch_browser)

    def launch_browser(self, event):
        self.urlstart = event.GetURLStart()
        self.urlend = event.GetURLEnd()
        if event.GetMouseEvent().LeftUp():
            wx.LaunchDefaultBrowser(self.GetRange(self.urlstart, self.urlend))
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        self.Bind(wx.EVT_MOTION, self.reset_cursor)
        self.Bind(wx.EVT_TEXT_URL, None)

    def reset_cursor(self, event):
        hitpos = self.HitTestPos(event.GetPosition())[1]
        if self.urlstart is not None and self.urlend is not None and \
                              (hitpos < self.urlstart or hitpos > self.urlend):
            self.urlstart = None
            self.urlend = None
            self.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))
            self.Bind(wx.EVT_TEXT_URL, self.launch_browser)
            self.Bind(wx.EVT_MOTION, None)
        # Skip the event, otherwise EVT_TEXT_URL won't work
        event.Skip()


class TextArea():
    filename = None
    id_ = None
    item = None
    original = None
    mtimer = None
    tmrunning = None
    area = None

    def __init__(self, filename, id_, item, text):
        self.filename = filename
        self.id_ = id_
        self.item = item
        self.original = text
        self.tmrunning = False
        self.area = TextCtrl(editor.tabs[item].panel, text)

        self.area.Bind(wx.EVT_TEXT, self._on_text)
        editor.apply_editor_event.bind(self.handle_apply)
        editor.check_modified_state_event.bind(
                                             self.handle_check_editor_modified)
        editor.close_editor_event.bind(self.handle_close)

    def _on_text(self, event):
        if not (self.tmrunning):
            # Always set modified when (re)starting the timer, in fact it's not
            # possible that the textarea can be unmodified, except for the
            # only case where the original state is actually restored, but in
            # that case the modified state will be restored to False anyway if
            # and when the timer executes its action
            self.area.SetModified(True)
        else:
            self.mtimer.cancel()

        self.tmrunning = True
        self.mtimer = Timer(config.get_int('min_text_upd_time'),
                            self.reset_timer)
        self.mtimer.start()

        event.Skip()

    def reset_timer(self):
        self.tmrunning = False
        self.set_modified()

    def set_modified(self):
        if self.area.GetValue() == self.original:
            self.area.SetModified(False)
        else:
            self.area.SetModified(True)

    def reset_modified(self):
        self.original = self.area.GetValue()
        self.area.SetModified(False)

    def is_modified(self):
        self.set_modified()
        return self.area.IsModified()

    def handle_apply(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                        and self.is_modified():
            core_api.update_item_text(self.filename, self.id_,
                                      self.area.GetValue(), kwargs['group'],
                                      kwargs['description'])
            self.refresh_mod_state()

    def refresh_mod_state(self):
        treedb = tree.dbs[self.filename]
        title = treedb.make_item_title(self.area.GetLineText(0))
        treedb.set_item_title(treedb.find_item(self.id_), title)
        tabtitle = editor.Editor.make_title(title)
        wx.GetApp().nb_right.set_editor_title(self.item, tabtitle)

        self.reset_modified()

    def handle_check_editor_modified(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                        and self.is_modified():
            editor.tabs[self.item].set_modified()

    def handle_close(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_:
            if self.mtimer:
                self.mtimer.cancel()
            # It's necessary to explicitly unbind the handlers, otherwise this
            # object will never be garbage-collected due to circular
            # references, and the automatic unbinding won't work
            editor.apply_editor_event.bind(self.handle_apply, False)
            editor.check_modified_state_event.bind(
                                      self.handle_check_editor_modified, False)
            editor.close_editor_event.bind(self.handle_close, False)

    def cut(self):
        self.area.Cut()

    def copy(self):
        self.area.Copy()

    def paste(self):
        self.area.Paste()

    def select_all(self):
        self.area.SetSelection(-1, -1)

    def can_cut(self):
        return self.area.CanCut()

    def can_copy(self):
        return self.area.CanCopy()

    def can_paste(self):
        return self.area.CanPaste()
