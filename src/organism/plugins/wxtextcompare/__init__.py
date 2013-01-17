# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
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

import organism.coreaux_api as coreaux_api
import organism.interfaces.wxgui_api as wxgui_api


class MenuCompare(wx.Menu):
    ID_TWO = None
    two = None
    ID_EDITOR = None
    editor = None
    ID_ORIGINAL = None
    orig = None
    
    def __init__(self):
        wx.Menu.__init__(self)
        
        self.ID_TWO = wx.NewId()
        self.ID_EDITOR = wx.NewId()
        self.ID_ORIGINAL = wx.NewId()
        
        self.two = self.Append(self.ID_TWO, "&Two items",
                               "Compare two selected items").Enable(False)
        self.editor = self.Append(self.ID_EDITOR, "&Editor with item",
                                  "Compare editor with selected item"
                                 ).Enable(False)
        self.orig = self.Append(self.ID_ORIGINAL, "&Editor with original",
                                "Compare editor with original text"
                               ).Enable(False)


def main():
    config = coreaux_api.get_plugin_configuration('wxtextcompare')
    ID_COMPARE = wx.NewId()
    wxgui_api.insert_menu_item('Editor', config.get_int('menu_pos'),
                               'Co&mpare', id_=ID_COMPARE,
                               help='Compare the text of two items',
                               sep=config['menu_sep'],
                               sub=MenuCompare(),
                               icon='@compare').Enable(False)
