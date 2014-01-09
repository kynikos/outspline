# wxClasses
# Copyright (C) 2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of wxClasses.
#
# wxClasses is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wxClasses is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with wxClasses.  If not, see <http://www.gnu.org/licenses/>.

import wx


class ToolTip():
    parent = None
    window = None
    text = None
    timer = None
    rect_bounds = None

    def __init__(self, parent, delay, call):
        self.parent = parent
        self.window = wx.PopupWindow(self.parent)

        box = wx.BoxSizer(wx.HORIZONTAL)
        self.window.SetSizer(box)

        self.text = wx.StaticText(self.window)
        box.Add(self.text, flag=wx.ALL, border=4)

        self.text.Bind(wx.EVT_LEFT_DOWN, self._handle_left_down)
        self.parent.Bind(wx.EVT_KEY_DOWN, self._handle_key_down)
        self.text.Bind(wx.EVT_KILL_FOCUS, self._handle_kill_focus)

        # self.parent must also be bound to EVT_LEAVE_WINDOW
        self.parent.Bind(wx.EVT_MOTION, self._handle_motion_hidden)

        # Binding to EVT_LEAVE_WINDOW also allows closing the tooltip when
        # leaving rect_bounds from one of its sides that overlaps an edge of
        # parent
        # parent is the correct window to bind because it's also bound to
        # EVT_MOTION, meaning that outside of it motion events won't be handled
        self.parent.Bind(wx.EVT_LEAVE_WINDOW, self._handle_leave_window)

        self.timer = wx.CallLater(delay, call)

    def _handle_left_down(self, event):
        self.close()
        event.Skip()

    def _handle_key_down(self, event):
        # Doesn't work if the parent window doesn't have focus *****************************
        print('KEY_DOWN')  # ***********************************************************
        self.close()
        event.Skip()

    def _handle_kill_focus(self, event):
        # Test: let the tooltip popup and then switch window with ALT+TAB: ***********************
        #   the tooltip must close (disable the closing on key down first!) **********************
        print('KILL_FOCUS')  # ***********************************************************
        self.close()
        event.Skip()

    def _handle_motion_hidden(self, event):
        self.timer.Restart()
        event.Skip()

    def _handle_motion_shown(self, event):
        self._close_conditional()
        event.Skip()

    def _handle_leave_window(self, event):
        # EVT_LEAVE_WINDOW is triggered also if the mouse enters a child window
        # *inside* rect_bounds, and in that case the tooltip should not be
        # closed
        # For some reason EVT_LEAVE_WINDOW is triggered twice for example in a
        # ListCtrl with different event.Position parameters (apparently
        # differing by the list header height), so one of them would always be
        # out of rect_bounds, thus always closing the tooltip; for this reason
        # use self._close_conditional, which in turn makes use of the more
        # reliable wx.GetMousePosition()
        self._close_conditional()
        event.Skip()

    def popup(self, tip, rect_bounds=None):
        self.text.SetLabel(tip)

        self.parent.Unbind(wx.EVT_MOTION, handler=self._handle_motion_hidden)

        if rect_bounds is not None:
            self.rect_bounds = rect_bounds
            self.parent.Bind(wx.EVT_MOTION, self._handle_motion_shown)

        self.window.Layout()
        self.window.Fit()
        self.window.Position(wx.GetMousePosition(), (0, 0))
        self.window.Show()

    def _close_conditional(self):
        if self.rect_bounds and not self.rect_bounds.Contains(
                            self.parent.ScreenToClient(wx.GetMousePosition())):
            self.close()

    def close(self):
        self.window.Show(False)
        self.parent.Unbind(wx.EVT_MOTION, handler=self._handle_motion_shown)
        self.parent.Bind(wx.EVT_MOTION, self._handle_motion_hidden)
