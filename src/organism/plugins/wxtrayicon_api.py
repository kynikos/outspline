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

import wxtrayicon


def insert_menu_item(pos, item, id_=wx.ID_ANY, help='', sep='none',
                     kind='normal', sub=None, icon=None):
    return wxtrayicon.trayicon.menu.insert_item(pos, item, id_, help, sep,  # @UndefinedVariable
                                                kind, sub, icon)


def bind_to_tray_menu(handler, button):
    return wxtrayicon.trayicon.Bind(wx.EVT_MENU, handler, button)


def bind_to_reset_menu(handler, bind=True):
    wxtrayicon.reset_menu_event.bind(handler, bind)


def bind_to_create_menu(handler, bind=True):
    wxtrayicon.create_menu_event.bind(handler, bind)
