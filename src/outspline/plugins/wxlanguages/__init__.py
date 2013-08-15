# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import outspline.coreaux_api as coreaux_api
import outspline.interfaces.wxgui_api as wxgui_api


class MenuLanguages(wx.Menu):
    ID_ENG = None
    eng = None
    ID_ITA = None
    ita = None

    def __init__(self):
        # Note that the content is still hard-coded, will need to be *************
        # separated from the source in order to enable language choice ***********

        wx.Menu.__init__(self)

        self.ID_ENG = wx.NewId()
        self.ID_ITA = wx.NewId()

        self.eng = self.Append(self.ID_ENG, "&English",
                               "View Outspline in English").Enable(False)
        self.ita = self.Append(self.ID_ITA, "&Italiano",
                               "Visualizza Outspline in Italiano").Enable(False)


def main():
    config = coreaux_api.get_plugin_configuration('wxlanguages')
    ID_LANGUAGES = wx.NewId()
    wxgui_api.insert_menu_item('View', config.get_int('menu_pos'),
                               '&Languages', id_=ID_LANGUAGES,
                               help='Select a language for the interface',
                               sep=config['menu_sep'],
                               sub=MenuLanguages(),
                               icon='@languages').Enable(False)
