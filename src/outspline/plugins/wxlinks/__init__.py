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

from outspline.coreaux_api import Event
import outspline.coreaux_api as coreaux_api
import outspline.extensions.links_api as links_api
import outspline.interfaces.wxgui_api as wxgui_api
wxcopypaste_api = coreaux_api.import_optional_plugin_api('wxcopypaste')

items = {}
formatted_items = {}

# See #214 for features left to be implemented ****************************************
# https://github.com/kynikos/outspline/issues/214 *************************************


class LinkManager():
    filename = None
    id_ = None
    fpanel = None
    lpanel = None
    origtarget = None
    target = None
    button_link = None

    def __init__(self, filename, id_):
        self.filename = filename
        self.id_ = id_

        self.fpanel = wxgui_api.add_plugin_to_editor(filename, id_,
                                                                'Manage links')

        self.lpanel = wx.Panel(self.fpanel)

        wxgui_api.add_window_to_plugin(filename, id_, self.fpanel, self.lpanel)

    def post_init(self):
        self.target = links_api.find_link_target(self.filename, self.id_)

        self._init_buttons()

        self.refresh_mod_state()

        self.resize_lpanel()

        if not self.target:
            wxgui_api.collapse_panel(self.filename, self.id_, self.fpanel)
            wxgui_api.resize_foldpanelbar(self.filename, self.id_)

        wxgui_api.bind_to_apply_editor(self.handle_apply)
        wxgui_api.bind_to_check_editor_modified_state(
                                             self.handle_check_editor_modified)
        wxgui_api.bind_to_close_editor(self.handle_close)

    def handle_apply(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                        and self.is_modified():
            links_api.make_link(self.filename, self.id_, self.target,
                                        kwargs['group'], kwargs['description'])
            self.refresh_mod_state()
            update_items_formatting(self.filename)

    def handle_check_editor_modified(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                        and self.is_modified():
            wxgui_api.set_editor_modified(self.filename, self.id_)

    def handle_close(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_:
            # It's necessary to explicitly unbind the handlers, otherwise this
            # object will never be garbage-collected due to circular
            # references, and the automatic unbinding won't work
            wxgui_api.bind_to_apply_editor(self.handle_apply, False)
            wxgui_api.bind_to_check_editor_modified_state(
                                      self.handle_check_editor_modified, False)
            wxgui_api.bind_to_close_editor(self.handle_close, False)

    def resize_lpanel(self):
        self.lpanel.Fit()
        wxgui_api.expand_panel(self.filename, self.id_, self.fpanel)
        wxgui_api.resize_foldpanelbar(self.filename, self.id_)

    def is_modified(self):
        return self.origtarget != self.target

    def refresh_mod_state(self):
        self.origtarget = self.target

    def _init_buttons(self):
        self.button_link = wx.Button(self.lpanel,
                                  label='Link to selected item', size=(-1, 24))

        self.lpanel.Bind(wx.EVT_BUTTON, self._link_to_selection,
                                                              self.button_link)

    def _link_to_selection(self, event):
        self.link_to_selection()

    def link_to_selection(self):
        filename = wxgui_api.get_selected_database_filename()

        if filename:
            selection = wxgui_api.get_tree_selections(filename, none=False,
                                                                    many=False)

            if selection:
                self.target = wxgui_api.get_tree_item_id(filename,
                                                                selection[0])

    @staticmethod
    def make_itemid(filename, id_):
        return '_'.join((filename, str(id_)))


def update_items_formatting(filename):
    new_formatted_items = set()
    wxfont = wxgui_api.get_main_frame().GetFont()

    rows = links_api.get_existing_links(filename)

    for row in rows:
        id_ = row['L_id']
        wxfont.SetStyle(wx.FONTSTYLE_ITALIC)
        wxgui_api.set_item_font(filename, id_, wxfont)
        new_formatted_items.add(id_)

    # Also remove italic from items that are no longer links (e.g. after
    # undoing a linking action)
    for oldid in formatted_items[filename] - new_formatted_items:
        wxfont.SetStyle(wx.FONTSTYLE_NORMAL)
        # oldid may not exist anymore, however wxgui_api.set_item_font is
        # protected against KeyError
        wxgui_api.set_item_font(filename, oldid, wxfont)

    formatted_items[filename] = new_formatted_items


def handle_open_database(kwargs):
    filename = kwargs['filename']

    if filename in links_api.get_supported_open_databases():
        formatted_items[filename] = set()
        update_items_formatting(filename)


def handle_close_database(kwargs):
    try:
        del formatted_items[kwargs['filename']]
    except KeyError:
        pass


def handle_tree_creation(kwargs):
    filename = kwargs['filename']

    if filename in links_api.get_supported_open_databases():
        update_items_formatting(filename)


def handle_open_editor(kwargs):
    filename = kwargs['filename']

    if filename in links_api.get_supported_open_databases():
        id_ = kwargs['id_']
        itemid = LinkManager.make_itemid(filename, id_)

        global items
        items[itemid] = LinkManager(filename, id_)
        items[itemid].post_init()


def main():
    wxgui_api.bind_to_open_database(handle_open_database)
    wxgui_api.bind_to_close_database(handle_close_database)
    wxgui_api.bind_to_open_editor(handle_open_editor)
    wxgui_api.bind_to_undo_tree(handle_tree_creation)
    wxgui_api.bind_to_redo_tree(handle_tree_creation)
    wxgui_api.bind_to_move_item(handle_tree_creation)

    if wxcopypaste_api:
        wxcopypaste_api.bind_to_items_pasted(handle_tree_creation)
