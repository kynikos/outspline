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

import time as _time
import wx

import organism.extensions.organizer_basicrules_api as organizer_basicrules_api
import organism.plugins.wxscheduler_api as wxscheduler_api

_RULE_DESC = 'Occur every day at <time> for <time>'


class Rule():
    mwidgets = None
    mpanel = None
    pgrid = None

    def __init__(self, kwargs):
        self._create_widgets(kwargs['parent'])

        # dict.get() returns None if key is not in dictionary, and it happens
        # when the interface is being set up for a new rule
        rstart = kwargs['ruled'].get('rstart')
        rendn = kwargs['ruled'].get('rendn')
        rendu = kwargs['ruled'].get('rendu')
        ralarm = kwargs['ruled'].get('ralarm')

        self._init_values(rstart, rendn, rendu, ralarm)

        wxscheduler_api.change_rule(kwargs['filename'], kwargs['id_'],
                                                                    self.mpanel)

    def _create_widgets(self, parent):
        self.mwidgets = {}

        self.mpanel = wx.Panel(parent)

        self.pgrid = wx.GridBagSizer(4, 4)
        self.mpanel.SetSizer(self.pgrid)

        self._create_widgets_start()
        self._create_widgets_end()
        self._create_widgets_alarm()

    def _create_widgets_start(self):
        slabel = wx.StaticText(self.mpanel, label='At:')
        self.pgrid.Add(slabel, (0, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        self.mwidgets['start_hour'] = wx.SpinCtrl(self.mpanel, min=0, max=23,
                                           size=(40, 21),
                                           style=wx.SP_ARROW_KEYS | wx.SP_WRAP)
        self.pgrid.Add(self.mwidgets['start_hour'], (0, 2),
                  flag=wx.ALIGN_CENTER_VERTICAL)

        slabel = wx.StaticText(self.mpanel, label=':')
        self.pgrid.Add(slabel, (0, 3), flag=wx.ALIGN_CENTER_VERTICAL)

        self.mwidgets['start_minute'] = wx.SpinCtrl(self.mpanel, min=0, max=59,
                                           size=(40, 21),
                                           style=wx.SP_ARROW_KEYS | wx.SP_WRAP)
        self.pgrid.Add(self.mwidgets['start_minute'], (0, 4),
                  flag=wx.ALIGN_CENTER_VERTICAL)

    def _create_widgets_end(self):
        self.mwidgets['end_chbox'] = wx.CheckBox(self.mpanel)
        self.pgrid.Add(self.mwidgets['end_chbox'], (1, 0))

        slabel = wx.StaticText(self.mpanel, label='For:')
        self.pgrid.Add(slabel, (1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        self.mwidgets['end_number'] = wx.SpinCtrl(self.mpanel, min=1, max=99,
                                             size=(40, 21),
                                             style=wx.SP_ARROW_KEYS)
        self.pgrid.Add(self.mwidgets['end_number'], (1, 2),
                                                  flag=wx.ALIGN_CENTER_VERTICAL)

        self.mwidgets['end_unit'] = wx.ComboBox(self.mpanel, value='minutes',
                                           size=(100, 21),
                                           choices=('minutes', 'hours', 'days',
                                                    'weeks', 'months', 'years'),
                                           style=wx.CB_READONLY)
        self.pgrid.Add(self.mwidgets['end_unit'], (1, 3), span=(1, 2),
                  flag=wx.ALIGN_CENTER_VERTICAL)

        self.mpanel.Bind(wx.EVT_CHECKBOX, self.handle_end_checkbox,
                                                     self.mwidgets['end_chbox'])

    def _create_widgets_alarm(self):
        self.mwidgets['alarm_chbox'] = wx.CheckBox(self.mpanel)
        self.pgrid.Add(self.mwidgets['alarm_chbox'], (2, 0))

        slabel = wx.StaticText(self.mpanel, label='Alarm')
        self.pgrid.Add(slabel, (2, 1), span=(1, 2),
                                                  flag=wx.ALIGN_CENTER_VERTICAL)

    def _init_values(self, rstart, rendn, rendu, ralarm):
        if rstart == None:
            rstart = int(_time.strftime('%H', _time.localtime())) * 3600 + 3600

        self.mwidgets['start_hour'].SetValue(rstart // 3600)
        self.mwidgets['start_minute'].SetValue(rstart % 3600 // 60)

        if rendn == None:
            self.mwidgets['end_chbox'].SetValue(False)
            rendn = 1
            rendu = 'hours'

            self.mwidgets['end_number'].Disable()
            self.mwidgets['end_unit'].Disable()
        else:
            self.mwidgets['end_chbox'].SetValue(True)

        self.mwidgets['end_number'].SetValue(rendn)
        self.mwidgets['end_unit'].SetValue(rendu)

        if ralarm == None:
            self.mwidgets['alarm_chbox'].SetValue(False)
        else:
            self.mwidgets['alarm_chbox'].SetValue(True)


    def handle_end_checkbox(self, event):
        if event.IsChecked():
            self.mwidgets['end_number'].Enable()
            self.mwidgets['end_unit'].Enable()
        else:
            self.mwidgets['end_number'].Disable()
            self.mwidgets['end_unit'].Disable()


    def apply_rule(self, kwargs):
        shour = self.mwidgets['start_hour'].GetValue()
        sminute = self.mwidgets['start_minute'].GetValue()

        rstart = shour * 3600 + sminute * 60

        if self.mwidgets['end_chbox'].GetValue():
            rendn = self.mwidgets['end_number'].GetValue()
            rendu = self.mwidgets['end_unit'].GetValue()
        else:
            rendn = None
            rendu = None

        if self.mwidgets['alarm_chbox'].GetValue():
            ralarm = 0
        else:
            ralarm = None

        try:
            ruled = organizer_basicrules_api.make_occur_every_day_rule(rstart,
                                                           rendn, rendu, ralarm)
        except organizer_basicrules_api.BadRuleError:
            # At the moment this warning's message is not relevant since the
            # exception will never be raised because the rule is created safely
            # with this interface
            msgboxes.warn_bad_rule().ShowModal()
        else:
            label = self.make_label(rstart, rendn, rendu, ralarm)
            wxscheduler_api.apply_rule(kwargs['filename'], kwargs['id_'], ruled,
                                                                          label)

    @classmethod
    def insert_rule(cls, kwargs):
        rstart = kwargs['rule']['rstart']
        rendn = kwargs['rule']['rendn']
        rendu = kwargs['rule']['rendu']
        ralarm = kwargs['rule']['ralarm']

        ruled = organizer_basicrules_api.make_occur_every_day_rule(rstart,
                                                           rendn, rendu, ralarm)
        label = cls.make_label(rstart, rendn, rendu, ralarm)
        wxscheduler_api.insert_rule(kwargs['filename'], kwargs['id_'], ruled,
                                                                          label)

    @staticmethod
    def make_label(rstart, rendn, rendu, ralarm):
        label = 'Occur every day at {}:{}'.format(str(rstart // 3600).zfill(2),
                                              str(rstart % 3600 // 60).zfill(2))

        if rendn != None:
            label += ' for {} {}'.format(rendn, rendu)

        if ralarm != None:
            label += ', alarm enabled'

        return label
