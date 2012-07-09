# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import wx


class ArtProvider(wx.ArtProvider):
    gtk = None
    bundled = None
    
    def __init__(self):
        wx.ArtProvider.__init__(self)
        
        # Use ids prefixed with '@' so that they're not mistaken as GTK icons
        self.gtk = {'@alarms': ('appointment-soon', 'appointment',
                                'appointment-new', 'stock_new-appointment'),
                    '@apply': ('emblem-ok', 'dialog-apply', 'dialog-ok',
                               'dialog-yes', 'gtk-apply', 'gtk-ok', 'gtk-yes',
                               'stock_yes', 'stock_mark', 'emblem-default'),
                    '@backup': ('document-save-as', 'gtk-save-as',
                                'filesaveas', 'stock_save-as'),
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
                    '@exporttxt': ('document-export', 'gnome-stock-export',
                                   'document-save-as', 'gtk-save-as',
                                   'filesaveas', 'stock_save-as'),
                    '@languages': ('locale', 'preferences-desktop-locale',
                                   'config-language'),
                    '@movedown': ('go-down', 'gtk-go-down', 'down',
                                  'stock_down'),
                    '@movetoparent': ('go-previous', 'gtk-go-back-ltr',
                                      'previous', 'stock_left'),
                    '@moveup': ('go-up', 'gtk-go-up', 'up', 'stock_up'),
                    '@newitem': ('document-new', 'gtk-new', 'filenew',
                                 'stock_new-text'),
                    '@newsubitem': ('document-new', 'gtk-new', 'filenew',
                                    'stock_new-text'),
                    '@paste': ('edit-paste', 'editpaste', 'gtk-paste',
                               'stock_paste'),
                    '@preferences': ('package_settings', 'gtk-preferences'),
                    '@save': ('document-save', 'gtk-save', 'filesave',
                                'stock_save'),
                    '@saveall': ('document-save', 'gtk-save', 'filesave',
                                'stock_save'),
                    '@selectall': ('edit-select-all', 'gtk-select-all',
                                   'stock_select-all'),
                    '@redo': ('redo', 'edit-redo', 'gtk-redo-ltr',
                                'stock_redo'),
                    '@redodb': ('redo', 'edit-redo', 'gtk-redo-ltr',
                                'stock_redo'),
                    '@saveas': ('document-save-as', 'gtk-save-as',
                                'filesaveas', 'stock_save-as'),
                    '@textsearch': ('edit-find-replace',
                                    'gtk-find-and-replace',
                                    'stock_search-and-replace'),
                    '@tips': ('dialog-information', 'info', 'gtk-dialog-info',
                              'stock_dialog-info'),
                    '@tray': ('go-bottom', 'gtk-goto-bottom', 'bottom',
                              'stock_bottom'),
                    '@undo': ('undo', 'edit-undo', 'gtk-undo-ltr',
                                'stock_undo'),
                    '@undodb': ('undo', 'edit-undo', 'gtk-undo-ltr',
                                'stock_undo')}

        # Bundled images (currently empty)
        self.bundled = {}
    
    def CreateBitmap(self, artid, client, size):
        if artid in self.gtk:
            for gtkid in self.gtk[artid]:
                bmp = wx.ArtProvider.GetBitmap(gtkid, client, size)
                if bmp.IsOk():
                    break
        # The default art provider will take care of the else case
        else:
            bmp = wx.ArtProvider.GetBitmap(artid, client, size)
        
        return bmp