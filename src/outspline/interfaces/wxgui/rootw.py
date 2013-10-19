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

import art
import menubar
import notebooks
import msgboxes
import history

config = coreaux_api.get_interface_configuration('wxgui')

exit_application_event = Event()

_ROOT_MIN_SIZE = (600, 408)


class GUI(wx.App):
    MAIN_ICON_BUNDLE = None
    root = None
    menu = None
    nb_left = None
    nb_right = None

    def __init__(self):
        wx.App.__init__(self, False)

        wx.ArtProvider.Push(art.ArtProvider())

        self.MAIN_ICON_BUNDLE = wx.IconBundle()
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                             wx.ART_TOOLBAR))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                             wx.ART_MENU))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                             wx.ART_BUTTON))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                            wx.ART_FRAME_ICON))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                            wx.ART_CMN_DIALOG))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                          wx.ART_HELP_BROWSER))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                           wx.ART_MESSAGE_BOX))
        self.MAIN_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('text-editor',
                                                             wx.ART_OTHER))

        self.root = MainFrame()

        self.menu = self.root.menu
        self.nb_left = self.root.mainpanes.nb_left
        self.nb_right = self.root.mainpanes.nb_right

        coreaux_api.bind_to_uncaught_exception(self.handle_uncaught_exception)

    def get_main_icon_bundle(self):
        return self.MAIN_ICON_BUNDLE

    def exit_app(self, event):
        self.export_options()

        exit_application_event.signal()

        # close_all_databases() already blocks the databases
        if self.menu.file.close_all_databases(event, exit_=True):
            core_api.exit_()
            coreaux_api.bind_to_uncaught_exception(
                                         self.handle_uncaught_exception, False)
            self.root.Destroy()
        # else: event.Veto() doesn't work here

    def export_options(self):
        config['show_history'] = 'yes' if history.is_shown() else 'no'
        config.export_upgrade(coreaux_api.get_user_config_file())

    def handle_uncaught_exception(self, kwargs):
        coreaux_api.bind_to_uncaught_exception(self.handle_uncaught_exception,
                                               False)
        msgboxes.uncaught_exception(kwargs['exc_info']).ShowModal()
        self.root.Destroy()


class MainFrame(wx.Frame):
    menu = None
    mainpanes = None
    focus = None

    def __init__(self):
        confsize = [int(s) for s in config['initial_geometry'].split('x')]
        clarea = wx.Display().GetClientArea()
        initsize = [min((confsize[0], clarea.GetWidth())),
                    min((confsize[1], clarea.GetHeight()))]
        wx.Frame.__init__(self, None, title='Outspline', size=initsize)
        self.SetMinSize(_ROOT_MIN_SIZE)
        if config.get_bool('maximized'):
            self.Maximize()

        self.SetIcons(wx.GetApp().get_main_icon_bundle())

        self.menu = menubar.RootMenu()
        self.SetMenuBar(self.menu)

        self.mainpanes = MainPanes(self)

        self.CreateStatusBar()

        self.focus = self.FindFocus()

        self.Bind(wx.EVT_MENU_OPEN, self.handle_menu_open)
        self.Bind(wx.EVT_UPDATE_UI, self.handle_update_ui)
        self.Bind(wx.EVT_CLOSE, wx.GetApp().exit_app)

        self.Centre()
        self.Show(True)

    def hide(self, event):
        self.Show(False)

    def show(self, event):
        self.Show(True)

    def toggle_shown(self, event):
        if self.IsShown():
            self.hide(event)
        else:
            self.show(event)

    def handle_menu_open(self, event):
        self.menu.update_menus(event.GetMenu())

    def handle_update_ui(self, event):
        cfocus = self.FindFocus()
        if cfocus != self.focus:
            self.focus = cfocus
            self.menu.set_top_menus()


class MainPanes(wx.SplitterWindow):
    parent = None
    nb_left = None
    nb_right = None

    def __init__(self, parent):
        wx.SplitterWindow.__init__(self, parent, style=wx.SP_LIVE_UPDATE)

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)

        self.parent = parent
        self.nb_left = notebooks.LeftNotebook(self)
        self.nb_right = notebooks.RightNotebook(self)

        self.nb_left.Show(False)
        self.nb_right.Show(False)
        self.Initialize(self.nb_left)

        self.Bind(wx.EVT_SPLITTER_DCLICK, self.veto_dclick)

    def veto_dclick(self, event):
        event.Veto()

    def split_window(self):
        if not self.IsSplit() and self.nb_right.GetPageCount() > 0:
            width = self.GetSizeTuple()[0]

            self.SplitVertically(self.nb_left, self.nb_right)
            self.SetSashGravity(0.33)

            # This is a workaround for http://trac.wxwidgets.org/ticket/9821
            #   sash gravity doesn't work at the first resize after splitting
            self.SendSizeEvent()

            # Sash position must be set after setting sash gravity and sending
            # the size event, in this order, otherwise the following bug
            # happens:
            # * open a database in a non-maximized window
            # * close all databases
            # * maximize the window
            # * open a database -> the sash is positioned incorrectly
            self.SetSashPosition(width // 3)

    def unsplit_window(self):
        if self.IsSplit():
            self.Unsplit(self.nb_right)
