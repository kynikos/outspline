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

ID_CUT = None
mcut = None
ID_COPY = None
mcopy = None
ID_PASTE = None
mpaste = None
mpaste_label_1 = None
mpaste_help_1 = None
mpaste_label_2 = None
mpaste_help_2 = None
ID_PASTE_SUB = None
mpastesub = None
cmenu = {}
cpaste_label_1 = None
cpaste_label_2 = None


def cut_items(event, no_confirm=False):
    if core_api.block_databases():
        filename = wxgui_api.get_selected_database_filename()

        # This method may be launched by the menu accelerator, but no database
        # may be open
        if filename:
            # select() arguments must be compatible with delete_items()
            selection = wxgui_api.get_tree_selections(filename, none=False,
                                                            descendants=True)

            if selection:
                for item in selection:
                    id_ = wxgui_api.get_tree_item_id(filename, item)

                    if not wxgui_api.close_editor(filename, id_,
                                    ask='quiet' if no_confirm else 'discard'):
                        core_api.release_databases()
                        return False

                items = []

                for item in selection:
                    id_ = wxgui_api.get_tree_item_id(filename, item)
                    items.append(id_)

                copypaste_api.cut_items(filename, items,
                                description='Cut {} items'.format(len(items)))

                wxgui_api.remove_tree_items(filename, selection)
                wxgui_api.refresh_history(filename)
                cut_items_event.signal()

        core_api.release_databases()


def copy_items(event):
    if core_api.block_databases():
        filename = wxgui_api.get_selected_database_filename()

        # This method may be launched by the menu accelerator, but not database
        # may be open
        if filename:
            # select() arguments must be compatible with delete_items()
            selection = wxgui_api.get_tree_selections(filename, none=False,
                                                            descendants=True)

            if selection:
                items = []

                for item in selection:
                    items.append(wxgui_api.get_tree_item_id(filename, item))

                copypaste_api.copy_items(filename, items)

        core_api.release_databases()


def paste_items_as_siblings(event, no_confirm=False):
    if core_api.block_databases():
        filename = wxgui_api.get_selected_database_filename()

        # This method may be launched by the menu accelerator, but not database
        # may be open
        if filename and \
                    (no_confirm or copypaste_api.can_paste_safely(filename) or
                    msgboxes.unsafe_paste_confirm().ShowModal() == wx.ID_OK):
            # Do not use none=False in order to allow pasting in an empty
            # database
            selection = wxgui_api.get_tree_selections(filename, many=False)

            # If multiple items are selected, selection will be False
            if selection is not False:
                if len(selection) > 0:
                    base = selection[0]
                    baseid = wxgui_api.get_tree_item_id(filename, base)

                    roots, ids = copypaste_api.paste_items_as_siblings(
                                filename, baseid, description='Paste items')

                    for r in roots:
                        treeroot = wxgui_api.insert_tree_item_after(filename,
                                                            selection[0], r)
                        wxgui_api.create_tree(filename, treeroot)
                else:
                    base = wxgui_api.get_root_tree_item(filename)
                    baseid = wxgui_api.get_tree_item_id(filename, base)

                    roots, ids = copypaste_api.paste_items_as_children(
                                    filename, baseid, description='Paste items')

                    for r in roots:
                        treeroot = wxgui_api.append_tree_item(filename, base,
                                                                            r)
                        wxgui_api.create_tree(filename, treeroot)

                wxgui_api.refresh_history(filename)

                items_pasted_event.signal(filename=filename, roots=roots,
                                                                    ids=ids)

        core_api.release_databases()


def paste_items_as_children(event, no_confirm=False):
    if core_api.block_databases():
        filename = wxgui_api.get_selected_database_filename()

        # This method may be launched by the menu accelerator, but not database
        # may be open
        if filename:
            selection = wxgui_api.get_tree_selections(filename, none=False,
                                                                    many=False)

            if selection and (no_confirm or
                                    copypaste_api.can_paste_safely(filename) or
                                    msgboxes.unsafe_paste_confirm().ShowModal(
                                    ) == wx.ID_OK):
                baseid = wxgui_api.get_tree_item_id(filename, selection[0])

                roots, ids = copypaste_api.paste_items_as_children(filename,
                                        baseid, description='Paste sub-items')

                for r in roots:
                    treeroot = wxgui_api.append_tree_item(filename,
                                                            selection[0], r)
                    wxgui_api.create_tree(filename, treeroot)

                wxgui_api.refresh_history(filename)

                items_pasted_event.signal(filename=filename, roots=roots,
                                                                    ids=ids)

        core_api.release_databases()


def handle_open_database(kwargs):
    filename = kwargs['filename']

    global cmenu, cpaste_label_1, cpaste_label_2
    cpaste_label_1 = '&Paste items'
    cpaste_label_2 = '&Paste as siblings'

    cmenu[filename] = {}

    cmenu[filename]['cut'] = wx.MenuItem(
                                    wxgui_api.get_tree_context_menu(filename),
                                    ID_CUT, 'Cu&t items')
    cmenu[filename]['copy'] = wx.MenuItem(
                                    wxgui_api.get_tree_context_menu(filename),
                                    ID_COPY, '&Copy items')
    cmenu[filename]['paste'] = wx.MenuItem(
                                    wxgui_api.get_tree_context_menu(filename),
                                    ID_PASTE, cpaste_label_1)
    cmenu[filename]['pastesub'] = wx.MenuItem(
                                    wxgui_api.get_tree_context_menu(filename),
                                    ID_PASTE_SUB, 'P&aste as children')

    cmenu[filename]['cut'].SetBitmap(wx.ArtProvider.GetBitmap('@cut',
                                                                wx.ART_MENU))
    cmenu[filename]['copy'].SetBitmap(wx.ArtProvider.GetBitmap('@copy',
                                                                wx.ART_MENU))
    cmenu[filename]['paste'].SetBitmap(wx.ArtProvider.GetBitmap('@paste',
                                                                wx.ART_MENU))
    cmenu[filename]['pastesub'].SetBitmap(wx.ArtProvider.GetBitmap('@paste',
                                                                wx.ART_MENU))

    separator = wx.MenuItem(wxgui_api.get_tree_context_menu(filename),
                                                        kind=wx.ITEM_SEPARATOR)

    # Add in reverse order
    wxgui_api.add_tree_context_menu_item(filename, separator)
    wxgui_api.add_tree_context_menu_item(filename, cmenu[filename]['pastesub'])
    wxgui_api.add_tree_context_menu_item(filename, cmenu[filename]['paste'])
    wxgui_api.add_tree_context_menu_item(filename, cmenu[filename]['copy'])
    wxgui_api.add_tree_context_menu_item(filename, cmenu[filename]['cut'])


def handle_close_database(kwargs):
    del cmenu[kwargs['filename']]


def handle_reset_menu_items(kwargs):
    # Re-enable all the actions so they are available for their accelerators
    mcut.Enable()
    mcopy.Enable()
    mpaste.Enable()
    mpastesub.Enable()


def handle_enable_tree_menus(kwargs):
    filename = kwargs['filename']

    mcut.Enable(False)
    mcopy.Enable(False)
    mpaste.Enable(False)
    mpastesub.Enable(False)
    mpaste.SetItemLabel(mpaste_label_1)
    mpaste.SetHelp(mpaste_help_1)

    # filename is None is no database is open
    if filename:
        sel = wxgui_api.get_tree_selections(filename)

        if len(sel) == 1:
            mcut.Enable()
            mcopy.Enable()
            if copypaste_api.has_copied_items(filename):
                mpaste.Enable()
                mpaste.SetItemLabel(mpaste_label_2)
                mpaste.SetHelp(mpaste_help_2)
                mpastesub.Enable()
        elif len(sel) > 1:
            mcut.Enable()
            mcopy.Enable()
        elif copypaste_api.has_copied_items(filename):
            mpaste.Enable()


def handle_reset_tree_context_menu(kwargs):
    cms = cmenu[kwargs['filename']]
    cms['cut'].Enable(False)
    cms['copy'].Enable(False)
    cms['paste'].Enable(False)
    cms['pastesub'].Enable(False)
    cms['paste'].SetItemLabel(cpaste_label_1)


def handle_popup_tree_context_menu(kwargs):
    filename = kwargs['filename']
    cms = cmenu[filename]
    sel = wxgui_api.get_tree_selections(filename)

    if len(sel) == 1:
        cms['cut'].Enable()
        cms['copy'].Enable()
        if copypaste_api.has_copied_items(filename):
            cms['paste'].Enable()
            cms['paste'].SetItemLabel(cpaste_label_2)
            cms['pastesub'].Enable()
    elif len(sel) > 1:
        cms['cut'].Enable()
        cms['copy'].Enable()
    elif copypaste_api.has_copied_items(filename):
        cms['paste'].Enable()


def main():
    global ID_CUT, ID_COPY, ID_PASTE, ID_PASTE_SUB
    ID_CUT = wx.NewId()
    ID_COPY = wx.NewId()
    ID_PASTE = wx.NewId()
    ID_PASTE_SUB = wx.NewId()

    config = coreaux_api.get_plugin_configuration('wxcopypaste')('Shortcuts')

    global mpaste_label_1, mpaste_help_1, mpaste_label_2, mpaste_help_2
    mpaste_label_1 = '&Paste items\t{}'.format(config['paste'])
    mpaste_help_1 = 'Paste items as root items'
    mpaste_label_2 = '&Paste as siblings\t{}'.format(config['paste'])
    mpaste_help_2 = 'Paste items as siblings below the selected item'

    global mcut, mcopy, mpaste, mpastesub

    mcut = wx.MenuItem(wxgui_api.get_menu_database(), ID_CUT,
                                        'Cu&t items\t{}'.format(config['cut']),
                                        'Cut the selected items')
    mcopy = wx.MenuItem(wxgui_api.get_menu_database(), ID_COPY,
                                    '&Copy items\t{}'.format(config['copy']),
                                    'Copy the selected items')
    mpaste = wx.MenuItem(wxgui_api.get_menu_database(), ID_PASTE,
                                                mpaste_label_1, mpaste_help_1)
    mpastesub = wx.MenuItem(wxgui_api.get_menu_database(), ID_PASTE_SUB,
                    'P&aste as children\t{}'.format(config['paste_children']),
                    'Paste items as children of the selected item')

    mcut.SetBitmap(wx.ArtProvider.GetBitmap('@cut', wx.ART_MENU))
    mcopy.SetBitmap(wx.ArtProvider.GetBitmap('@copy', wx.ART_MENU))
    mpaste.SetBitmap(wx.ArtProvider.GetBitmap('@paste', wx.ART_MENU))
    mpastesub.SetBitmap(wx.ArtProvider.GetBitmap('@paste', wx.ART_MENU))

    separator = wx.MenuItem(wxgui_api.get_menu_database(),
                                                        kind=wx.ITEM_SEPARATOR)

    # Add in reverse order
    wxgui_api.add_menu_database_item(separator)
    wxgui_api.add_menu_database_item(mpastesub)
    wxgui_api.add_menu_database_item(mpaste)
    wxgui_api.add_menu_database_item(mcopy)
    wxgui_api.add_menu_database_item(mcut)

    wxgui_api.bind_to_menu(cut_items, mcut)
    wxgui_api.bind_to_menu(copy_items, mcopy)
    wxgui_api.bind_to_menu(paste_items_as_siblings, mpaste)
    wxgui_api.bind_to_menu(paste_items_as_children, mpastesub)

    wxgui_api.bind_to_open_database(handle_open_database)
    wxgui_api.bind_to_close_database(handle_close_database)

    wxgui_api.bind_to_reset_menu_items(handle_reset_menu_items)
    wxgui_api.bind_to_menu_database_update(handle_enable_tree_menus)
    wxgui_api.bind_to_reset_tree_context_menu(handle_reset_tree_context_menu)
    wxgui_api.bind_to_popup_tree_context_menu(handle_popup_tree_context_menu)
