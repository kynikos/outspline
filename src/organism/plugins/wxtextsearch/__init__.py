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

ID_SEARCH = None


def handle_open_editor(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']

    accels = [(wx.ACCEL_CTRL, ord('f'), ID_SEARCH), ]

    wxgui_api.add_editor_accelerators(filename, id_, accels)


def main():
    config = coreaux_api.get_plugin_configuration('wxtextsearch')

    global ID_SEARCH
    ID_SEARCH = wx.NewId()

    wxgui_api.insert_menu_item('Editor', config.get_int('menu_pos'),
                               '&Find/Replace...', id_=ID_SEARCH,
                               help='Find text in the editor',
                               sep=config['menu_sep'],
                               icon='@textsearch').Enable(False)

    wxgui_api.bind_to_open_editor(handle_open_editor)
