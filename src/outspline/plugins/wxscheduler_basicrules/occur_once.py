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

import time as _time
import datetime as _datetime
import random
import wx

from outspline.static.wxclasses.choices import WidgetChoiceCtrl
from outspline.static.wxclasses.time import DateHourCtrl, TimeSpanCtrl
import outspline.extensions.organism_basicrules_api as organism_basicrules_api
import outspline.plugins.wxscheduler_api as wxscheduler_api

import msgboxes

_RULE_DESC = 'Occur once'


class Rule():
    original_values = None
    mpanel = None
    pbox = None
    slabel = None
    startw = None
    endchoicew = None
    endw = None
    alarmchoicew = None
    alarmw = None

    def __init__(self, parent, filename, id_, rule):
        self.original_values = self._compute_values(rule)

        self._create_widgets(parent)

        wxscheduler_api.change_rule(filename, id_, self.mpanel)

    def _create_widgets(self, parent):
        self.mpanel = wx.Panel(parent)

        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.mpanel.SetSizer(self.pbox)

        self._create_widgets_start()
        self._create_widgets_end()
        self._create_widgets_alarm()

        self._align_first_column()

    def _create_widgets_start(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.slabel = wx.StaticText(self.mpanel, label='Start date:')
        box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.startw = DateHourCtrl(self.mpanel)
        self.startw.set_values(self.original_values['startY'],
                               self.original_values['startm'],
                               self.original_values['startd'],
                               self.original_values['startH'],
                               self.original_values['startM'])
        box.Add(self.startw.get_main_panel())

    def _create_widgets_end(self):
        self.endchoicew = WidgetChoiceCtrl(self.mpanel, (('No duration', None),
                                   ('Duration:', self._create_duration_widget),
                                  ('End date:', self._create_end_date_widget)),
                                            self.original_values['endtype'], 4)
        self.endchoicew.force_update()
        self.pbox.Add(self.endchoicew.get_main_panel(), flag=wx.BOTTOM,
                                                                      border=4)

    def _create_duration_widget(self):
        self.endw = TimeSpanCtrl(self.endchoicew.get_main_panel(), 1, 999)
        self.endw.set_values(self.original_values['rendn'],
                             self.original_values['rendu'])

        return self.endw.get_main_panel()

    def _create_end_date_widget(self):
        self.endw = DateHourCtrl(self.endchoicew.get_main_panel())
        self.endw.set_values(self.original_values['endY'],
                             self.original_values['endm'],
                             self.original_values['endd'],
                             self.original_values['endH'],
                             self.original_values['endM'])

        return self.endw.get_main_panel()

    def _create_widgets_alarm(self):
        self.alarmchoicew = WidgetChoiceCtrl(self.mpanel, (('No alarm', None),
                         ('Alarm advance:', self._create_alarm_advance_widget),
                              ('Alarm date:', self._create_alarm_date_widget)),
                                          self.original_values['alarmtype'], 4)
        self.alarmchoicew.force_update()
        self.pbox.Add(self.alarmchoicew.get_main_panel())

    def _create_alarm_advance_widget(self):
        self.alarmw = TimeSpanCtrl(self.alarmchoicew.get_main_panel(), 0, 999)
        self.alarmw.set_values(self.original_values['ralarmn'],
                               self.original_values['ralarmu'])

        return self.alarmw.get_main_panel()

    def _create_alarm_date_widget(self):
        self.alarmw = DateHourCtrl(self.alarmchoicew.get_main_panel())
        self.alarmw.set_values(self.original_values['alarmY'],
                               self.original_values['alarmm'],
                               self.original_values['alarmd'],
                               self.original_values['alarmH'],
                               self.original_values['alarmM'])

        return self.alarmw.get_main_panel()

    def _align_first_column(self):
        sminw = self.slabel.GetSizeTuple()[0]
        eminw = self.endchoicew.get_choice_width()
        aminw = self.alarmchoicew.get_choice_width()

        maxw = max((sminw, eminw, aminw))

        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((maxw, sminh))

        self.endchoicew.set_choice_min_width(maxw)

        self.alarmchoicew.set_choice_min_width(maxw)

    def apply_rule(self, filename, id_):
        start = self.startw.get_unix_time()

        endtype = self.endchoicew.get_selection()

        if endtype == 1:
            end = start + self.endw.get_time_span()
            rendn = self.endw.get_number()
            rendu = self.endw.get_unit()
        elif endtype == 2:
            end = self.endw.get_unix_time()
            rendn = None
            rendu = None
        else:
            end = None
            rendn = None
            rendu = None

        alarmtype = self.alarmchoicew.get_selection()

        if alarmtype == 1:
            alarm = start - self.alarmw.get_time_span()
            ralarmn = self.alarmw.get_number()
            ralarmu = self.alarmw.get_unit()
        elif alarmtype == 2:
            alarm = self.alarmw.get_unix_time()
            ralarmn = None
            ralarmu = None
        else:
            alarm = None
            ralarmn = None
            ralarmu = None

        try:
            ruled = organism_basicrules_api.make_occur_once_rule(start, end,
                                                   alarm, (endtype, alarmtype))
        except organism_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule(msgboxes.end_time).ShowModal()
        else:
            label = self._make_label(start, end, alarm, endtype, alarmtype,
                                                rendn, rendu, ralarmn, ralarmu)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        values = cls._compute_values(rulev)
        label = cls._make_label(values['start'], values['end'],
                       values['alarm'], values['endtype'], values['alarmtype'],
                                              values['rendn'], values['rendu'],
                                          values['ralarmn'], values['ralarmu'])
        wxscheduler_api.insert_rule(filename, id_, rule, label)

    @classmethod
    def _compute_values(cls, rule):
        values = {}

        if not rule:
            values['start'] = (int(_time.time()) // 3600 + 1) * 3600

            values.update({
                'end': values['start'] + 3600,
                'alarm': values['start'],
                'endtype': 0,
                'alarmtype': 0,
            })
        else:
            values = {
                'start': rule[0],
                'end': rule[1] if rule[1] else rule[0] + 3600,
                'alarm': rule[2] if rule[2] else rule[0],
                'endtype': rule[3][0],
                'alarmtype': rule[3][1],
            }

        values['rendn'], values['rendu'] = \
                                           TimeSpanCtrl._compute_widget_values(
                                               values['end'] - values['start'])

        values['ralarmn'], values['ralarmu'] = \
                                           TimeSpanCtrl._compute_widget_values(
                                   max((0, values['start'] - values['alarm'])))

        localstart = _datetime.datetime.fromtimestamp(values['start'])
        localend = _datetime.datetime.fromtimestamp(values['end'])
        localalarm = _datetime.datetime.fromtimestamp(values['alarm'])

        values.update({
            'startY': localstart.year,
            'startm': localstart.month - 1,
            'startd': localstart.day,
            'startH': localstart.hour,
            'startM': localstart.minute,
            'endY': localend.year,
            'endm': localend.month - 1,
            'endd': localend.day,
            'endH': localend.hour,
            'endM': localend.minute,
            'alarmY': localalarm.year,
            'alarmm': localalarm.month - 1,
            'alarmd': localalarm.day,
            'alarmH': localalarm.hour,
            'alarmM': localalarm.minute,
        })

        return values

    @staticmethod
    def _make_label(start, end, alarm, endtype, alarmtype, rendn, rendu,
                                                             ralarmn, ralarmu):
        label = ' '.join(('Occur once',
                                      _time.strftime('on %a %d %b %Y at %H:%M',
                                                      _time.localtime(start))))

        if endtype == 1:
            label += ' for {} {}'.format(rendn, rendu)
        elif endtype == 2:
            label += _time.strftime(' until %a %d %b %Y at %H:%M',
                                                          _time.localtime(end))

        if alarmtype == 1:
            label += ', activate alarm {} {} before'.format(ralarmn, ralarmu)
        elif alarmtype == 2:
            label += _time.strftime(', alarm set on %a %d %b %Y at %H:%M',
                                                        _time.localtime(alarm))

        return label

    @staticmethod
    def create_random_rule():
        start = int((random.gauss(_time.time(), 15000)) // 60 * 60)

        endtype = random.randint(0, 2)

        if endtype == 0:
            end = None
        else:
            end = start + random.randint(1, 360) * 60

        alarmtype = random.randint(0, 2)

        if alarmtype == 0:
            alarm = None
        else:
            alarm = start - random.randint(0, 360) * 60

        return organism_basicrules_api.make_occur_once_rule(start, end, alarm,
                                                          (endtype, alarmtype))
