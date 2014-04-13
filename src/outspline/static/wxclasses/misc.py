# wxClasses
# Copyright (C) 2013-2014 Dario Giovannetti <dev@dariogiovannetti.net>
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


class NarrowSpinCtrl(wx.SpinCtrl):
    def __init__(self, *args, **kwargs):
        wx.SpinCtrl.__init__(self, *args, **kwargs)

        font = self.GetFont()
        dc = wx.WindowDC(self)
        dc.SetFont(font)
        swidth = dc.GetTextExtent("0")[0]
        # Some skins have arrows wider than others: Elegant Brit and Orion are
        #   the largest I've found
        ARROWS = 28

        # Note that min_number's length includes also the minus sign, if
        # negative
        width = swidth * max((len(str(self.GetMin())),
                                            len(str(self.GetMax())))) + ARROWS

        height = self.GetMinSize()[1]
        self.SetMinSize((width, height))

