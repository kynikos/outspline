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

import threading
import wx
import wx.lib.newevent

import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import Event
import outspline.core_api as core_api

import art
import menubar
import notebooks
import databases
import msgboxes
import logs
import sessions

application_loaded_event = Event()
show_main_window_event = Event()
hide_main_window_event = Event()


class GUI(wx.App):
    def __init__(self):
        self.config = coreaux_api.get_interface_configuration('wxgui')

        wx.App.__init__(self, False)

        self.artprovider = art.ArtProvider()

        self.root = MainFrame()
        self.logs_configuration = logs.LogsConfiguration()

        self.menu = self.root.menu
        self.nb_left = self.root.mainpanes.nb_left
        self.nb_right = self.root.mainpanes.nb_right

        self.uncaught_max = self.config.get_int('max_exceptions')
        self.uncaught_counter = 0
        self.uncaught_event = threading.Event()

        core_api.bind_to_blocked_databases(self._handle_blocked_databases)

        if self.uncaught_max > 0:
            coreaux_api.bind_to_uncaught_exception(
                                            self._handle_uncaught_exception)

        # Window managers like i3 and awesome need MainFrame to be shown here,
        # not at the end of its constructor, or EVT_WINDOW_CREATE will be sent
        # too early (bug #366)
        self.root.Centre()
        self.root.Show(True)

    def exit_app(self, event):
        self._export_options()

        # Refresh the session also when exiting, in order to save the order of
        # visualization of the tabs
        # Do it *before* closing the databases
        self.root.sessionmanager.refresh_session()

        # close_all_databases() already blocks the databases
        if self.menu.file.close_all_databases(event, exit_=True):
            core_api.exit_()
            coreaux_api.bind_to_uncaught_exception(
                                        self._handle_uncaught_exception, False)
            self.root.Destroy()
        # else: event.Veto() doesn't work here

    def _export_options(self):
        self.config['show_logs'] = 'yes' if \
                                self.logs_configuration.is_shown() else 'no'

        if self.config.get_bool('remember_geometry'):
            self.root.save_geometry()

        self.config.export_upgrade(coreaux_api.get_user_config_file())

    def _handle_blocked_databases(self, kwargs):
        msgboxes.blocked_databases().ShowModal()

    def _handle_uncaught_exception(self, kwargs):
        if self.uncaught_counter < self.uncaught_max:
            # Increment in this thread, otherwise uncaught_event won't work
            self.uncaught_counter += 1

            if coreaux_api.is_main_thread():
                self._show_uncaught_dialog(kwargs)
            else:
                wx.CallAfter(self._show_uncaught_dialog, kwargs)

        self.uncaught_event.wait()

    def _show_uncaught_dialog(self, kwargs):
        msgboxes.uncaught_exception(kwargs['exc_info']).ShowModal()

        if self.uncaught_counter == 1:
            # Only unbind here, otherwise another thread that crashes would
            # bypass this whole mechanism
            coreaux_api.bind_to_uncaught_exception(
                                        self._handle_uncaught_exception, False)
            self.root.Destroy()
            # No need to set self.uncaught_counter = 0
            self.uncaught_event.set()
            # No need to call self.uncaught_event.clear()
        else:
            self.uncaught_counter -= 1


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

        self.SetIcons(wx.GetApp().artprovider.get_frame_icon_bundle(
                                                                "&outspline"))

        self.menu = menubar.RootMenu(self)
        self.SetMenuBar(self.menu)

        self._init_accelerators()

        self.mainpanes = MainPanes(self, self.menu)

        self.close_handler = False

        self.Bind(wx.EVT_WINDOW_CREATE, self._handle_creation)
        self.bind_to_close_event(wx.GetApp().exit_app)
        coreaux_api.bind_to_external_nudge(self._handle_external_nudge)

        # Window managers like i3 and awesome need MainFrame to be shown after
        # the instantiation of this class, or EVT_WINDOW_CREATE will be sent
        # too early (bug #366)
        #self.Centre()
        #self.Show(True)

    def _init_accelerators(self):
        aconfig = self.config("ContextualShortcuts")
        self.accmanager = AcceleratorsManagers()
        altmovkeys = AlternativeMovementKeys()
        self.accmanager.create_manager(self, {
            aconfig["up"]: altmovkeys.simulate_up,
            aconfig["down"]: altmovkeys.simulate_down,
            aconfig["left"]: altmovkeys.simulate_left,
            aconfig["right"]: altmovkeys.simulate_right,
            "Shift+{}".format(aconfig["up"]): altmovkeys.simulate_shift_up,
            "Shift+{}".format(aconfig["down"]): altmovkeys.simulate_shift_down,
            "Shift+{}".format(aconfig["left"]): altmovkeys.simulate_shift_left,
            "Shift+{}".format(aconfig["right"]):
                                            altmovkeys.simulate_shift_right,
            "Ctrl+{}".format(aconfig["up"]): altmovkeys.simulate_ctrl_up,
            "Ctrl+{}".format(aconfig["down"]): altmovkeys.simulate_ctrl_down,
            "Ctrl+{}".format(aconfig["left"]): altmovkeys.simulate_ctrl_left,
            "Ctrl+{}".format(aconfig["right"]): altmovkeys.simulate_ctrl_right,
            "Ctrl+Shift+{}".format(aconfig["up"]):
                                            altmovkeys.simulate_ctrl_shift_up,
            "Ctrl+Shift+{}".format(aconfig["down"]):
                                        altmovkeys.simulate_ctrl_shift_down,
            "Ctrl+Shift+{}".format(aconfig["left"]):
                                        altmovkeys.simulate_ctrl_shift_left,
            "Ctrl+Shift+{}".format(aconfig["right"]):
                                        altmovkeys.simulate_ctrl_shift_right,
            aconfig["focus_database"]:
                                    self.menu.view.databases_submenu.ID_FOCUS,
            aconfig["focus_rightnb"]: self.menu.view.rightnb_submenu.ID_FOCUS,
            aconfig["focus_logs"]: self.menu.view.logs_submenu.ID_FOCUS,
        })

    def _handle_creation(self, event):
        self.Unbind(wx.EVT_WINDOW_CREATE, handler=self._handle_creation)

        self.menu.post_init()

        databases.dbpropmanager.post_init()

        if self.config.get_bool('remember_session'):
            self.sessionmanager = sessions.SessionManager()

        application_loaded_event.signal()

    def _handle_external_nudge(self, kwargs):
        self.show()

    def bind_to_close_event(self, handler):
        if self.close_handler:
            self.Unbind(wx.EVT_CLOSE, handler=self.close_handler)

        self.close_handler = handler
        self.Bind(wx.EVT_CLOSE, handler)

    def show(self):
        # Don't execute self._show if it's already shown, otherwise all the
        # handlers of show_main_window_event will be executed for no reason
        if not self.IsShown():
            self._show()

    def hide(self):
        # Don't execute self._hide if it's already hidden, otherwise all the
        # handlers of hide_main_window_event will be executed for no reason
        if self.IsShown():
            self._hide()

    def _show(self):
        show_main_window_event.signal()
        self.Show(True)

    def _hide(self):
        self.Show(False)
        hide_main_window_event.signal()

    def toggle_shown(self):
        if self.IsShown():
            self._hide()
        else:
            self._show()

    def save_geometry(self):
        if self.IsMaximized():
            self.config['maximized'] = 'yes'
        else:
            self.config['initial_geometry'] = 'x'.join([str(s) for s in
                                                            self.GetSize()])
            self.config['maximized'] = 'no'

        self.mainpanes.save_sash_position()


class MainPanes(wx.SplitterWindow):
    def __init__(self, parent, menu):
        wx.SplitterWindow.__init__(self, parent, style=wx.SP_LIVE_UPDATE)

        self.config = coreaux_api.get_interface_configuration('wxgui')
        self.sash_position = self.config.get_float("tree_sash_position")
        self.sash_gravity = 1.0 / self.sash_position if \
                        self.config.get_bool("tree_auto_sash_gravity") else 0

        # Prevent the window from unsplitting when dragging the sash to the
        # border
        self.SetMinimumPaneSize(20)

        self.parent = parent
        self.nb_left = notebooks.LeftNotebook(self, parent, menu)
        self.nb_right = notebooks.RightNotebook(self, parent, menu)

        self.Initialize(self.nb_left)

        # Hide the notebooks *after* self.Initialize, which would instead show
        # them again implicitly
        self.nb_left.Show(False)
        self.nb_right.Show(False)

        self.Bind(wx.EVT_SPLITTER_DCLICK, self._veto_dclick)

    def _veto_dclick(self, event):
        event.Veto()

    def split_window(self):
        # Make sure the left notebook is shown in any case
        self.nb_left.Show(True)

        if not self.IsSplit() and self.nb_right.get_real_page_count() > 0:
            # Make sure the right notebook is shown although
            # self.SplitVertically should do it implicitly
            self.nb_right.Show(True)

            self.SplitVertically(self.nb_left, self.nb_right)

            width = self.GetSize().GetWidth()
            self.SetSashGravity(self.sash_gravity)
            self.SetSashPosition(width // self.sash_position)

    def unsplit_window(self):
        if self.IsSplit():
            width = self.GetSize().GetWidth()
            # Make sure that a float is returned
            self.sash_position = float(width) / self.GetSashPosition()
            self.Unsplit(self.nb_right)

        # Explicitly reset the focus, which in some cases would be lost
        self.parent.SetFocus()

    def save_sash_position(self):
        if self.IsSplit():
            width = self.GetSize().GetWidth()
            # Make sure that a float is returned
            self.sash_position = float(width) / self.GetSashPosition()

        self.config["tree_sash_position"] = str(self.sash_position)


class AcceleratorsManagers(object):
    def __init__(self):
        # This object shouldn't store any references to windows or tables,
        # otherwise it will prevent them from being garbage-collected when
        # destroyed
        config = coreaux_api.get_interface_configuration('wxgui')

        if config.get_bool('contextual_shortcuts'):
            self.generate_table = self._generate_table
            self.accelclass = _WindowAccelerators
        else:
            self.generate_table = self._noop
            self.accelclass = _WindowAcceleratorsNoOp

        self.EnableAcceleratorsEvent, self.EVT_ENABLE_ACCELERATORS = \
                                            wx.lib.newevent.NewCommandEvent()
        self.DisableAcceleratorsEvent, self.EVT_DISABLE_ACCELERATORS = \
                                            wx.lib.newevent.NewCommandEvent()

    def generate_table(self, window, accelsconf):
        # This method is defined dynamically
        pass

    def create_manager(self, window, accelsconf):
        table = self.generate_table(window, accelsconf)
        return self.accelclass(self, window, table)

    def register_text_ctrl(self, window):
        window.Bind(wx.EVT_SET_FOCUS, self._disable_accelerators)
        window.Bind(wx.EVT_KILL_FOCUS, self._enable_accelerators)

    def _noop(self, *args, **kwargs):
        pass

    def _generate_table(self, window, accelsconf):
        accels = []

        for accstr in accelsconf:
            # An empty string should disable the accelerator
            if accstr:
                action = accelsconf[accstr]

                # action can be either a real ID (integer) or a function
                if isinstance(action, int):
                    id_ = action
                else:
                    id_ = wx.NewId()
                    window.Bind(wx.EVT_BUTTON, action, id=id_)

                accel = wx.AcceleratorEntry(0, 0, id_)
                accel.FromString(accstr)
                accels.append(accel)

        return wx.AcceleratorTable(accels)

    def _enable_accelerators(self, event):
        window = event.GetEventObject()
        enable_accelerators_event = self.EnableAcceleratorsEvent(
                                                                window.GetId())
        wx.PostEvent(window, enable_accelerators_event)

    def _disable_accelerators(self, event):
        window = event.GetEventObject()
        disable_accelerators_event = self.DisableAcceleratorsEvent(
                                                                window.GetId())
        wx.PostEvent(window, disable_accelerators_event)


class _WindowAcceleratorsNoOp(object):
    def __init__(self, *args, **kwargs):
        pass

    def set_table(self, *args, **kwargs):
        pass


class _WindowAccelerators(object):
    def __init__(self, mainmanager, window, table):
        self.mainmanager = mainmanager
        self.window = window
        self.table = table
        self.tablenoop = wx.AcceleratorTable([])

        self._enable()

        self.window.Bind(self.mainmanager.EVT_ENABLE_ACCELERATORS,
                                            self._handle_enable_accelerators)
        self.window.Bind(self.mainmanager.EVT_DISABLE_ACCELERATORS,
                                            self._handle_disable_accelerators)

    def set_table(self, table):
        self.table = table
        self._enable()

    def _enable(self):
        self.window.SetAcceleratorTable(self.table)

    def _handle_enable_accelerators(self, event):
        self._enable()
        event.Skip()

    def _handle_disable_accelerators(self, event):
        self.window.SetAcceleratorTable(self.tablenoop)
        event.Skip()


class AlternativeMovementKeys(object):
    def __init__(self):
        self.uisim = wx.UIActionSimulator()

    def simulate_up(self, event):
        self.uisim.Char(wx.WXK_UP)
        event.Skip()

    def simulate_down(self, event):
        self.uisim.Char(wx.WXK_DOWN)
        event.Skip()

    def simulate_left(self, event):
        self.uisim.Char(wx.WXK_LEFT)
        event.Skip()

    def simulate_right(self, event):
        self.uisim.Char(wx.WXK_RIGHT)
        event.Skip()

    def simulate_shift_up(self, event):
        self.uisim.Char(wx.WXK_UP, modifiers=wx.MOD_SHIFT)
        event.Skip()

    def simulate_shift_down(self, event):
        self.uisim.Char(wx.WXK_DOWN, modifiers=wx.MOD_SHIFT)
        event.Skip()

    def simulate_shift_left(self, event):
        self.uisim.Char(wx.WXK_LEFT, modifiers=wx.MOD_SHIFT)
        event.Skip()

    def simulate_shift_right(self, event):
        self.uisim.Char(wx.WXK_RIGHT, modifiers=wx.MOD_SHIFT)
        event.Skip()

    def simulate_ctrl_up(self, event):
        self.uisim.Char(wx.WXK_UP, modifiers=wx.MOD_CONTROL)
        event.Skip()

    def simulate_ctrl_down(self, event):
        self.uisim.Char(wx.WXK_DOWN, modifiers=wx.MOD_CONTROL)
        event.Skip()

    def simulate_ctrl_left(self, event):
        self.uisim.Char(wx.WXK_LEFT, modifiers=wx.MOD_CONTROL)
        event.Skip()

    def simulate_ctrl_right(self, event):
        self.uisim.Char(wx.WXK_RIGHT, modifiers=wx.MOD_CONTROL)
        event.Skip()

    def simulate_ctrl_shift_up(self, event):
        self.uisim.Char(wx.WXK_UP, modifiers=wx.MOD_CONTROL | wx.MOD_SHIFT)
        event.Skip()

    def simulate_ctrl_shift_down(self, event):
        self.uisim.Char(wx.WXK_DOWN, modifiers=wx.MOD_CONTROL | wx.MOD_SHIFT)
        event.Skip()

    def simulate_ctrl_shift_left(self, event):
        self.uisim.Char(wx.WXK_LEFT, modifiers=wx.MOD_CONTROL | wx.MOD_SHIFT)
        event.Skip()

    def simulate_ctrl_shift_right(self, event):
        self.uisim.Char(wx.WXK_RIGHT, modifiers=wx.MOD_CONTROL | wx.MOD_SHIFT)
        event.Skip()
