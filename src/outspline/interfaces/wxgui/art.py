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

import exceptions


class ArtProvider(object):
    def __init__(self):
        self._init_system_icons()
        self._init_bundled_icons()
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
                    '@close': (wx.ART_CLOSE, 'window-close', 'gtk-close'),
                    '@copy': (wx.ART_COPY, 'edit-copy', 'gtk-copy'),
                    '@cut': (wx.ART_CUT, 'edit-cut', 'gtk-cut'),
                    '@delete': (wx.ART_DELETE, 'edit-delete', 'gtk-delete'),
                    '@down': (wx.ART_GO_DOWN, 'go-down', 'gtk-go-down'),
                    '@edit': ("gtk-edit", ),
                    '@exit': (wx.ART_QUIT, 'application-exit', "gtk-quit"),
                    '@file': (wx.ART_NORMAL_FILE, 'text-x-generic',
                                                                "gtk-file"),
                    '@jump': ('go-jump', "gtk-jump-to", wx.ART_GO_DOWN),
                    '@left': (wx.ART_GO_BACK, 'go-previous', "gtk-go-back"),
                    '@new': (wx.ART_NEW, 'document-new', 'gtk-new'),
                    '@paste': (wx.ART_PASTE, 'edit-paste', 'gtk-paste'),
                    '@properties': ('document-properties', "gtk-properties"),
                    '@question': (wx.ART_QUESTION, 'dialog-question',
                                "gtk-dialog-question"),
                    '@redo': (wx.ART_REDO, 'edit-redo', 'gtk-redo'),
                    '@refresh': ('view-refresh', "gtk-refresh"),
                    '@right': (wx.ART_GO_FORWARD, 'go-next', "gtk-go-forward"),
                    '@save': (wx.ART_FILE_SAVE, 'document-save', 'gtk-save'),
                    '@saveas': (wx.ART_FILE_SAVE_AS, 'document-save-as',
                                'gtk-save-as'),
                    '@selectall': ('edit-select-all', 'gtk-select-all'),
                    '@undo': (wx.ART_UNDO, 'edit-undo', 'gtk-undo'),
                    '@up': (wx.ART_GO_UP, 'go-up', 'gtk-go-up'),
                    '@warning': (wx.ART_WARNING, 'dialog-warning',
                                "gtk-dialog-warning")}

    def _init_bundled_icons(self):
        # Use artids prefixed with "@" so that they can't conflict with icon
        #  theme names
        self.bundled = {icon[0]: coreaux_api.get_interface_bundled_data(
            "wxgui", icon[1]) for icon in (
                ("@dbfind", ("Tango", "find16.png")),
                ("@edit", ("Tango", "edit16.png")),
                ("@logs", ("Tango", "logs16.png")),
                ("@outspline", ("main48.png", )),
                ("@outsplinetray", ("main24.png", )),
                ("@properties", ("Tango", "properties16.png")),
                ("@refresh", ("Tango", "refresh16.png")),
                ("@selectall", ("Tango", "selectall16.png")),
                ("@toggle", ("Tango", "toggle16.png")),
            )
        }

        # Use bundleid prefixed with "&" so that they can't conflict with icon
        #  theme names
        self.bundles = {
            "&outspline": (coreaux_api.get_interface_bundled_data(
                "wxgui", (icon, )) for icon in ("main16.png", "main24.png",
                "main32.png", "main48.png", "main64.png", "main128.png", ))
        }

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

    def install_bundled_icon(self, plugin, artid, path):
        # Use artids prefixed with "@" so that they can't conflict with icon
        #  theme names
        abspath = coreaux_api.get_plugin_bundled_data(plugin, path)

        if abspath in self.bundled.values():
            raise exceptions.DuplicatedIconError()
        else:
            try:
                self.bundled[artid]
            except KeyError:
                self.bundled[artid] = abspath
            else:
                # Just crash if there's a conflict, it should happen only in
                #  development
                raise exceptions.DuplicatedArtIdError()

    def install_icon_bundle(self, plugin, bundleid, paths):
        # Use bundleid prefixed with "&" so that they can't conflict with icon
        #  theme names
        try:
            self.bundles[bundleid]
        except KeyError:
            self.bundles[bundleid] = (coreaux_api.get_plugin_bundled_data(
                                            plugin, path) for path in paths)
        else:
            # Just crash if there's a conflict, it should happen only in
            #  development
            raise exceptions.DuplicatedArtIdError()

    def _find_bitmap(self, artid, client, size):
        return self._find(artid, client, size, wx.ArtProvider.GetBitmap,
                                                                    wx.Bitmap)

    def _find_icon(self, artid, client, size):
        return self._find(artid, client, size, wx.ArtProvider.GetIcon, wx.Icon)

    def _find(self, artid, client, size, get_system, get_bundled):
        try:
            strids = self.strids[artid]
        except KeyError:
            # Use strict=True because it shouldn't happen that the @artid isn't
            #  found in the bundled icons either
            # Also, the @artid shouldn't be used to retrieve system icons or
            #  file names directly, in fact bypassing this whole system
            return self._find_bundled(artid, get_bundled, strict=True)
        else:
            for strid in strids:
                bmp = get_system(strid, client, size)

                if bmp.IsOk():
                    return bmp

            else:
                # Use strict=False because the @artid was correctly used, it's
                #  just that the system doesn't have the icon installed
                return self._find_bundled(artid, get_bundled, strict=False)

    def _find_bundled(self, artid, get_bundled, strict):
        try:
            filepath = self.bundled[artid]
        except KeyError:
            if strict:
                raise exceptions.UnknownArtIdError()
            else:
                return False
        else:
            return get_bundled(filepath)

    def get_notebook_icon(self, artid):
        # A valid bitmap must be returned in any case
        return self._find_bitmap(artid, wx.ART_TOOLBAR, (16, 16))

    def get_log_icon(self, artid):
        # A valid bitmap must be returned in any case
        return self._find_bitmap(artid, wx.ART_MENU, (16, 16))

    def get_menu_icon(self, artid):
        # A valid bitmap is not required
        return self._find_bitmap(artid, wx.ART_MENU, (16, 16))

    def get_dialog_icon(self, artid):
        # A valid bitmap is not required
        return self._find_bitmap(artid, wx.ART_CMN_DIALOG, (48, 48))

    def get_message_icon(self, artid):
        # A valid bitmap is not required
        return self._find_bitmap(artid, wx.ART_BUTTON, (16, 16))

    def get_about_icon(self):
        return self.bundled["@outspline"]

    def get_tray_icon(self, artid):
        # Don't try to get an SVG, because the tray icon won't be resized with
        #  the notification area anyway
        return wx.Icon(self.bundled[artid])

    def get_frame_icon_bundle(self, bundleid):
        # wx.ArtProvider would have a GetIconBundle method, but it's not easy
        #  to understand how to use it... if it's actually
        #  implemented/tested/maintained at all...
        bundle = wx.IconBundle()

        for path in self.bundles[bundleid]:
            bundle.AddIcon(wx.Icon(path))

        return bundle

    def get_list_sort_icons(self):
        return self.listsorticons
