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

import art
import menubar
import notebooks
import msgboxes
import logs


application_loaded_event = Event()
show_main_window_event = Event()
hide_main_window_event = Event()
exit_application_event = Event()


class GUI(wx.App):
    def __init__(self):
        self.config = coreaux_api.get_interface_configuration('wxgui')

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
        self.logs_configuration = logs.LogsConfiguration()

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
        self.config['show_logs'] = 'yes' if \
                                self.logs_configuration.is_shown() else 'no'
        self.config.export_upgrade(coreaux_api.get_user_config_file())

    def handle_uncaught_exception(self, kwargs):
        coreaux_api.bind_to_uncaught_exception(self.handle_uncaught_exception,
                                               False)
        msgboxes.uncaught_exception(kwargs['exc_info']).ShowModal()
        self.root.Destroy()


class MainFrame(wx.Frame):
    def __init__(self):
        self._ROOT_MIN_SIZE = (600, 408)
        self.config = coreaux_api.get_interface_configuration('wxgui')

        confsize = [int(s) for s in self.config['initial_geometry'].split('x')]
        clarea = wx.Display().GetClientArea()
        initsize = [min((confsize[0], clarea.GetWidth())),
                    min((confsize[1], clarea.GetHeight()))]
        wx.Frame.__init__(self, None, title='Outspline', size=initsize)
        self.SetMinSize(self._ROOT_MIN_SIZE)

        if self.config.get_bool('maximized'):
            self.Maximize()

        self.SetIcons(wx.GetApp().get_main_icon_bundle())

        self.menu = menubar.RootMenu()
        self.SetMenuBar(self.menu)

        self.mainpanes = MainPanes(self)

        self.CreateStatusBar()

        self.close_handler = False

        self.Bind(wx.EVT_WINDOW_CREATE, self._handle_creation)
        self.Bind(wx.EVT_MENU_OPEN, self.menu.update_menus)
        self.Bind(wx.EVT_MENU_CLOSE, self.menu.reset_menus)
        self.bind_to_close_event(wx.GetApp().exit_app)

        self.Centre()
        self.Show(True)

    def _handle_creation(self, event):
        self.Unbind(wx.EVT_WINDOW_CREATE, handler=self._handle_creation)
        application_loaded_event.signal()

    def bind_to_close_event(self, handler):
        if self.close_handler:
            self.Unbind(wx.EVT_CLOSE, handler=self.close_handler)

        self.close_handler = handler
        self.Bind(wx.EVT_CLOSE, handler)

    def hide(self):
        self.Show(False)
        hide_main_window_event.signal()

    def show(self):
        show_main_window_event.signal()
        self.Show(True)

    def toggle_shown(self):
        if self.IsShown():
            self.hide()
        else:
            self.show()


class MainPanes(wx.SplitterWindow):
    def __init__(self, parent):
        wx.SplitterWindow.__init__(self, parent, style=wx.SP_LIVE_UPDATE)

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)

        self.parent = parent
        self.nb_left = notebooks.LeftNotebook(self)
        self.nb_right = notebooks.RightNotebook(self)

        self.Initialize(self.nb_left)

        # Hide the notebooks *after* self.Initialize, which would isntead show
        # them again implicitly
        self.nb_left.Show(False)
        self.nb_right.Show(False)

        self.Bind(wx.EVT_SPLITTER_DCLICK, self.veto_dclick)

    def veto_dclick(self, event):
        event.Veto()

    def split_window(self):
        # Make sure the left notebook is shown in any case
        self.nb_left.Show(True)

        if not self.IsSplit() and self.nb_right.GetPageCount() > 0:
            # Make sure the right notebook is shown although
            # self.SplitVertically should do it implicitly
            self.nb_right.Show(True)

            width = self.GetSize().GetWidth()

            self.SplitVertically(self.nb_left, self.nb_right)
            self.SetSashGravity(0.33)
            self.SetSashPosition(width // 3)

    def unsplit_window(self):
        if self.IsSplit():
            self.Unsplit(self.nb_right)
