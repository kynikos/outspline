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
    def __init__(self, *args, **kwargs):
        print(args)
        if 'style' in kwargs:
            kwargs['style'] |= wx.TE_AUTO_URL
        else:
            kwargs['style'] = wx.TE_AUTO_URL

        wx.TextCtrl.__init__(self, *args, **kwargs)

        self.Bind(wx.EVT_TEXT_URL, self.handle_mouse_on_url)

    def handle_mouse_on_url(self, event):
        if event.GetMouseEvent().LeftUp():
            wx.LaunchDefaultBrowser(self.GetRange(event.GetURLStart(),
                                                            event.GetURLEnd()))
