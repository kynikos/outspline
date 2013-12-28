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

import wxtrayicon


def insert_menu_item(pos, item, id_=wx.ID_ANY, help='', sep='none',
                     kind='normal', sub=None, icon=None):
    return wxtrayicon.trayicon.menu.insert_item(pos, item, id_, help, sep,
                                                kind, sub, icon)


def start_blinking(start_id, alt_icon=None):
    return wxtrayicon.trayicon.icon.start(start_id, alt_icon=alt_icon)


def stop_blinking(start_id):
    return wxtrayicon.trayicon.icon.stop(start_id)


def set_tooltip_value(tooltip_id, value):
    return wxtrayicon.trayicon.icon.set_tooltip_value(tooltip_id, value)


def unset_tooltip_value(tooltip_id):
    return wxtrayicon.trayicon.icon.unset_tooltip_value(tooltip_id)


def bind_to_tray_menu(handler, button):
    return wxtrayicon.trayicon.Bind(wx.EVT_MENU, handler, button)


def bind_to_reset_menu(handler, bind=True):
    wxtrayicon.reset_menu_event.bind(handler, bind)


def bind_to_create_menu(handler, bind=True):
    wxtrayicon.create_menu_event.bind(handler, bind)
