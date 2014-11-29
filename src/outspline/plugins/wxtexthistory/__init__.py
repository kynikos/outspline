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

import outspline.static.texthistory as texthistory

import outspline.coreaux_api as coreaux_api
import outspline.interfaces.wxgui_api as wxgui_api


class TextHistory(object):
    def __init__(self):
        self.config = coreaux_api.get_plugin_configuration('wxtexthistory')
        self.areas = {}
        Menu(self)

        wxgui_api.bind_to_open_editor(self._handle_open_editor)

    def _handle_open_editor(self, kwargs):
        self.areas[kwargs['item']] = texthistory.WxTextHistory(
                    wxgui_api.get_textctrl(kwargs['filename'], kwargs['id_']),
                    kwargs['text'], self.config.get_int('max_undos'),
                    self.config.get_int('min_update_interval'))

    def get_area(self, item):
        return self.areas[item]

    def undo_text(self, event):
        tab = wxgui_api.get_selected_editor()

        if tab:
            self.areas[tab].undo()

    def redo_text(self, event):
        tab = wxgui_api.get_selected_editor()

        if tab:
            self.areas[tab].redo()


class Menu(object):
    def __init__(self, plugin):
        self.plugin = plugin

        self.ID_UNDO = wx.NewId()
        self.ID_REDO = wx.NewId()

        config = coreaux_api.get_plugin_configuration('wxtexthistory')(
                                                            'GlobalShortcuts')

        self.mundo = wx.MenuItem(wxgui_api.get_menu_editor(), self.ID_UNDO,
                                            '&Undo\t{}'.format(config['undo']),
                                            'Undo the previous text edit')
        self.mredo = wx.MenuItem(wxgui_api.get_menu_editor(), self.ID_REDO,
                                            '&Redo\t{}'.format(config['redo']),
                                            'Redo the next text edit')
        separator = wx.MenuItem(wxgui_api.get_menu_editor(),
                                                        kind=wx.ITEM_SEPARATOR)

        self.mundo.SetBitmap(wxgui_api.get_menu_icon('@undo'))
        self.mredo.SetBitmap(wxgui_api.get_menu_icon('@redo'))

        # Add in reverse order
        wxgui_api.add_menu_editor_item(separator)
        wxgui_api.add_menu_editor_item(self.mredo)
        wxgui_api.add_menu_editor_item(self.mundo)

        wxgui_api.bind_to_menu(self.plugin.undo_text, self.mundo)
        wxgui_api.bind_to_menu(self.plugin.redo_text, self.mredo)

        wxgui_api.bind_to_reset_menu_items(self._reset)
        wxgui_api.bind_to_menu_edit_update(self._update)

    def _reset(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.mundo.Enable()
        self.mredo.Enable()

    def _update(self, kwargs):
        item = kwargs['item']

        # item is None is no editor is open
        if item:
            area = self.plugin.get_area(item)

            if area.can_undo():
                self.mundo.Enable()
            else:
                self.mundo.Enable(False)

            if area.can_redo():
                self.mredo.Enable()
            else:
                self.mredo.Enable(False)

        else:
            self.mundo.Enable(False)
            self.mredo.Enable(False)


def main():
    TextHistory()
