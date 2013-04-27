# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import os as _os
import wx

import organism.coreaux_api as coreaux_api
import organism.core_api as core_api
import organism.extensions.organizer_alarms_api as organizer_alarms_api
import organism.interfaces.wxgui_api as wxgui_api
wxtrayicon_api = coreaux_api.import_plugin_api('wxtrayicon')

_ALARMS_MIN_SIZE = (400, 140)
_ALARMS_TITLE = 'Organism - Alarms'
_ALARMS_ICON_BUNDLE = wx.IconBundle()
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms', wx.ART_TOOLBAR))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms', wx.ART_MENU))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms', wx.ART_BUTTON))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                   wx.ART_FRAME_ICON))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                   wx.ART_CMN_DIALOG))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                   wx.ART_HELP_BROWSER))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms',
                                                   wx.ART_MESSAGE_BOX))
_ALARMS_ICON_BUNDLE.AddIcon(wx.ArtProvider.GetIcon('@alarms', wx.ART_OTHER))
_WRAP = 260


class AlarmsWindow():
    config = None
    window = None
    panel = None
    pbox = None
    snooze = None
    bottom = None
    ID_SHOW = None
    menushow = None
    traymenushow = None
    number = None
    unit = None
    alarms = None

    def __init__(self, parent):
        self.config = coreaux_api.get_plugin_configuration('wxalarms')

        self.window = wx.Frame(parent, title=_ALARMS_TITLE, size=[int(s)
                          for s in self.config['initial_geometry'].split('x')])
        self.window.SetMinSize(_ALARMS_MIN_SIZE)

        self.window.SetIcons(_ALARMS_ICON_BUNDLE)

        self.alarms = {}

        box = wx.BoxSizer(wx.VERTICAL)
        self.window.SetSizer(box)

        self.panel = wx.ScrolledWindow(self.window, style=wx.BORDER_SUNKEN)
        self.panel.SetScrollRate(20, 20)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)
        box.Add(self.panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        self.snooze = wx.Panel(self.window)
        self._init_snooze(self.snooze)
        box.Add(self.snooze, flag=wx.LEFT | wx.RIGHT, border=4)

        self.bottom = wx.Panel(self.window)
        self._init_bottom(self.bottom)
        box.Add(self.bottom, flag=wx.ALL, border=4)

        self.ID_SHOW = wx.NewId()
        self.menushow = wxgui_api.insert_menu_item('View',
                                               self.config.get_int('menu_pos'),
                                               'Show &alarms\tCtrl+R',
                                               id_=self.ID_SHOW,
                                               help='Open the alarms window',
                                               kind='check',
                                               sep=self.config['menu_sep'])

        parent.Bind(wx.EVT_MENU, self.toggle_shown, self.menushow)

        self.window.Bind(wx.EVT_CLOSE, self.hide)

        core_api.bind_to_delete_item(self.handle_remove_item)
        core_api.bind_to_history_remove(self.handle_remove_item)
        organizer_alarms_api.bind_to_alarm(self.handle_alarm)
        organizer_alarms_api.bind_to_alarm_off(self.handle_alarm_off)
        wxgui_api.bind_to_close_database(self.handle_close_db)
        wxgui_api.bind_to_reset_menu_items(self.handle_reset_menu_items)

        if wxtrayicon_api:
            wxtrayicon_api.bind_to_create_menu(self.handle_create_tray_menu)
            wxtrayicon_api.bind_to_reset_menu(self.handle_reset_tray_menu)

    def handle_reset_menu_items(self, kwargs):
        if kwargs['menu'] is self.menushow.GetMenu():
            self.menushow.Check(check=self.window.IsShown())

    def handle_create_tray_menu(self, kwargs):
        self.traymenushow = wxtrayicon_api.insert_menu_item(
                                           self.config.get_int('traymenu_pos'),
                                           'Show &alarms', id_=self.ID_SHOW,
                                           kind='check',
                                           sep=self.config['traymenu_sep'])

        wxtrayicon_api.bind_to_tray_menu(self.toggle_shown, self.traymenushow)

    def handle_reset_tray_menu(self, kwargs):
        self.traymenushow.Check(check=self.window.IsShown())

    def _init_snooze(self, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.snooze.SetSizer(box)

        label = wx.StaticText(parent, label='Snooze configuration:')
        box.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.number = wx.SpinCtrl(parent, min=1, max=99, size=(40, 21),
                                  style=wx.SP_ARROW_KEYS)
        self.number.SetValue(5)
        box.Add(self.number, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                border=4)

        self.unit = wx.ComboBox(parent, value='minutes', size=(100, 21),
                                choices=('minutes', 'hours', 'days',
                                         'weeks', 'months', 'years'),
                                style=wx.CB_READONLY)
        box.Add(self.unit, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

    def _init_bottom(self, parent):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom.SetSizer(box)

        button_s = wx.Button(parent, label='Snooze all', size=(-1, 24))
        box.Add(button_s, flag=wx.RIGHT, border=4)

        button_d = wx.Button(parent, label='Dismiss all', size=(-1, 24))
        box.Add(button_d, flag=wx.RIGHT, border=4)

        self.window.Bind(wx.EVT_BUTTON, self.snooze_all, button_s)
        self.window.Bind(wx.EVT_BUTTON, self.dismiss_all, button_d)

    def show(self, event=None):
        self.window.Show(True)
        self.window.Centre()

    def hide(self, event=None):
        self.window.Show(False)

    def toggle_shown(self, event):
        if self.window.IsShown():
            self.hide()
        else:
            self.show()

    def dismiss_all(self, event):
        core_api.block_databases()

        alarmst = []
        for a in self.alarms:
            alarmst.append((self.alarms[a].get_filename(),
                            self.alarms[a].get_alarmid()))
        organizer_alarms_api.dismiss_alarms(alarmst)
        # Let the alarm off event close the alarms

        core_api.release_databases()

    def snooze_all(self, event):
        core_api.block_databases()

        alarmst = []
        for a in self.alarms:
            alarmst.append((self.alarms[a].get_filename(),
                            self.alarms[a].get_alarmid()))
        organizer_alarms_api.snooze_alarms(alarmst,
                                                   stime=self.get_snooze_time())
        # Let the alarm off event close the alarms

        core_api.release_databases()

    def close_alarms(self, filename=None, id_=None, alarmid=None):
        for a in tuple(self.alarms.keys()):
            afilename = self.alarms[a].get_filename()
            aitem = self.alarms[a].get_id()
            aid = self.alarms[a].get_alarmid()
            if filename in (afilename, None) and id_ in (aitem, None) and \
                                                         alarmid in (aid, None):
                self.alarms[a].close()

    def handle_close_db(self, kwargs):
        self.close_alarms(filename=kwargs['filename'])

    def handle_remove_item(self, kwargs):
        self.close_alarms(filename=kwargs['filename'], id_=kwargs['id_'])

    def handle_alarm(self, kwargs):
        # Using CallAfter can cause (minor) bugs if the core timer is refreshed
        # in a loop (events could be displayed when not necessary...)
        wx.CallAfter(self.append, **kwargs)

    def handle_alarm_off(self, kwargs):
        filename = kwargs['filename']
        if 'alarmid' in kwargs:
            alarmid = kwargs['alarmid']
            self.close_alarms(filename=filename, alarmid=alarmid)
        else:
            id_ = kwargs['id_']
            self.close_alarms(filename=filename, id_=id_)

    def append(self, filename, id_, alarmid, start, end, alarm):
        a = self.make_alarmid(filename, alarmid)
        # Check whether the database is still open because this method is called
        # with wx.CallAfter in handle_alarm, thus running in a different thread;
        # this way it can happen that, when handle_alarm is called, a database
        # is still open, but when this method is called, that database has been
        # already closed; this would happen for example when closing all the
        # databases: after each database is closed (in rapid succession), all
        # the remaining alarms are searched and signalled again, and when this
        # method would be run (in a different thread) the alarm's database would
        # have already been closed, thus raising an exception later when looking
        # information for the item (e.g. core_api.get_item_text)
        if core_api.is_database_open(filename) and a not in self.alarms:
            self.alarms[a] = Alarm(self, filename, id_, alarmid, start, end,
                                   alarm)
            self.window.Layout()
            self.show()

    @staticmethod
    def make_alarmid(filename, alarmid):
        return '_'.join((filename, str(alarmid)))

    def get_snooze_time(self):
        mult = {'minutes': 60,
                'hours': 3600,
                'days': 86400,
                'weeks': 604800,
                'months': 2592000,
                'years': 31536000}
        stime = self.number.GetValue() * mult[self.unit.GetValue()]
        return stime


class Alarm():
    awindow = None
    panel = None
    pgrid = None
    filename = None
    id_ = None
    alarmid = None
    start = None
    end = None
    alarm = None

    def __init__(self, awindow, filename, id_, alarmid, start, end, alarm):
        self.awindow = awindow
        self.panel = wx.Panel(awindow.panel)
        self.pgrid = wx.GridBagSizer(4, 4)
        self.panel.SetSizer(self.pgrid)
        self.pgrid.AddGrowableCol(0)

        self.filename = filename
        self.id_ = id_
        self.alarmid = alarmid
        self.start = start
        self.end = end
        self.alarm = alarm

        self._init_widgets(self.panel)

        awindow.pbox.Add(self.panel, flag=wx.EXPAND)

    def _init_widgets(self, parent):
        label1 = wx.StaticText(parent, label=_os.path.basename(self.filename))
        label1.Wrap(_WRAP)
        self.pgrid.Add(label1, (0, 0),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.TOP,
                       border=4)

        text = core_api.get_item_text(self.filename, self.id_)

        label2 = wx.StaticText(parent, label=text.partition('\n')[0])
        label2.Wrap(_WRAP)
        self.pgrid.Add(label2, (1, 0), span=(1, 2),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)

        button_s = wx.Button(parent, label='Snooze', size=(-1, 24))
        self.pgrid.Add(button_s, (0, 1), flag=wx.ALIGN_RIGHT | wx.TOP,
                       border=4)

        button_d = wx.Button(parent, label='Dismiss', size=(-1, 24))
        self.pgrid.Add(button_d, (0, 2), flag=wx.RIGHT | wx.TOP, border=4)

        button_e = wx.Button(parent, label='Open', size=(-1, 24))
        self.pgrid.Add(button_e, (1, 2), flag=wx.RIGHT, border=4)

        line = wx.StaticLine(parent, size=(1, 1), style=wx.LI_HORIZONTAL)
        self.pgrid.Add(line, (2, 0), span=(1, 3), flag=wx.EXPAND)

        self.panel.Bind(wx.EVT_BUTTON, self.snooze, button_s)
        self.panel.Bind(wx.EVT_BUTTON, self.dismiss, button_d)
        self.panel.Bind(wx.EVT_BUTTON, self.open, button_e)

    def snooze(self, event):
        core_api.block_databases()

        organizer_alarms_api.snooze_alarms(((self.filename, self.alarmid), ),
                                          stime=self.awindow.get_snooze_time())
        # Let the alarm off event close the alarm

        core_api.release_databases()

    def dismiss(self, event):
        core_api.block_databases()

        organizer_alarms_api.dismiss_alarms(((self.filename, self.alarmid), ))
        # Let the alarm off event close the alarm

        core_api.release_databases()

    def open(self, event):
        wxgui_api.open_editor(self.filename, self.id_)

    def close(self):
        self.panel.Destroy()
        self.awindow.window.Layout()
        del self.awindow.alarms[self.awindow.make_alarmid(self.filename,
                                                          self.alarmid)]

        if len(self.awindow.alarms) == 0:
            self.awindow.hide()

    def get_filename(self):
        return self.filename

    def get_id(self):
        return self.id_

    def get_alarmid(self):
        return self.alarmid


def main():
    AlarmsWindow(wxgui_api.get_main_frame())
