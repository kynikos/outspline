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
from threading import Timer

from outspline.static.wxclasses.texturl import TextUrlCtrl
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api

import editor
import tree


class TextArea(object):
    def __init__(self, filename, id_, item, text):
        self.filename = filename
        self.id_ = id_
        self.item = item
        self.original = text
        self.mtimer = None
        self.tmrunning = False
        config = coreaux_api.get_interface_configuration('wxgui')
        self.DELAY = config.get_int('text_min_upd_time')

        # Do not set the text now, otherwise for example URLs won't be
        # highlighted in blue
        # wx.TE_PROCESS_TAB seems to have no effect...
        self.area = TextUrlCtrl(editor.tabs[item].panel, value='',
                    style=wx.TE_MULTILINE | wx.TE_DONTWRAP | wx.TE_NOHIDESEL)

        font = self.area.GetFont()
        font = wx.Font(font.GetPointSize(), wx.FONTFAMILY_TELETYPE,
                       font.GetStyle(), font.GetWeight(), font.GetUnderlined())
        self.area.SetFont(font)

        # Set the text after setting the font, so for example URLs will be
        # correctly highlighted in blue
        self.area.SetValue(text)

        self.area.Bind(wx.EVT_KEY_DOWN, self._handle_esc_down)

        # wx.TE_PROCESS_TAB seems to have no effect...
        if not config.get_bool('text_process_tab'):
            # Note that this natively still lets Ctrl+(Shift+)Tab navigate as
            # expected
            self.area.Bind(wx.EVT_KEY_DOWN, self._handle_tab_down)

        self.area.Bind(wx.EVT_TEXT, self._handle_text)
        editor.apply_editor_event.bind(self._handle_apply)
        editor.check_modified_state_event.bind(
                                            self._handle_check_editor_modified)
        editor.close_editor_event.bind(self._handle_close)

    def _handle_esc_down(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.area.Navigate(flags=wx.NavigationKeyEvent.IsBackward)
            # Don't skip the event
        else:
            event.Skip()

    def _handle_tab_down(self, event):
        # Note that this natively still lets Ctrl+(Shift+)Tab navigate as
        # expected
        if event.GetKeyCode() == wx.WXK_TAB:
            if event.ShiftDown():
                self.area.Navigate(flags=wx.NavigationKeyEvent.IsBackward)
                # Don't skip the event
            else:
                self.area.Navigate(flags=wx.NavigationKeyEvent.IsForward)
                # Don't skip the event
        else:
            event.Skip()

    def _handle_text(self, event):
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
        self.mtimer = Timer(self.DELAY, self._reset_timer)
        self.mtimer.name = "wxtextarea"
        self.mtimer.start()

        event.Skip()

    def _reset_timer(self):
        self.tmrunning = False
        self._set_modified()

    def _set_modified(self):
        if self.area.GetValue() == self.original:
            self.area.SetModified(False)
        else:
            self.area.SetModified(True)

    def _reset_modified(self):
        self.original = self.area.GetValue()
        self.area.SetModified(False)

    def _is_modified(self):
        self._set_modified()
        return self.area.IsModified()

    def _handle_apply(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                    and self._is_modified():
            core_api.update_item_text(self.filename, self.id_,
                                      self.area.GetValue(), kwargs['group'],
                                      kwargs['description'])
            self._refresh_mod_state()

    def _refresh_mod_state(self):
        treedb = tree.dbs[self.filename]
        tabtitle = editor.Editor.make_title(self.area.GetLineText(0))
        wx.GetApp().nb_right.set_editor_title(self.item, tabtitle)

        self._reset_modified()

    def _handle_check_editor_modified(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                    and self._is_modified():
            editor.tabs[self.item].set_modified()

    def _handle_close(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_:
            if self.mtimer:
                self.mtimer.cancel()
            # It's necessary to explicitly unbind the handlers, otherwise this
            # object will never be garbage-collected due to circular
            # references, and the automatic unbinding won't work
            editor.apply_editor_event.bind(self._handle_apply, False)
            editor.check_modified_state_event.bind(
                                    self._handle_check_editor_modified, False)
            editor.close_editor_event.bind(self._handle_close, False)

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
