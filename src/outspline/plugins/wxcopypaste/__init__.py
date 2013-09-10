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
from outspline.coreaux_api import Event
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api
import outspline.extensions.copypaste_api as copypaste_api

import msgboxes

cut_items_event = Event()

ID_CUT = None
mcut = None
cmcut = None
ID_COPY = None
mcopy = None
cmcopy = None
ID_PASTE = None
mpaste = None
cmpaste = None
ID_PASTE_SUB = None
mpastesub = None
cmpastesub = None


def cut_items(event, no_confirm=False):
    core_api.block_databases()

    treedb = wxgui_api.get_active_database()
    if treedb:
        # select() arguments must be compatible with delete_items()
        selection = treedb.get_selections(none=False, descendants=True)
        if selection:
            filename = treedb.get_filename()

            for item in selection:
                id_ = treedb.get_item_id(item)
                if not wxgui_api.close_editor(filename, id_,
                                      ask='quiet' if no_confirm else 'discard'):
                    core_api.release_databases()
                    return False

            items = []
            for item in selection:
                id_ = treedb.get_item_id(item)
                items.append(id_)

            copypaste_api.cut_items(filename, items, description='Cut {} items'
                                    ''.format(len(items)))

            treedb.remove_items(selection)
            treedb.history.refresh()
            cut_items_event.signal()

    core_api.release_databases()


def copy_items(event):
    core_api.block_databases()

    treedb = wxgui_api.get_active_database()
    if treedb:
        # select() arguments must be compatible with delete_items()
        selection = treedb.get_selections(none=False, descendants=True)
        if selection:
            filename = treedb.get_filename()
            items = []
            for item in selection:
                items.append(treedb.get_item_id(item))
            copypaste_api.copy_items(filename, items)

    core_api.release_databases()


def paste_items_as_siblings(event, no_confirm=False):
    core_api.block_databases()

    treedb = wxgui_api.get_active_database()

    if treedb:
        filename = treedb.get_filename()

        if no_confirm or copypaste_api.can_paste_safely(filename) or \
                        msgboxes.unsafe_paste_confirm().ShowModal() == wx.ID_OK:
            # Do not use none=False in order to allow pasting in an empty
            # database
            selection = treedb.get_selections(many=False)

            if selection:
                base = selection[0]
                baseid = treedb.get_item_id(base)

                roots = copypaste_api.paste_items_as_siblings(filename, baseid,
                                                      description='Paste items')

                for r in roots:
                    treeroot = treedb.insert_item(selection[0], 'after', id_=r)
                    treedb.create(base=treeroot)
            else:
                base = treedb.get_root()
                baseid = treedb.get_item_id(base)

                roots = copypaste_api.paste_items_as_children(filename, baseid,
                                                      description='Paste items')

                for r in roots:
                    treeroot = treedb.insert_item(base, 'append', id_=r)
                    treedb.create(base=treeroot)

            treedb.history.refresh()

    core_api.release_databases()


def paste_items_as_children(event, no_confirm=False):
    core_api.block_databases()

    treedb = wxgui_api.get_active_database()
    if treedb:
        selection = treedb.get_selections(none=False, many=False)
        if selection:
            filename = treedb.get_filename()

            if no_confirm or copypaste_api.can_paste_safely(filename) or \
                        msgboxes.unsafe_paste_confirm().ShowModal() == wx.ID_OK:
                baseid = treedb.get_item_id(selection[0])

                roots = copypaste_api.paste_items_as_children(filename, baseid,
                                                  description='Paste sub-items')

                for r in roots:
                    treeroot = treedb.insert_item(selection[0], 'append', id_=r)
                    treedb.create(base=treeroot)

                treedb.history.refresh()

    core_api.release_databases()


def handle_open_database(kwargs):
    global cmcut, cmcopy, cmpaste, cmpastesub
    filename = kwargs['filename']
    config = coreaux_api.get_plugin_configuration('wxcopypaste')

    cmcut = wxgui_api.insert_tree_context_menu_item(filename,
                                                config.get_int('cmenucut_pos'),
                                                'Cu&t items', id_=ID_CUT,
                                                help='Cut the selected items',
                                                sep=config['cmenucut_sep'],
                                                icon='@cut')
    cmcopy = wxgui_api.insert_tree_context_menu_item(filename,
                                               config.get_int('cmenucopy_pos'),
                                               '&Copy items', id_=ID_COPY,
                                               help='Copy the selected items',
                                               sep=config['cmenucopy_sep'],
                                               icon='@copy')
    cmpaste = wxgui_api.insert_tree_context_menu_item(filename,
                        config.get_int('cmenupaste_pos'),
                        '&Paste siblings',
                        id_=ID_PASTE,
                        help='Paste items as siblings after the selected item',
                        sep=config['cmenupaste_sep'], icon='@paste')
    cmpastesub = wxgui_api.insert_tree_context_menu_item(filename,
                           config.get_int('cmenupastesub_pos'),
                           'P&aste sub-items',
                           id_=ID_PASTE_SUB,
                           help='Paste items as children of the selected item',
                           sep=config['cmenupastesub_sep'], icon='@paste')

    accels = [(wx.ACCEL_CTRL, ord('x'), ID_CUT),
              (wx.ACCEL_CTRL, ord('c'), ID_COPY),
              (wx.ACCEL_CTRL, ord('v'), ID_PASTE),
              (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('v'), ID_PASTE_SUB)]

    wxgui_api.add_database_tree_accelerators(filename, accels)


def handle_reset_menu_items(kwargs):
    if kwargs['menu'] is wxgui_api.get_menu().database:
        mcut.Enable(False)
        mcopy.Enable(False)
        mpaste.Enable(False)
        mpastesub.Enable(False)


def handle_enable_tree_menus(kwargs):
    filename = kwargs['filename']
    sel = wxgui_api.get_tree_selections(filename)

    if len(sel) == 1:
        mcut.Enable()
        mcopy.Enable()
        if copypaste_api.has_copied_items(filename):
            mpaste.Enable()
            mpastesub.Enable()
    elif len(sel) > 1:
        mcut.Enable()
        mcopy.Enable()
    else:
        if copypaste_api.has_copied_items(filename):
            mpaste.Enable()


def handle_reset_tree_context_menu(kwargs):
    cmcut.Enable(False)
    cmcopy.Enable(False)
    cmpaste.Enable(False)
    cmpastesub.Enable(False)


def handle_popup_tree_context_menu(kwargs):
    filename = kwargs['filename']
    sel = wxgui_api.get_tree_selections(filename)

    if len(sel) == 1:
        cmcut.Enable()
        cmcopy.Enable()
        if copypaste_api.has_copied_items(filename):
            cmpaste.Enable()
            cmpastesub.Enable()
    elif len(sel) > 1:
        cmcut.Enable()
        cmcopy.Enable()
    else:
        if copypaste_api.has_copied_items(filename):
            cmpaste.Enable()


def main():
    global ID_CUT, ID_COPY, ID_PASTE, ID_PASTE_SUB
    ID_CUT = wx.NewId()
    ID_COPY = wx.NewId()
    ID_PASTE = wx.NewId()
    ID_PASTE_SUB = wx.NewId()

    global mcut, mcopy, mpaste, mpastesub
    config = coreaux_api.get_plugin_configuration('wxcopypaste')

    mcut = wxgui_api.insert_menu_item('Database',
                                      config.get_int('menucut_pos'),
                                      'Cu&t items', id_=ID_CUT,
                                      help='Cut the selected items',
                                      sep=config['menucut_sep'], icon='@cut')
    mcopy = wxgui_api.insert_menu_item('Database',
                                       config.get_int('menucopy_pos'),
                                       '&Copy items', id_=ID_COPY,
                                       help='Copy the selected items',
                                       sep=config['menucopy_sep'],
                                       icon='@copy')
    mpaste = wxgui_api.insert_menu_item('Database',
                        config.get_int('menupaste_pos'),
                        '&Paste items', id_=ID_PASTE,
                        help='Paste items as siblings after the selected item',
                        sep=config['menupaste_sep'], icon='@paste')
    mpastesub = wxgui_api.insert_menu_item('Database',
                           config.get_int('menupastesub_pos'),
                           'P&aste sub-items', id_=ID_PASTE_SUB,
                           help='Paste items as children of the selected item',
                           sep=config['menupastesub_sep'], icon='@paste')

    wxgui_api.bind_to_menu(cut_items, mcut)
    wxgui_api.bind_to_menu(copy_items, mcopy)
    wxgui_api.bind_to_menu(paste_items_as_siblings, mpaste)
    wxgui_api.bind_to_menu(paste_items_as_children, mpastesub)

    wxgui_api.bind_to_open_database(handle_open_database)

    wxgui_api.bind_to_reset_menu_items(handle_reset_menu_items)
    wxgui_api.bind_to_enable_tree_menus(handle_enable_tree_menus)
    wxgui_api.bind_to_reset_tree_context_menu(handle_reset_tree_context_menu)
    wxgui_api.bind_to_popup_tree_context_menu(handle_popup_tree_context_menu)
