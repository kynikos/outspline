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

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import Event
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api
import outspline.extensions.copypaste_api as copypaste_api

import msgboxes

cut_items_event = Event()
items_pasted_event = Event()

plugin = None


class Main(object):
    def __init__(self):
        self.mainmenu = MainMenu()
        self.cmenus = {}

        wxgui_api.bind_to_open_database(self._handle_open_database)
        wxgui_api.bind_to_close_database(self._handle_close_database)

    def _handle_open_database(self, kwargs):
        filename = kwargs['filename']
        self.cmenus[filename] = TreeContextMenu(filename, self.mainmenu)

    def _handle_close_database(self, kwargs):
        del self.cmenus[kwargs['filename']]


class MainMenu(object):
    def __init__(self):
        self.ID_CUT = wx.NewId()
        self.ID_COPY = wx.NewId()
        self.ID_PASTE = wx.NewId()
        self.ID_PASTE_SUB = wx.NewId()

        config = coreaux_api.get_plugin_configuration('wxcopypaste')(
                                                                'Shortcuts')

        self.mpaste_label_1 = '&Paste items\t{}'.format(config['paste'])
        self.mpaste_help_1 = 'Paste items as root items'
        self.mpaste_label_2 = '&Paste as siblings\t{}'.format(config['paste'])
        self.mpaste_help_2 = 'Paste items as siblings below the selected item'

        self.mcut = wx.MenuItem(wxgui_api.get_menu_database(), self.ID_CUT,
                                        'Cu&t items\t{}'.format(config['cut']),
                                        'Cut the selected items')
        self.mcopy = wx.MenuItem(wxgui_api.get_menu_database(), self.ID_COPY,
                                    '&Copy items\t{}'.format(config['copy']),
                                    'Copy the selected items')
        self.mpaste = wx.MenuItem(wxgui_api.get_menu_database(), self.ID_PASTE,
                                    self.mpaste_label_1, self.mpaste_help_1)
        self.mpastesub = wx.MenuItem(wxgui_api.get_menu_database(),
                                                            self.ID_PASTE_SUB,
                    'P&aste as children\t{}'.format(config['paste_children']),
                    'Paste items as children of the selected item')

        self.mcut.SetBitmap(wx.ArtProvider.GetBitmap('@cut', wx.ART_MENU))
        self.mcopy.SetBitmap(wx.ArtProvider.GetBitmap('@copy', wx.ART_MENU))
        self.mpaste.SetBitmap(wx.ArtProvider.GetBitmap('@paste', wx.ART_MENU))
        self.mpastesub.SetBitmap(wx.ArtProvider.GetBitmap('@paste',
                                                                wx.ART_MENU))

        separator = wx.MenuItem(wxgui_api.get_menu_database(),
                                                        kind=wx.ITEM_SEPARATOR)

        # Add in reverse order
        wxgui_api.add_menu_database_item(separator)
        wxgui_api.add_menu_database_item(self.mpastesub)
        wxgui_api.add_menu_database_item(self.mpaste)
        wxgui_api.add_menu_database_item(self.mcopy)
        wxgui_api.add_menu_database_item(self.mcut)

        wxgui_api.bind_to_menu(self.cut_items, self.mcut)
        wxgui_api.bind_to_menu(self.copy_items, self.mcopy)
        wxgui_api.bind_to_menu(self.paste_items_as_siblings, self.mpaste)
        wxgui_api.bind_to_menu(self.paste_items_as_children, self.mpastesub)

        wxgui_api.bind_to_reset_menu_items(self._handle_reset_menu_items)
        wxgui_api.bind_to_menu_database_update(self._handle_enable_tree_menus)

    def _handle_reset_menu_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.mcut.Enable()
        self.mcopy.Enable()
        self.mpaste.Enable()
        self.mpastesub.Enable()

    def _handle_enable_tree_menus(self, kwargs):
        filename = kwargs['filename']

        self.mcut.Enable(False)
        self.mcopy.Enable(False)
        self.mpaste.Enable(False)
        self.mpastesub.Enable(False)
        self.mpaste.SetItemLabel(self.mpaste_label_1)
        self.mpaste.SetHelp(self.mpaste_help_1)

        # filename is None is no database is open
        if filename:
            sel = wxgui_api.get_tree_selections(filename)

            if len(sel) == 1:
                self.mcut.Enable()
                self.mcopy.Enable()

                if copypaste_api.has_copied_items(filename):
                    self.mpaste.Enable()
                    self.mpaste.SetItemLabel(self.mpaste_label_2)
                    self.mpaste.SetHelp(self.mpaste_help_2)
                    self.mpastesub.Enable()

            elif len(sel) > 1:
                self.mcut.Enable()
                self.mcopy.Enable()

            elif copypaste_api.has_copied_items(filename):
                self.mpaste.Enable()

    def cut_items(self, event, no_confirm=False):
        if core_api.block_databases():
            filename = wxgui_api.get_selected_database_filename()

            # This method may be launched by the menu accelerator, but no
            # database may be open
            if filename:
                # get_tree_selections() arguments must be compatible with the
                # ones used in self.delete_items()
                selection = wxgui_api.get_tree_selections(filename, none=False,
                                                            descendants=True)

                if selection:
                    items = []

                    for item in selection:
                        id_ = wxgui_api.get_tree_item_id(filename, item)

                        if not wxgui_api.close_editor(filename, id_,
                                    ask='quiet' if no_confirm else 'discard'):
                            core_api.release_databases()
                            return False

                        items.append(id_)

                    copypaste_api.copy_items(filename, items)

                    wxgui_api.delete_items(filename, items,
                                description='Cut {} items'.format(len(items)))
                    wxgui_api.refresh_history(filename)
                    cut_items_event.signal()

            core_api.release_databases()

    def copy_items(self, event):
        if core_api.block_databases():
            filename = wxgui_api.get_selected_database_filename()

            # This method may be launched by the menu accelerator, but not
            # database may be open
            if filename:
                # get_tree_selections() arguments must be compatible with the
                # ones used in self.delete_items()
                selection = wxgui_api.get_tree_selections(filename, none=False,
                                                            descendants=True)

                if selection:
                    items = []

                    for item in selection:
                        items.append(wxgui_api.get_tree_item_id(filename,
                                                                        item))

                    copypaste_api.copy_items(filename, items)

            core_api.release_databases()

    def paste_items_as_siblings(self, event, no_confirm=False):
        if core_api.block_databases():
            filename = wxgui_api.get_selected_database_filename()

            # This method may be launched by the menu accelerator, but not
            # database may be open
            if filename and \
                    (no_confirm or copypaste_api.can_paste_safely(filename) or
                    msgboxes.unsafe_paste_confirm().ShowModal() == wx.ID_OK):
                # Do not use none=False in order to allow pasting in an empty
                # database
                selection = wxgui_api.get_tree_selections(filename, many=False)

                # If multiple items are selected, selection will be False
                if selection is not False:
                    if len(selection) > 0:
                        baseid = wxgui_api.get_tree_item_id(filename,
                                                                selection[0])

                        roots, ids = copypaste_api.paste_items_as_siblings(
                                filename, baseid, description='Paste items')
                    else:
                        roots, ids = copypaste_api.paste_items_as_children(
                                        filename, 0, description='Paste items')

                    wxgui_api.refresh_history(filename)

                    items_pasted_event.signal(filename=filename, roots=roots,
                                                                    ids=ids)

            core_api.release_databases()

    def paste_items_as_children(self, event, no_confirm=False):
        if core_api.block_databases():
            filename = wxgui_api.get_selected_database_filename()

            # This method may be launched by the menu accelerator, but not
            # database may be open
            if filename:
                selection = wxgui_api.get_tree_selections(filename, none=False,
                                                                    many=False)

                if selection and (no_confirm or
                                    copypaste_api.can_paste_safely(filename) or
                                    msgboxes.unsafe_paste_confirm().ShowModal(
                                    ) == wx.ID_OK):
                    baseid = wxgui_api.get_tree_item_id(filename, selection[0])

                    roots, ids = copypaste_api.paste_items_as_children(
                            filename, baseid, description='Paste sub-items')

                    wxgui_api.refresh_history(filename)

                    items_pasted_event.signal(filename=filename, roots=roots,
                                                                    ids=ids)

            core_api.release_databases()


class TreeContextMenu(object):
    def __init__(self, filename, mainmenu):
        self.cpaste_label_1 = '&Paste items'
        self.cpaste_label_2 = '&Paste as siblings'

        self.cut = wx.MenuItem(wxgui_api.get_tree_context_menu(filename),
                                                mainmenu.ID_CUT, 'Cu&t items')
        self.copy = wx.MenuItem(wxgui_api.get_tree_context_menu(filename),
                                            mainmenu.ID_COPY, '&Copy items')
        self.paste = wx.MenuItem(wxgui_api.get_tree_context_menu(filename),
                                        mainmenu.ID_PASTE, self.cpaste_label_1)
        self.pastesub = wx.MenuItem(wxgui_api.get_tree_context_menu(filename),
                                mainmenu.ID_PASTE_SUB, 'P&aste as children')

        self.cut.SetBitmap(wx.ArtProvider.GetBitmap('@cut', wx.ART_MENU))
        self.copy.SetBitmap(wx.ArtProvider.GetBitmap('@copy', wx.ART_MENU))
        self.paste.SetBitmap(wx.ArtProvider.GetBitmap('@paste', wx.ART_MENU))
        self.pastesub.SetBitmap(wx.ArtProvider.GetBitmap('@paste',
                                                                wx.ART_MENU))

        separator = wx.MenuItem(wxgui_api.get_tree_context_menu(filename),
                                                        kind=wx.ITEM_SEPARATOR)

        # Add in reverse order
        wxgui_api.add_tree_context_menu_item(filename, separator)
        wxgui_api.add_tree_context_menu_item(filename, self.pastesub)
        wxgui_api.add_tree_context_menu_item(filename, self.paste)
        wxgui_api.add_tree_context_menu_item(filename, self.copy)
        wxgui_api.add_tree_context_menu_item(filename, self.cut)

        wxgui_api.bind_to_reset_tree_context_menu(
                                        self._handle_reset_tree_context_menu)
        wxgui_api.bind_to_popup_tree_context_menu(
                                        self._handle_popup_tree_context_menu)

    def _handle_reset_tree_context_menu(self, kwargs):
        self.cut.Enable(False)
        self.copy.Enable(False)
        self.paste.Enable(False)
        self.pastesub.Enable(False)
        self.paste.SetItemLabel(self.cpaste_label_1)

    def _handle_popup_tree_context_menu(self, kwargs):
        filename = kwargs['filename']
        sel = wxgui_api.get_tree_selections(filename)

        if len(sel) == 1:
            self.cut.Enable()
            self.copy.Enable()

            if copypaste_api.has_copied_items(filename):
                self.paste.Enable()
                self.paste.SetItemLabel(self.cpaste_label_2)
                self.pastesub.Enable()

        elif len(sel) > 1:
            self.cut.Enable()
            self.copy.Enable()

        elif copypaste_api.has_copied_items(filename):
            self.paste.Enable()


def main():
    global plugin
    plugin = Main()
