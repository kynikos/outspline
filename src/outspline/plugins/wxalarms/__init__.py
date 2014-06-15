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

import os as _os
import time as _time
import wx

from outspline.static.wxclasses.misc import NarrowSpinCtrl

from outspline.coreaux_api import log
import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api
wxtrayicon_api = coreaux_api.import_optional_plugin_api('wxtrayicon')

alarmswindow = None


class AlarmsWindow(object):
    def __init__(self, parent):
        self.ALARMS_MIN_HEIGHT = 140
        self.ALARMS_ICON_BUNDLE = wx.IconBundle()
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_TOOLBAR))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_MENU))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_BUTTON))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_FRAME_ICON))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_CMN_DIALOG))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_HELP_BROWSER))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_MESSAGE_BOX))
        self.ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                        wx.ART_OTHER))

        self.config = coreaux_api.get_plugin_configuration('wxalarms')

        self.window = wx.Frame(parent, size=[int(s)
                          for s in self.config['initial_geometry'].split('x')])

        self.window.SetIcons(self.ALARMS_ICON_BUNDLE)

        self.alarms = {}
        self._update_title()

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.window.SetSizer(self.box)

        self.panel = wx.ScrolledWindow(self.window, style=wx.BORDER_THEME)
        self.panel.SetScrollRate(20, 20)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)
        self.box.Add(self.panel, proportion=1, flag=wx.EXPAND | wx.ALL,
                                                                    border=4)

        self.bottom = wx.BoxSizer(wx.HORIZONTAL)
        self._init_bottom()
        self.box.Add(self.bottom, flag=wx.LEFT | wx.RIGHT | wx.EXPAND,
                                                                    border=4)

        # Set the minimum width so that the bottom controls can fit, and also
        # add 20 px for the stretch spacer
        minwidth = self.bottom.ComputeFittingWindowSize(self.window).GetWidth()
        self.window.SetMinSize((minwidth + 20, self.ALARMS_MIN_HEIGHT))

        self.DELAY = 50
        # Set CDELAY shorter than DELAY, so that if an alarm is activated at
        # the same time an alarm is dismissed, there's a better chance that
        # the alarm window requests the user attention
        self.CDELAY = 30

        # Initialize self.timer and self.stimer with a dummy function (int)
        self.timer = wx.CallLater(1, int)
        self.stimer = wx.CallLater(1, int)

        self.LIMIT = self.config.get_int('limit')

        self.mainmenu = MainMenu(self)
        TrayMenu(self)

        self.window.Bind(wx.EVT_CLOSE, self._handle_close)

        organism_alarms_api.bind_to_alarm(self._handle_alarm)
        organism_alarms_api.bind_to_alarm_off(self._handle_alarm_off)
        wxgui_api.bind_to_close_database(self._handle_close_db)

    def _init_bottom(self):
        button_s = wx.Button(self.window, label='Snooze all')
        self.bottom.Add(button_s, flag=wx.RIGHT, border=4)

        button_d = wx.Button(self.window, label='Dismiss all')
        self.bottom.Add(button_d, flag=wx.RIGHT, border=4)

        self.bottom.AddStretchSpacer()

        label = wx.StaticText(self.window, label='Snooze for:')
        self.bottom.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.number = NarrowSpinCtrl(self.window, min=1, max=999,
                                                        style=wx.SP_ARROW_KEYS)
        self.number.SetValue(5)
        self.bottom.Add(self.number, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.unit = wx.Choice(self.window,
                                choices=('minutes', 'hours', 'days', 'weeks'))
        self.unit.SetSelection(0)
        self.bottom.Add(self.unit, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.window.Bind(wx.EVT_BUTTON, self.snooze_all, button_s)
        self.window.Bind(wx.EVT_BUTTON, self.dismiss_all, button_d)

    def _handle_close(self, event):
        self._hide()

    def _show(self):
        self.window.Show(True)
        self.window.Centre()

    def _display_append(self):
        self.window.Layout()
        self._update_title()

        if not self.window.IsShown():
            # Centre only if not already shown; using ShowWithoutActivating
            # *before* the self.window.IsShown() test would never verify the
            # condition
            self.window.ShowWithoutActivating()
            self.window.Centre()

        self.window.RequestUserAttention()

    def _display_close(self):
        self.window.Layout()
        self._update_title()

        if len(self.alarms) == 0:
            self._hide()

    def _hide(self):
        self.window.Show(False)

    def is_shown(self):
        return self.window.IsShown()

    def toggle_shown(self, event):
        if self.window.IsShown():
            self._hide()
        else:
            self._show()

    def dismiss_all(self, event):
        core_api.block_databases()

        organism_alarms_api.dismiss_alarms(self._get_shown_alarms_dictionary())
        # Let the alarm off event close the alarms

        core_api.release_databases()

    def snooze_all(self, event):
        core_api.block_databases()

        organism_alarms_api.snooze_alarms(self._get_shown_alarms_dictionary(),
                                                  stime=self.get_snooze_time())
        # Let the alarm off event close the alarms

        core_api.release_databases()

    def _close_alarms(self, filename=None, id_=None, alarmid=None):
        for a in self.alarms.keys():
            afilename = self.alarms[a].get_filename()
            aitem = self.alarms[a].get_id()
            aid = self.alarms[a].get_alarmid()

            if filename in (afilename, None) and id_ in (aitem, None) and \
                                                        alarmid in (aid, None):
                self.alarms[a].close()
                del self.alarms[a]

        self.stimer.Stop()
        self.stimer = wx.CallLater(self.CDELAY, self._display_close)

    def _handle_close_db(self, kwargs):
        self._close_alarms(filename=kwargs['filename'])

    def _handle_alarm(self, kwargs):
        # Using CallAfter can cause (minor) bugs if the core timer is refreshed
        # in a loop (events could be displayed when not necessary...)
        wx.CallAfter(self._append, **kwargs)

    def _handle_alarm_off(self, kwargs):
        filename = kwargs['filename']
        if 'alarmid' in kwargs:
            alarmid = kwargs['alarmid']
            self._close_alarms(filename=filename, alarmid=alarmid)
        else:
            id_ = kwargs['id_']
            self._close_alarms(filename=filename, id_=id_)

    def _append(self, filename, id_, alarmid, start, end, alarm):
        a = self.make_alarmid(filename, alarmid)

        # Check whether the database is still open because this method is
        # called with wx.CallAfter in _handle_alarm, thus running in a
        # different thread; this way it can happen that, when _handle_alarm is
        # called, a database is still open, but when this method is called,
        # that database has been already closed; this would happen for example
        # when closing all the databases: after each database is closed (in
        # rapid succession), all the remaining alarms are searched and
        # signalled again, and when this method would be run (in a different
        # thread) the alarm's database would have already been closed, thus
        # raising an exception later when looking information for the item
        # (e.g. core_api.get_item_text)
        # Also, for the same reason, check if the item exists, as for example
        # performing several undos/redos of the database in rapid succession
        # (e.g. using CTRL+Z/Y) would cause the same issue
        if core_api.is_database_open(filename) and \
                                        core_api.is_item(filename, id_) and \
                                        a not in self.alarms:
            self.alarms[a] = Alarm(self, filename, id_, alarmid, start, end,
                                                                        alarm)

            if len(self.alarms) < self.LIMIT + 1:
                self.alarms[a].show()

            # Besides being much slower, calling Layout and the other
            # functions at every append would raise an exception for
            # excessive recursions in case of too many alarms are signalled
            # at once
            self.timer.Stop()
            self.timer = wx.CallLater(self.DELAY, self._display_append)

    def _update_title(self):
        self.window.SetTitle(''.join(('Outspline - ', str(len(self.alarms)),
                                                                   ' alarms')))

    @staticmethod
    def make_alarmid(filename, alarmid):
        return '_'.join((filename, str(alarmid)))

    def get_snooze_time(self):
        mult = {'minutes': 60,
                'hours': 3600,
                'days': 86400,
                'weeks': 604800}
        stime = self.number.GetValue() * mult[self.unit.GetString(
                                                    self.unit.GetSelection())]
        return stime

    def _get_shown_alarms_dictionary(self):
        alarmsd = {}

        for a in self.alarms:
            if self.alarms[a].is_shown():
                filename = self.alarms[a].get_filename()
                id_ = self.alarms[a].get_id()

                try:
                    alarmsd[filename]
                except KeyError:
                    alarmsd[filename] = {id_: []}
                else:
                    try:
                        alarmsd[filename][id_]
                    except KeyError:
                        alarmsd[filename][id_] = []

                alarmsd[filename][id_].append(self.alarms[a].get_alarmid())

        return alarmsd

    def get_show_menu_id(self):
        return self.mainmenu.get_show_id()


class Alarm(object):
    def __init__(self, awindow, filename, id_, alarmid, start, end, alarm):
        self.awindow = awindow
        self.filename = filename
        self.id_ = id_
        self.alarmid = alarmid
        self.start = start
        self.end = end
        self.alarm = alarm
        self.panel = None

    def show(self):
        log.debug('Appending alarm id: {}'.format(self.alarmid))

        self.panel = wx.Panel(self.awindow.panel)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

        self._init_widgets(self.panel)

        self.awindow.pbox.Add(self.panel, flag=wx.EXPAND)

    def is_shown(self):
        return bool(self.panel)

    def _init_widgets(self, parent):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(hbox, flag=wx.EXPAND | wx.ALL, border=4)

        startdate = wx.StaticText(parent, label=_time.strftime(
                                '%Y.%m.%d %H:%M', _time.localtime(self.start)))
        hbox.Add(startdate, 1, flag=wx.ALIGN_CENTER_VERTICAL)

        button_s = wx.Button(parent, label='Snooze', style=wx.BU_EXACTFIT)
        hbox.Add(button_s)

        button_d = wx.Button(parent, label='Dismiss', style=wx.BU_EXACTFIT)
        hbox.Add(button_d, flag=wx.LEFT, border=4)

        button_e = wx.Button(parent, label='Open', style=wx.BU_EXACTFIT)
        hbox.Add(button_e, flag=wx.LEFT, border=4)

        # wx.CP_NO_TLW_RESIZE in conjunction with
        # self.panel.GetParent().SendSizeEvent() on EVT_COLLAPSIBLEPANE_CHANGED
        # are necessary for the correct functioning
        self.pane = wx.CollapsiblePane(parent, style=wx.CP_NO_TLW_RESIZE)
        # Setting the label directly when instantiating CollapsiblePane through
        # the 'label' parameter would make it parse '&' characters to form
        # mnemonic shortcuts, like in menus
        self._set_pane_label()
        self.pbox.Add(self.pane, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.cpane = self.pane.GetPane()
        self.cbox = wx.BoxSizer(wx.VERTICAL)
        self.cpane.SetSizer(self.cbox)


        line = wx.StaticLine(parent, style=wx.LI_HORIZONTAL)
        self.pbox.Add(line, flag=wx.EXPAND)

        core_api.bind_to_update_item(self._update_info)

        self.panel.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                                                self._update_pane_ancestors)
        self.panel.Bind(wx.EVT_BUTTON, self.snooze, button_s)
        self.panel.Bind(wx.EVT_BUTTON, self.dismiss, button_d)
        self.panel.Bind(wx.EVT_BUTTON, self._open, button_e)

    def _update_info(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_:
            self._set_pane_label()

    def _set_pane_label(self):
        text = core_api.get_item_text(self.filename, self.id_)
        self.pane.SetLabel(text.partition('\n')[0])

    def _update_pane_ancestors(self, event):
        # Reset ancestors with EVT_COLLAPSIBLEPANE_CHANGED, otherwise they
        # should be reset everytime one of them is updated
        # This way if an ancestor is updated while the collapsible pane is
        # expanded, it will have to be collapsed and expanded again to be
        # reset, but that is a reasonable compromise

        if not event.GetCollapsed():
            # Get the size of the panel *before* adding or destroying any
            # children
            psize = self.pane.GetSize()

            self.cpane.DestroyChildren()

            for anc in core_api.get_item_ancestors(self.filename, self.id_):
                ancestor = wx.StaticText(self.cpane)
                # Setting the label directly when instantiating StaticText
                # through the 'label' parameter would make it parse '&'
                # characters to form mnemonic shortcuts, like in menus
                # Note that in this case the '&' characters have to be escaped
                # explicitly
                ancestor.SetLabel(anc.get_text().partition('\n')[0].replace(
                                                                    '&', '&&'))
                self.cbox.Add(ancestor, flag=wx.LEFT | wx.TOP, border=4)

            dbname = wx.StaticText(self.cpane)
            # Setting the label directly when instantiating StaticText through
            # the 'label' parameter would make it parse '&' characters to form
            # mnemonic shortcuts, like in menus
            dbname.SetLabel(_os.path.basename(self.filename).replace('&',
                                                                         '&&'))
            self.cbox.Add(dbname, flag=wx.LEFT | wx.TOP, border=4)

            # Without these operations, the panel's expanded height would
            # always be the one of its previous state (0 at the first expansion
            # attempt)
            self.cpane.Fit()
            csize = self.cpane.GetSize()
            psize.SetHeight(psize.GetHeight() + csize.GetHeight())
            self.pane.SetMinSize(psize)

        # This in conjunction with the wx.CP_NO_TLW_RESIZE style are necessary
        # for the correct functioning of the collapsible pane
        self.panel.GetParent().SendSizeEvent()

    def snooze(self, event):
        core_api.block_databases()

        organism_alarms_api.snooze_alarms({self.filename: {self.id_:
                    [self.alarmid, ]}}, stime=self.awindow.get_snooze_time())
        # Let the alarm off event close the alarm

        core_api.release_databases()

    def dismiss(self, event):
        core_api.block_databases()

        organism_alarms_api.dismiss_alarms({self.filename: {self.id_:
                                                            [self.alarmid, ]}})
        # Let the alarm off event close the alarm

        core_api.release_databases()

    def _open(self, event):
        wxgui_api.show_main_window()
        wxgui_api.open_editor(self.filename, self.id_)

    def close(self):
        if self.is_shown():
            log.debug('Destroying alarm id: {}'.format(self.alarmid))

            self.panel.Destroy()

            # It's necessary to explicitly unbind the handler, otherwise this
            # object will not be garbage-collected
            core_api.bind_to_update_item(self._update_info, False)

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    def get_alarmid(self):
        return self.alarmid


class MainMenu(wx.Menu):
    def __init__(self, alarmswindow):
        wx.Menu.__init__(self)
        self.alarmswindow = alarmswindow

        self.ID_SHOW = wx.NewId()

        self.menushow = wx.MenuItem(self, self.ID_SHOW,
                        "&Show window\tCTRL+SHIFT+a", "Show the alarms window",
                        kind=wx.ITEM_CHECK)

        self.AppendItem(self.menushow)

        wxgui_api.bind_to_menu(alarmswindow.toggle_shown, self.menushow)
        wxgui_api.bind_to_update_menu_items(self._update_items)

        wxgui_api.insert_menu_main_item('&Alarms',
                                    wxgui_api.get_menu_logs_position(), self)

    def _update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.menushow.Check(check=self.alarmswindow.is_shown())

    def get_show_id(self):
        return self.ID_SHOW


class TrayMenu(object):
    def __init__(self, alarmswindow):
        self.alarmswindow = alarmswindow

        if wxtrayicon_api:
            wxtrayicon_api.bind_to_create_menu(self._handle_create_tray_menu)
            wxtrayicon_api.bind_to_reset_menu(self._handle_reset_tray_menu)

    def _handle_create_tray_menu(self, kwargs):
        item = wx.MenuItem(kwargs['menu'],
                                        self.alarmswindow.get_show_menu_id(),
                                        "Show &alarms", kind=wx.ITEM_CHECK)
        self.traymenushow = wxtrayicon_api.add_menu_item(item)

        wxtrayicon_api.bind_to_tray_menu(self.alarmswindow.toggle_shown,
                                                            self.traymenushow)

    def _handle_reset_tray_menu(self, kwargs):
        self.traymenushow.Check(check=self.alarmswindow.is_shown())


def main():
    global alarmswindow
    alarmswindow = AlarmsWindow(wxgui_api.get_main_frame())
