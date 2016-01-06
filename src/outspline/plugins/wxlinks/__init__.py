# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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
import outspline.core_api as core_api
import outspline.extensions.links_api as links_api
import outspline.interfaces.wxgui_api as wxgui_api
wxcopypaste_api = coreaux_api.import_optional_plugin_api('wxcopypaste')

base = None

# See #214 for features left to be implemented


class Main(object):
    def __init__(self):
        self.items = {}
        self.itemicons = {}

        wxgui_api.install_bundled_icon("wxlinks", '@links',
                                                    ("Tango", "links16.png"))

        ViewMenu(self)

        wxgui_api.bind_to_creating_tree(self._handle_creating_tree)
        wxgui_api.bind_to_close_database(self._handle_close_database)
        wxgui_api.bind_to_open_editor(self._handle_open_editor)
        wxgui_api.bind_to_close_editor(self._handle_close_editor)

    def _handle_creating_tree(self, kwargs):
        filename = kwargs['filename']

        if filename in links_api.get_supported_open_databases():
            self.itemicons[filename] = TreeItemIcons(filename)

    def _handle_close_database(self, kwargs):
        try:
            del self.itemicons[kwargs['filename']]
        except KeyError:
            pass

    def _handle_open_editor(self, kwargs):
        filename = kwargs['filename']

        if filename in links_api.get_supported_open_databases():
            id_ = kwargs['id_']
            itemid = self._make_itemid(filename, id_)
            self.items[itemid] = LinkManager(filename, id_)
            self.items[itemid].post_init()

    def _handle_close_editor(self, kwargs):
        itemid = self._make_itemid(kwargs['filename'], kwargs['id_'])

        try:
            del self.items[itemid]
        except KeyError:
            pass

    def get_link_manager(self, filename, id_):
        return self.items[self._make_itemid(filename, id_)]

    def _make_itemid(self, filename, id_):
        return '_'.join((filename, str(id_)))


class LinkManager(object):
    def __init__(self, filename, id_):
        self.filename = filename
        self.id_ = id_

        self.fpanel = wxgui_api.add_plugin_to_editor(filename, id_,
                                                                'Manage links')

        self.lpanel = wx.Panel(self.fpanel)

        config = coreaux_api.get_plugin_configuration('wxlinks')(
                                                        'ContextualShortcuts')
        accelerators = {
            config["focus"]: lambda event: self.set_focus(),
            config["toggle"]: lambda event: self.toggle_focus(),
        }

        wxgui_api.add_window_to_plugin(filename, id_, self.fpanel, self.lpanel,
                                                                accelerators)

    def post_init(self):
        self.target = links_api.find_link_target(self.filename, self.id_)

        self._init_buttons()
        self._refresh_mod_state()
        self.lpanel.Fit()
        wxgui_api.expand_panel(self.filename, self.id_, self.fpanel)

        if not self.target:
            wxgui_api.collapse_panel(self.filename, self.id_, self.fpanel)

        wxgui_api.bind_to_apply_editor(self._handle_apply)
        wxgui_api.bind_to_check_editor_modified_state(
                                            self._handle_check_editor_modified)
        wxgui_api.bind_to_close_editor(self._handle_close)

    def _handle_apply(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                    and self._is_modified():
            links_api.make_link(self.filename, self.id_, self.target,
                                        kwargs['group'], kwargs['description'])
            self._refresh_mod_state()

    def _handle_check_editor_modified(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                    and self._is_modified():
            wxgui_api.set_editor_modified(self.filename, self.id_)

    def _handle_close(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_:
            # It's necessary to explicitly unbind the handlers, otherwise this
            # object will never be garbage-collected due to circular
            # references, and the automatic unbinding won't work
            wxgui_api.bind_to_apply_editor(self._handle_apply, False)
            wxgui_api.bind_to_check_editor_modified_state(
                                    self._handle_check_editor_modified, False)
            wxgui_api.bind_to_close_editor(self._handle_close, False)

    def _is_modified(self):
        return self.origtarget != self.target

    def _refresh_mod_state(self):
        self.origtarget = self.target

    def _init_buttons(self):
        self.button_link = wx.Button(self.lpanel,
                                                label='&Link to selected item')

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

    def set_focus(self):
        wxgui_api.expand_panel(self.filename, self.id_, self.fpanel)
        self.button_link.SetFocus()

    def toggle_focus(self):
        if wxgui_api.toggle_panel(self.filename, self.id_, self.fpanel):
            self.button_link.SetFocus()


class TreeItemIcons(object):
    def __init__(self, filename):
        self.filename = filename

        config = coreaux_api.get_plugin_configuration('wxlinks')('TreeIcons')
        char = config['symbol']

        if char != '':
            bits_to_colour = {b: wx.Colour() for b in xrange(1, 6)}
            bits_to_colour[1].SetFromString(config['color_valid'])
            bits_to_colour[2].SetFromString(config['color_broken'])
            bits_to_colour[3].SetFromString(config['color_target'])
            bits_to_colour[4].SetFromString(config['color_valid_and_target'])
            bits_to_colour[5].SetFromString(config['color_broken_and_target'])

            self.property_shift, self.property_mask = \
                                            wxgui_api.add_item_property(
                                            filename, 3, char, bits_to_colour)

            links_api.bind_to_upsert_link(self._handle_upsert_link)
            links_api.bind_to_delete_link(self._handle_delete_link)
            links_api.bind_to_break_link(self._handle_break_links)
            links_api.bind_to_history_insert(self._handle_history)
            links_api.bind_to_history_update(self._handle_history)
            links_api.bind_to_history_delete(self._handle_history)

            wxgui_api.bind_to_open_database(self._handle_open_database)
            wxgui_api.bind_to_close_database(self._handle_close_database)

            if wxcopypaste_api:
                wxcopypaste_api.bind_to_items_pasted(self._handle_paste)

    def _handle_open_database(self, kwargs):
        if kwargs['filename'] == self.filename:
            rows = links_api.get_existing_links(self.filename)
            links = set()
            broken_links = set()
            targets = set()

            for row in rows:
                target = row['L_target']

                if target is not None:
                    links.add(row['L_id'])
                    targets.add(target)
                else:
                    broken_links.add(row['L_id'])

            shift = self.property_shift
            mask = self.property_mask

            for rbits, set_ in ((1, links - targets),
                                (2, broken_links - targets),
                                (3, targets - links - broken_links),
                                (4, links & targets),
                                (5, broken_links & targets)):
                for id_ in set_:
                    self._update_item(id_, rbits)

    def _handle_close_database(self, kwargs):
        if kwargs['filename'] == self.filename:
            links_api.bind_to_upsert_link(self._handle_upsert_link, False)
            links_api.bind_to_delete_link(self._handle_delete_link, False)
            links_api.bind_to_break_link(self._handle_break_links, False)

            wxgui_api.bind_to_open_database(self._handle_open_database, False)
            wxgui_api.bind_to_close_database(self._handle_close_database,
                                                                        False)
            links_api.bind_to_history_insert(self._handle_history, False)
            links_api.bind_to_history_update(self._handle_history, False)
            links_api.bind_to_history_delete(self._handle_history, False)

            if wxcopypaste_api:
                wxcopypaste_api.bind_to_items_pasted(self._handle_paste, False)

    def _handle_upsert_link(self, kwargs):
        if kwargs['filename'] == self.filename:
            id_ = kwargs['id_']
            target = kwargs['target']
            oldtarget = kwargs['oldtarget']
            backlinks = links_api.find_back_links(self.filename, id_)
            target_target = links_api.find_link_target(self.filename, target)

            if target is None:
                rbits = 5 if len(backlinks) > 0 else 2
            else:
                rbits = 4 if len(backlinks) > 0 else 1

            if target_target is False:
                target_rbits = 3
            elif target_target is None:
                target_rbits = 5
            else:
                target_rbits = 4

            self._update_item(id_, rbits)

            if target is not None:
                self._update_item(target, target_rbits)

            # oldtarget may not exist anymore
            if oldtarget is not False and core_api.is_item(self.filename,
                                                                    oldtarget):
                self._reset_item(oldtarget)

    def _handle_delete_link(self, kwargs):
        if kwargs['filename'] == self.filename:
            id_ = kwargs['id_']
            backlinks = links_api.find_back_links(self.filename, id_)
            rbits = 3 if len(backlinks) > 0 else 0

            # id_ may not exist anymore
            if core_api.is_item(self.filename, id_):
                self._update_item(id_, rbits)

            oldtarget = kwargs['oldtarget']

            # oldtarget may not exist anymore
            if core_api.is_item(self.filename, oldtarget):
                self._reset_item(oldtarget)

    def _handle_break_links(self, kwargs):
        if kwargs['filename'] == self.filename:
            for id_ in kwargs['ids']:
                backlinks = links_api.find_back_links(self.filename, id_)
                rbits = 5 if len(backlinks) > 0 else 2
                self._update_item(id_, rbits)

            oldtarget = kwargs['oldtarget']

            # oldtarget may not exist anymore
            if core_api.is_item(self.filename, oldtarget):
                self._reset_item(oldtarget)

    def _handle_history(self, kwargs):
        if kwargs['filename'] == self.filename:
            id_ = kwargs['id_']

            # The history event may have effects also on target and backlinks
            backlinks = links_api.find_back_links(self.filename, id_)
            target = links_api.find_link_target(self.filename, id_)

            if target is False:
                rbits = 3 if len(backlinks) > 0 else 0

                # Find any possible old target and update it
                # This fixes for example the case of undoing the linking
                # of an item to another, which wouldn't update the tree
                # icon of the old target because this function would be
                # called *after* removing the link, so the old target
                # would not be retrievable through a database query
                old_target = links_api.get_last_known_target(self.filename, id_)

                if old_target is not None:
                    self._reset_item_no_tree_update(old_target)

            elif target is None:
                rbits = 5 if len(backlinks) > 0 else 2

            else:
                rbits = 4 if len(backlinks) > 0 else 1

                target_target = links_api.find_link_target(self.filename,
                                                                        target)

                if target_target is False:
                    target_rbits = 3
                elif target_target is None:
                    target_rbits = 5
                else:
                    target_rbits = 4

                self._update_item_no_tree_update(target, target_rbits)

            self._update_item_no_tree_update(id_, rbits)

            for blink in backlinks:
                blink_backlinks = links_api.find_back_links(self.filename,
                                                                        blink)
                blink_rbits = 4 if len(blink_backlinks) > 0 else 1
                self._update_item_no_tree_update(blink, blink_rbits)

    def _handle_paste(self, kwargs):
        if kwargs['filename'] == self.filename:
            for id_ in kwargs['ids']:
                self._reset_item(id_)

    def _compute_rbits(self, id_):
        backlinks = links_api.find_back_links(self.filename, id_)
        target = links_api.find_link_target(self.filename, id_)

        if target is False:
            rbits = 3 if len(backlinks) > 0 else 0
        elif target is None:
            rbits = 5 if len(backlinks) > 0 else 2
        else:
            rbits = 4 if len(backlinks) > 0 else 1

        return rbits

    def _reset_item_no_tree_update(self, id_):
        rbits = self._compute_rbits(id_)
        self._update_item_no_tree_update(id_, rbits)

    def _reset_item(self, id_):
        rbits = self._compute_rbits(id_)
        self._update_item(id_, rbits)

    def _update_item_properties(self, id_, rbits):
        bits = rbits << self.property_shift
        wxgui_api.update_item_properties(self.filename, id_, bits,
                                                        self.property_mask)

    def _update_item_no_tree_update(self, id_, rbits):
        self._update_item_properties(id_, rbits)
        wxgui_api.request_tree_item_refresh(self.filename, id_)

    def _update_item(self, id_, rbits):
        self._update_item_properties(id_, rbits)
        wxgui_api.update_tree_item(self.filename, id_)


class ViewMenu(object):
    def __init__(self, plugin):
        self.plugin = plugin

        self.ID_MAIN = wx.NewId()
        self.ID_FOCUS = wx.NewId()
        self.ID_TOGGLE = wx.NewId()

        submenu = wx.Menu()

        config = coreaux_api.get_plugin_configuration('wxlinks')(
                                                            'GlobalShortcuts')

        self.main = wx.MenuItem(wxgui_api.get_menu_view_editors(),
                        self.ID_MAIN,
                        '&Links manager', 'Links manager navigation actions',
                        subMenu=submenu)
        self.focus = wx.MenuItem(submenu, self.ID_FOCUS,
                    "&Focus\t{}".format(config['focus']),
                    "Focus links manager panel")
        self.toggle = wx.MenuItem(submenu, self.ID_TOGGLE,
                "&Toggle\t{}".format(config['toggle']),
                "Toggle links manager panel")

        self.main.SetBitmap(wxgui_api.get_menu_icon('@links'))
        self.focus.SetBitmap(wxgui_api.get_menu_icon('@jump'))
        self.toggle.SetBitmap(wxgui_api.get_menu_icon('@toggle'))

        wxgui_api.add_menu_editor_plugin(self.main)
        submenu.AppendItem(self.focus)
        submenu.AppendItem(self.toggle)

        wxgui_api.bind_to_menu(self._focus, self.focus)
        wxgui_api.bind_to_menu(self._toggle, self.toggle)

        wxgui_api.bind_to_menu_view_editors_disable(self._disable_items)
        wxgui_api.bind_to_reset_menu_items(self._reset_items)

    def _disable_items(self, kwargs):
        self.main.Enable(False)

    def _reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.main.Enable()

    def _focus(self, event):
        filename, id_ = wxgui_api.get_selected_editor_identification()

        if filename:
            self.plugin.get_link_manager(filename, id_).set_focus()

    def _toggle(self, event):
        filename, id_ = wxgui_api.get_selected_editor_identification()

        if filename:
            self.plugin.get_link_manager(filename, id_).toggle_focus()

def main():
    global base
    base = Main()
