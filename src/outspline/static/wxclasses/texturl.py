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


class TextUrlCtrl(wx.TextCtrl):
    urlstart = None
    urlend = None

    def __init__(self, parent, value='', style=0):
        wx.TextCtrl.__init__(self, parent, value=value, style=style |
                                                                wx.TE_AUTO_URL)

        self.Bind(wx.EVT_TEXT_URL, self.handle_mouse_on_url)

    def handle_mouse_on_url(self, event):
        self.urlstart = event.GetURLStart()
        self.urlend = event.GetURLEnd()

        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

        self.launch_browser(event)

        self.Bind(wx.EVT_MOTION, self.reset_cursor)
        self.Bind(wx.EVT_TEXT_URL, self.launch_browser)

    def launch_browser(self, event):
        if event.GetMouseEvent().LeftUp():
            wx.LaunchDefaultBrowser(self.GetRange(self.urlstart, self.urlend))

    def reset_cursor(self, event):
        hitpos = self.HitTestPos(event.GetPosition())[1]

        if (self.urlstart is not None and hitpos < self.urlstart) or \
                            (self.urlend is not None and hitpos > self.urlend):
            self.urlstart = None
            self.urlend = None

            self.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))

            self.Bind(wx.EVT_TEXT_URL, self.handle_mouse_on_url)
            self.Bind(wx.EVT_MOTION, None)
