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


class ArtProvider(wx.ArtProvider):
    def __init__(self):
        wx.ArtProvider.__init__(self)

        # Find standard icon names at http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        # Use ids prefixed with '@' so that they're not mistaken as freedesktop
        #  icons
        self.xdg = {'@add-filter': ('list-add', ),
                    '@alarms': ('appointment-soon', 'appointment',
                                'appointment-new', 'stock_new-appointment'),
                    '@alarmoff': ('appointment-missed', 'appointment-soon',
                                  'appointment'),
                    '@apply': ('emblem-ok', 'dialog-apply', 'dialog-ok',
                               'dialog-yes', 'gtk-apply', 'gtk-ok', 'gtk-yes',
                               'stock_yes', 'stock_mark', 'emblem-default'),
                    '@backup': ('document-save-as', 'gtk-save-as',
                                'filesaveas', 'stock_save-as'),
                    '@blinkicon': ('dialog-warning', 'gtk-dialog-warning',
                                   'stock_dialog-warning', 'important'),
                    '@bugreport': ('stock_terminal-reportbug',
                                   'dialog-warning', 'gtk-dialog-warning',
                                   'stock_dialog-warning'),
                    '@close': ('window-close', 'gtk-close', 'stock_close'),
                    '@closeall': ('window-close', 'gtk-close', 'stock_close'),
                    '@compare': ('find' 'edit-find', 'gtk-find', 'filefind',
                                 'stock_search'),
                    '@copy': ('edit-copy', 'editcopy', 'gtk-copy',
                              'stock_copy'),
                    '@cut': ('edit-cut', 'editcut', 'gtk-cut', 'stock_cut'),
                    '@dbsearch': ('search', 'find' 'edit-find', 'gtk-find',
                                  'filefind', 'stock_search'),
                    '@delete': ('edit-delete', 'editdelete', 'gtk-delete',
                                'stock_delete'),
                    '@edit': ('text-editor', 'accessories-text-editor'),
                    '@edit-filter': ('document-properties', ),
                    '@editortab': ('text-x-generic', ),
                    '@exit': ('application-exit', ),
                    '@exporttxt': ('document-export', 'gnome-stock-export',
                                   'document-save-as', 'gtk-save-as',
                                   'filesaveas', 'stock_save-as'),
                    '@exporttype': ('text-x-generic', ),
                    '@filters': ('document-open', ),
                    '@find': ('system-search', 'search', 'find' 'edit-find',
                                    'gtk-find', 'filefind', 'stock_search'),
                    '@focus': ('go-jump', ),
                    '@hide': ('window-close', ),
                    '@languages': ('locale', 'preferences-desktop-locale',
                                   'config-language'),
                    '@left': ('go-previous', ),
                    '@links': ('emblem-symbolic-link', ),
                    '@logs': ('applications-system', ),
                    '@movedown': ('go-down', 'gtk-go-down', 'down',
                                  'stock_down'),
                    '@movetoparent': ('go-previous', 'gtk-go-back-ltr',
                                      'previous', 'stock_left'),
                    '@moveup': ('go-up', 'gtk-go-up', 'up', 'stock_up'),
                    '@navigator': ('applications-system', ),
                    '@next': ('go-next', ),
                    '@newitem': ('document-new', 'gtk-new', 'filenew',
                                 'stock_new-text'),
                    '@newsubitem': ('document-new', 'gtk-new', 'filenew',
                                    'stock_new-text'),
                    '@outspline': ('text-editor', ),
                    '@paste': ('edit-paste', 'editpaste', 'gtk-paste',
                               'stock_paste'),
                    '@preferences': ('package_settings', 'gtk-preferences'),
                    '@previous': ('go-previous', ),
                    '@properties': ('document-properties', ),
                    '@question': ('dialog-question', ),
                    '@redo': ('redo', 'edit-redo', 'gtk-redo-ltr',
                                'stock_redo'),
                    '@redodb': ('redo', 'edit-redo', 'gtk-redo-ltr',
                                'stock_redo'),
                    '@refresh': ('view-refresh', ),
                    '@remove-filter': ('list-remove', ),
                    '@right': ('go-next', ),
                    '@save': ('document-save', 'gtk-save', 'filesave',
                                'stock_save'),
                    '@saveall': ('document-save', 'gtk-save', 'filesave',
                                'stock_save'),
                    '@saveas': ('document-save-as', 'gtk-save-as',
                                'filesaveas', 'stock_save-as'),
                    '@selectall': ('edit-select-all', 'gtk-select-all',
                                   'stock_select-all'),
                    '@tasklist': ('x-office-calendar', ),
                    '@textsearch': ('edit-find-replace',
                                    'gtk-find-and-replace',
                                    'stock_search-and-replace'),
                    '@tips': ('dialog-information', 'info', 'gtk-dialog-info',
                              'stock_dialog-info'),
                    '@toggle': ('go-up', ),
                    '@tray': ('go-bottom', 'gtk-goto-bottom', 'bottom',
                              'stock_bottom'),
                    '@undo': ('undo', 'edit-undo', 'gtk-undo-ltr',
                                'stock_undo'),
                    '@undodb': ('undo', 'edit-undo', 'gtk-undo-ltr',
                                'stock_undo'),
                    '@warning': ('dialog-warning', )}

        fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_CAPTIONTEXT
                                            ).GetAsString(wx.C2S_HTML_SYNTAX)
        header = ["16 16 2 1",
                  ". m {}".format(fg),
                  "m m none"]
        self.xpm = {
                    '@sortdown': header +
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
                        "mmmmmmmmmmmmmmmm"],
                    '@sortup': header +
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
                        "mmmmmmmmmmmmmmmm"],
                    }

    def CreateBitmap(self, artid, client, size):
        try:
            xdgids = self.xdg[artid]
        except KeyError:
            try:
                xpmid = self.xpm[artid]
            except KeyError:
                # The default art provider will take care of the else case
                bmp = wx.ArtProvider.GetBitmap(artid, client, size)
            else:
                bmp = wx.BitmapFromXPMData(xpmid)
        else:
            for xdgid in xdgids:
                bmp = wx.ArtProvider.GetBitmap(xdgid, client, size)

                if bmp.IsOk():
                    break

        return bmp
