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
    bounds_window = None

    def __init__(self, parent):
        self.parent = parent
        self.window = wx.PopupWindow(self.parent)

        # Initialize self.bounds_window so self.close will work anyway, as it
        # tries to unbind self.bounds_window
        self.bounds_window = wx.GetTopLevelParent(self.parent)

        box = wx.BoxSizer(wx.HORIZONTAL)
        self.window.SetSizer(box)

        self.text = wx.StaticText(self.window)
        box.Add(self.text, flag=wx.ALL, border=4)

        self.text.Bind(wx.EVT_LEFT_DOWN, self._handle_left_down)
        self.parent.Bind(wx.EVT_KEY_DOWN, self._handle_key_down)
        self.text.Bind(wx.EVT_KILL_FOCUS, self._handle_kill_focus)

    def _handle_motion_hidden(self, event):
        self.timer.Restart()
        event.Skip()

    def _handle_motion_shown(self, event):
        if not self.rect_bounds.Contains(event.GetPosition()):
            self.close()

        event.Skip()

    def _handle_left_down(self, event):
        self.close()
        event.Skip()

    def _handle_key_down(self, event):
        # Doesn't work the first time entering the parent window *****************************
        print('KEY_DOWN')
        self.close()
        event.Skip()

    def _handle_kill_focus(self, event):
        # Test ****************************************************************************
        print('KILL_FOCUS')
        self.close()
        event.Skip()

    def _handle_leave_window(self, event):
        print('WWW', self.bounds_window)  # *****************************************
        print('LEAVE', dir(event), event.GetPosition())  # **************************
        # Unless leaving to the tooltip window *****************************************
        # Maybe simply test again the rect contains? *********************************
        if False:  # *****************************************************************
            self.close()

        event.Skip()

    def enable(self, delay, call):
        self.parent.Bind(wx.EVT_MOTION, self._handle_motion_hidden)
        self.timer = wx.CallLater(delay, call)

    def popup(self, tip, rect_bounds=None, bounds_window=None):
        self.text.SetLabel(tip)

        self.parent.Unbind(wx.EVT_MOTION, handler=self._handle_motion_hidden)

        # First unbind the previously bound window
        self.bounds_window.Unbind(wx.EVT_LEAVE_WINDOW,
                                            handler=self._handle_leave_window)

        if bounds_window is None:
            self.bounds_window = wx.GetTopLevelParent(self.parent)
        else:
            self.bounds_window = bounds_window

        # Binding to EVT_LEAVE_WINDOW also allows closing the tooltip when
        # leaving rect_bounds from one of its sides that overlaps an edge of
        # bounds_window
        self.bounds_window.Bind(wx.EVT_LEAVE_WINDOW, self._handle_leave_window)

        if rect_bounds is not None:
            self.rect_bounds = rect_bounds
            self.parent.Bind(wx.EVT_MOTION, self._handle_motion_shown)

        self.window.Layout()
        self.window.Fit()
        self.window.Position(wx.GetMousePosition(), (0, 0))
        self.window.Show()

    def close(self):
        self.window.Show(False)
        self.parent.Unbind(wx.EVT_MOTION, handler=self._handle_motion_shown)
        self.bounds_window.Unbind(wx.EVT_LEAVE_WINDOW,
                                            handler=self._handle_leave_window)
        self.parent.Bind(wx.EVT_MOTION, self._handle_motion_hidden)
