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


class ArtProvider(object):
    def __init__(self):
        self._init_system_icons()
        self._init_list_header_icons()

    def _init_system_icons(self):
        # Use ids prefixed with "@" so that they can't conflict with icon theme
        #  names
        # wxWidgets default icon names:
        #  http://wxpython.org/Phoenix/docs/html/ArtProvider.html#phoenix-title-identifying-art-resources
        # Freedesktop.org icon names:
        #  http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        # GTK stock icon names:
        #  https://developer.gnome.org/gtk3/stable/gtk3-Stock-Items.html
        self.strids = {'@apply': (wx.ART_TICK_MARK, 'gtk-apply', 'gtk-ok',
                                'gtk-yes'),
                    '@backup': (wx.ART_FILE_SAVE_AS, 'document-save-as',
                                'gtk-save-as'),
                    '@close': (wx.ART_CLOSE, 'window-close', 'gtk-close'),
                    '@closeall': (wx.ART_CLOSE, 'window-close', 'gtk-close'),
                    '@copy': (wx.ART_COPY, 'edit-copy', 'gtk-copy'),
                    '@cut': (wx.ART_CUT, 'edit-cut', 'gtk-cut'),
                    '@delete': (wx.ART_DELETE, 'edit-delete', 'gtk-delete'),
                    '@edit': ('accessories-text-editor', "gtk-edit"),
                    '@editortab': (wx.ART_NORMAL_FILE, 'text-x-generic',
                                "gtk-file"),
                    '@exit': (wx.ART_QUIT, 'application-exit', "gtk-quit"),
                    '@find': ('system-search', wx.ART_FIND,
                                'edit-find', 'gtk-find'),
                    '@focus': ('go-jump', "gtk-jump-to", wx.ART_GO_DOWN),
                    '@hide': (wx.ART_CLOSE, 'window-close', 'gtk-close'),
                    '@left': (wx.ART_GO_BACK, 'go-previous', "gtk-go-back"),
                    '@logs': ('applications-system', ),
                    '@movedown': (wx.ART_GO_DOWN, 'go-down', 'gtk-go-down'),
                    '@movetoparent': (wx.ART_GO_BACK, 'go-previous',
                                'gtk-go-back'),
                    '@moveup': (wx.ART_GO_UP, 'go-up', 'gtk-go-up'),
                    '@newitem': (wx.ART_NEW, 'document-new', 'gtk-new'),
                    '@newsubitem': (wx.ART_NEW, 'document-new', 'gtk-new'),
                    '@outspline': ('accessories-text-editor', ),
                    '@next': (wx.ART_GO_FORWARD, 'go-next', "gtk-go-forward"),
                    '@paste': (wx.ART_PASTE, 'edit-paste', 'gtk-paste'),
                    '@previous': (wx.ART_GO_BACK, 'go-previous',
                                "gtk-go-back"),
                    '@properties': ('document-properties', "gtk-properties"),
                    '@question': (wx.ART_QUESTION, 'dialog-question',
                                "gtk-dialog-question"),
                    '@redo': (wx.ART_REDO, 'edit-redo', 'gtk-redo'),
                    '@redodb': (wx.ART_REDO, 'edit-redo', 'gtk-redo'),
                    '@refresh': ('view-refresh', "gtk-refresh"),
                    '@right': (wx.ART_GO_FORWARD, 'go-next', "gtk-go-forward"),
                    '@save': (wx.ART_FILE_SAVE, 'document-save', 'gtk-save'),
                    '@saveall': (wx.ART_FILE_SAVE, 'document-save',
                                'gtk-save'),
                    '@saveas': (wx.ART_FILE_SAVE_AS, 'document-save-as',
                                'gtk-save-as'),
                    '@selectall': ('edit-select-all', 'gtk-select-all'),
                    '@toggle': (wx.ART_GO_UP, 'go-up', 'gtk-go-up'),
                    '@undo': (wx.ART_UNDO, 'edit-undo', 'gtk-undo'),
                    '@undodb': (wx.ART_UNDO, 'edit-undo', 'gtk-undo'),
                    '@warning': (wx.ART_WARNING, 'dialog-warning',
                                "gtk-dialog-warning")}

    def _init_list_header_icons(self):
        fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_CAPTIONTEXT
                                            ).GetAsString(wx.C2S_HTML_SYNTAX)
        header = ["16 16 2 1",
                  ". m {}".format(fg),
                  "m m none"]
        # Note that "gtk-sort-ascending" and "gtk-sort-descending" are for
        #  menus, not list headings
        self.listsorticons = (
            wx.BitmapFromXPMData(header +
                        ["mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmm.mmmmmmmm",
                         "mmmmmm...mmmmmmm",
                         "mmmmm.....mmmmmm",
                         "mmmm.......mmmmm",
                         "mmm.........mmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm"]),
            wx.BitmapFromXPMData(header +
                        ["mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmm.........mmmm",
                         "mmmm.......mmmmm",
                         "mmmmm.....mmmmmm",
                         "mmmmmm...mmmmmmm",
                         "mmmmmmm.mmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm",
                         "mmmmmmmmmmmmmmmm"])
        )

    def _create_fallback_bitmap(self, size):
        return wx.EmptyBitmapRGBA(size, size, red=255, green=255, blue=255,
                                                                    alpha=0)

    def _find_bitmap(self, artid, client, size):
        return self._find(artid, client, size, wx.ArtProvider.GetBitmap)

    def _find_icon(self, artid, client, size):
        return self._find(artid, client, size, wx.ArtProvider.GetIcon)

    def _find(self, artid, client, size, action):
        try:
            strids = self.strids[artid]
        except KeyError:
            return action(artid, client, size)
        else:
            for strid in strids:
                bmp = action(strid, client, size)

                if bmp.IsOk:
                    return bmp
            else:
                return action(artid, client, size)


    def _create_icon_bundle(self, artid):
        # wx.ArtProvider would have a GetIconBundle method, but it's not easy
        #  to understand how to use it... if it's actually implemented at
        #  all...
        bundle = wx.IconBundle()

        for client in (wx.ART_TOOLBAR, wx.ART_MENU, wx.ART_BUTTON,
                    wx.ART_FRAME_ICON, wx.ART_CMN_DIALOG, wx.ART_HELP_BROWSER,
                    wx.ART_MESSAGE_BOX, wx.ART_OTHER):

            icon = self._find_icon(artid, client, (-1, -1))

            if icon.IsOk():
                bundle.AddIcon(icon)

        return bundle

    def install_system_icon(self, name, artids):
        # Use names prefixed with "@" so that they can't conflict with icon
        #  theme names
        try:
            self.strids[name]
        except KeyError:
            self.strids[name] = artids
        else:
            # Just crash if there's a conflict, it should happen only in
            #  development
            raise ValueError()

    def get_frame_icon_bundle(self, artid):
        bundle = self._create_icon_bundle(artid)

        if bundle.IsEmpty():
            # Even though a valid bundle wouldn't be required, be safe in
            #  frames
            for size in (16, 24, 32, 48):
                bundle.AddIcon(wx.IconFromBitmap(self._create_fallback_bitmap(
                                                                        size)))

        return bundle

    def get_notebook_icon(self, artid):
        bmp = self._find_bitmap(artid, wx.ART_TOOLBAR, (16, 16))

        if bmp.IsOk():
            return bmp
        else:
            # A valid bitmap must be returned in any case
            return self._create_fallback_bitmap(16)

    def get_log_icon(self, artid):
        bmp = self._find_bitmap(artid, wx.ART_MENU, (16, 16))

        if bmp.IsOk():
            return bmp
        else:
            # A valid bitmap must be returned in any case
            return self._create_fallback_bitmap(16)

    def get_menu_icon(self, artid):
        # A valid bitmap is not required
        return self._find_bitmap(artid, wx.ART_MENU, (-1, -1))

    def get_dialog_icon(self, artid):
        # A valid bitmap is not required
        return self._find_bitmap(artid, wx.ART_CMN_DIALOG, (-1, -1))

    def get_button_icon(self, artid):
        # A valid bitmap is not required
        return self._find_bitmap(artid, wx.ART_BUTTON, (-1, -1))

    def get_about_icon(self, artid):
        bmp = self._find_bitmap(artid, wx.ART_CMN_DIALOG, (48, 48))

        if bmp.IsOk():
            return bmp
        else:
            # Even though a valid bitmap wouldn't be required, be safe in the
            #  about dialog
            return self._create_fallback_bitmap(48)

    def get_tray_icon(self, artid):
        bmp = self._find_icon(artid, wx.ART_OTHER, (-1, -1))

        if bmp.IsOk():
            return bmp
        else:
            # A valid icon must be returned in any case
            return wx.IconFromBitmap(self._create_fallback_bitmap(16))

    def get_list_sort_icons(self):
        return self.listsorticons
