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
import datetime as _datetime
import random
import wx

import organism.extensions.organizer_basicrules_api as organizer_basicrules_api
import organism.plugins.wxscheduler_api as wxscheduler_api

import widgets
import msgboxes

_RULE_DESC = 'Occur at regular time intervals'


class Rule():
    original_values = None
    mpanel = None
    pbox = None
    slabel = None
    startw = None
    ilabel = None
    intervalw = None
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
        self._create_widgets_interval()
        self._create_widgets_end()
        self._create_widgets_alarm()

        self._align_first_column()

    def _create_widgets_start(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.slabel = wx.StaticText(self.mpanel, label='Sample start date:')
        box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.startw = widgets.DateHourCtrl(self.mpanel)
        self.startw.set_values(self.original_values['refstartY'],
                               self.original_values['refstartm'],
                               self.original_values['refstartd'],
                               self.original_values['refstartH'],
                               self.original_values['refstartM'])
        box.Add(self.startw.get_main_panel())

    def _create_widgets_interval(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.pbox.Add(box, flag=wx.BOTTOM, border=4)

        self.ilabel = wx.StaticText(self.mpanel, label='Interval time:')
        box.Add(self.ilabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.intervalw = widgets.TimeSpanCtrl(self.mpanel, 1)
        self.intervalw.set_values(self.original_values['intervaln'],
                                  self.original_values['intervalu'])
        box.Add(self.intervalw.get_main_panel())

    def _create_widgets_end(self):
        self.endchoicew = widgets.WidgetChoiceCtrl(self.mpanel,
                                                         (('No duration', None),
                                    ('Duration:', self._create_duration_widget),
                            ('Sample end date:', self._create_end_date_widget)),
                                             self.original_values['endtype'], 4)
        self.endchoicew.force_update()
        self.pbox.Add(self.endchoicew.get_main_panel(), flag=wx.BOTTOM,
                                                                       border=4)

    def _create_duration_widget(self):
        self.endw = widgets.TimeSpanCtrl(self.endchoicew.get_main_panel(), 1)
        self.endw.set_values(self.original_values['rendn'],
                             self.original_values['rendu'])

        return self.endw.get_main_panel()

    def _create_end_date_widget(self):
        self.endw = widgets.DateHourCtrl(self.endchoicew.get_main_panel())
        self.endw.set_values(self.original_values['refendY'],
                             self.original_values['refendm'],
                             self.original_values['refendd'],
                             self.original_values['refendH'],
                             self.original_values['refendM'])

        return self.endw.get_main_panel()

    def _create_widgets_alarm(self):
        self.alarmchoicew = widgets.WidgetChoiceCtrl(self.mpanel,
                                                            (('No alarm', None),
                          ('Alarm advance:', self._create_alarm_advance_widget),
                        ('Sample alarm date:', self._create_alarm_date_widget)),
                                           self.original_values['alarmtype'], 4)
        self.alarmchoicew.force_update()
        self.pbox.Add(self.alarmchoicew.get_main_panel())

    def _create_alarm_advance_widget(self):
        self.alarmw = widgets.TimeSpanCtrl(self.alarmchoicew.get_main_panel(),
                                                                              0)
        self.alarmw.set_values(self.original_values['ralarmn'],
                               self.original_values['ralarmu'])

        return self.alarmw.get_main_panel()

    def _create_alarm_date_widget(self):
        self.alarmw = widgets.DateHourCtrl(self.alarmchoicew.get_main_panel())
        self.alarmw.set_values(self.original_values['refalarmY'],
                               self.original_values['refalarmm'],
                               self.original_values['refalarmd'],
                               self.original_values['refalarmH'],
                               self.original_values['refalarmM'])

        return self.alarmw.get_main_panel()

    def _align_first_column(self):
        sminw = self.slabel.GetSizeTuple()[0]
        iminw = self.ilabel.GetSizeTuple()[0]
        eminw = self.endchoicew.get_choice_width()
        aminw = self.alarmchoicew.get_choice_width()

        maxw = max((sminw, iminw, eminw, aminw))

        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((maxw, sminh))

        iminh = self.ilabel.GetMinHeight()
        self.ilabel.SetMinSize((maxw, iminh))

        self.endchoicew.set_choice_min_width(maxw)

        self.alarmchoicew.set_choice_min_width(maxw)

    def apply_rule(self, filename, id_):
        refstart = self.startw.get_unix_time()

        interval = self.intervalw.get_time_span()
        intervaln = self.intervalw.get_number()
        intervalu = self.intervalw.get_unit()

        endtype = self.endchoicew.get_selection()

        if endtype == 1:
            rend = self.endw.get_time_span()
            rendn = self.endw.get_number()
            rendu = self.endw.get_unit()
        elif endtype == 2:
            rend = self.endw.get_unix_time() - refstart
            rendn = None
            rendu = None
        else:
            rend = None
            rendn = None
            rendu = None

        alarmtype = self.alarmchoicew.get_selection()

        if alarmtype == 1:
            ralarm = self.alarmw.get_time_span()
            ralarmn = self.alarmw.get_number()
            ralarmu = self.alarmw.get_unit()
        elif alarmtype == 2:
            ralarm = refstart - self.alarmw.get_unix_time()
            ralarmn = None
            ralarmu = None
        else:
            ralarm = None
            ralarmn = None
            ralarmu = None

        try:
            ruled = organizer_basicrules_api.make_occur_regularly_single_rule(
                   refstart, interval, rend, ralarm, (None, endtype, alarmtype))
        except organizer_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule().ShowModal()
        else:
            label = self._make_label(intervaln, intervalu, refstart, rend,
                     ralarm, endtype, alarmtype, rendn, rendu, ralarmn, ralarmu)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        values = cls._compute_values(rulev)
        label = cls._make_label(values['intervaln'], values['intervalu'],
                           values['refstart'], values['rend'], values['ralarm'],
                        values['endtype'], values['alarmtype'], values['rendn'],
                          values['rendu'], values['ralarmn'], values['ralarmu'])
        wxscheduler_api.insert_rule(filename, id_, rule, label)

    @classmethod
    def _compute_values(cls, rule):
        values = {}

        if not rule:
            values['refmin'] = (int(_time.time()) // 3600 + 1) * 3600
            values['refmax'] = values['refmin'] + 3600

            values.update({
                'refspan': values['refmax'] - values['refmin'],
                'interval': 86400,
                'rstart': 0,
                'rend': 3600,
                'ralarm': 0,
                'endtype': 0,
                'alarmtype': 0,
            })
        else:
            values = {
                'refmax': rule[0],
                'refspan': rule[1],
                'interval': rule[2],
                'rstart': rule[3],
                'rend': rule[4] if rule[4] is not None else 3600,
                'ralarm': rule[5] if rule[5] is not None else 0,
                'endtype': rule[6][1],
                'alarmtype': rule[6][2],
            }

            values['refmin'] = values['refmax'] - values['refspan']

        values['refstart'] = values['refmin'] + values['rstart']

        values['intervaln'], values['intervalu'] = \
                 widgets.TimeSpanCtrl._compute_widget_values(values['interval'])

        values['rendn'], values['rendu'] = \
                     widgets.TimeSpanCtrl._compute_widget_values(values['rend'])

        # ralarm could be negative
        values['ralarmn'], values['ralarmu'] = \
                                    widgets.TimeSpanCtrl._compute_widget_values(
                                                     max((0, values['ralarm'])))

        refstart = values['refmin'] + values['rstart']

        localstart = _datetime.datetime.fromtimestamp(refstart)
        localend = _datetime.datetime.fromtimestamp(refstart + values['rend'])
        localalarm = _datetime.datetime.fromtimestamp(refstart - values['ralarm'
                                                                              ])

        values.update({
            'refstartY': localstart.year,
            'refstartm': localstart.month - 1,
            'refstartd': localstart.day,
            'refstartH': localstart.hour,
            'refstartM': localstart.minute,
            'refendY': localend.year,
            'refendm': localend.month - 1,
            'refendd': localend.day,
            'refendH': localend.hour,
            'refendM': localend.minute,
            'refalarmY': localalarm.year,
            'refalarmm': localalarm.month - 1,
            'refalarmd': localalarm.day,
            'refalarmH': localalarm.hour,
            'refalarmM': localalarm.minute,
        })

        return values

    @staticmethod
    def _make_label(intervaln, intervalu, refstart, rend, ralarm, endtype,
                                     alarmtype, rendn, rendu, ralarmn, ralarmu):
        label = 'Occur every {} {}'.format(intervaln, intervalu)

        label += ', for example on {}'.format(_time.strftime(
                             '%a %d %b %Y at %H:%M', _time.localtime(refstart)))

        if endtype == 1:
            label += ' for {} {}'.format(rendn, rendu)
        elif endtype == 2:
            label += _time.strftime(' until %a %d %b %Y at %H:%M',
                                               _time.localtime(refstart + rend))

        if alarmtype == 1:
            label += ', activate alarm {} {} before'.format(ralarmn, ralarmu)
        elif alarmtype == 2:
            label += _time.strftime(', alarm set on %a %d %b %Y at %H:%M',
                                             _time.localtime(refstart - ralarm))

        return label

    @staticmethod
    def create_random_rule():
        refstart = int((random.gauss(_time.time(), 15000)) // 60 * 60)

        interval = random.randint(1, 4320) * 60

        endtype = random.randint(0, 2)

        if endtype == 0:
            rend = None
        else:
            rend = random.randint(1, 360) * 60

        alarmtype = random.randint(0, 2)

        if alarmtype == 0:
            ralarm = None
        else:
            ralarm = random.randint(0, 360) * 60

        return organizer_basicrules_api.make_occur_regularly_single_rule(
                   refstart, interval, rend, ralarm, (None, endtype, alarmtype))
