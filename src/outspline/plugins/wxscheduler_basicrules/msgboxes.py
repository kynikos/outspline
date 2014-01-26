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

import outspline.interfaces.wxgui_api as wxgui_api

generic = "Some rule parameters are not set correctly."
end_time = "End time must be greater than start time."
short_months = "Some selected months do not have enough days."


def warn_bad_rule(message):
    return wx.MessageDialog(wxgui_api.get_main_frame(), message,
                    caption="Create rule", style=wx.OK | wx.ICON_EXCLAMATION)
