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

ID_SEARCH = None


def handle_open_database(kwargs):
    filename = kwargs['filename']
    
    accels = [(wx.ACCEL_CTRL, ord('f'), ID_SEARCH), ]
    
    wxgui_api.add_database_accelerators(filename, accels)


def main():
    config = coreaux_api.get_plugin_configuration('wxdbsearch')
    
    global ID_SEARCH
    ID_SEARCH = wx.NewId()
    
    wxgui_api.insert_menu_item('Database', config.get_int('menu_pos'),
                               'Searc&h...', id_=ID_SEARCH,
                               help='Search in the database',
                               sep=config['menu_sep'],
                               icon='@dbsearch').Enable(False)
    
    #wxgui_api.bind_to_open_database(handle_open_database)
