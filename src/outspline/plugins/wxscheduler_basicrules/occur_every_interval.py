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

from outspline.static.wxclasses.timectrls import TimeSpanCtrl
import outspline.extensions.organism_basicrules_api as organism_basicrules_api
import outspline.plugins.wxscheduler_api as wxscheduler_api

import interface
import msgboxes


class Rule(object):
    def __init__(self, parent, filename, id_, standard, rule):
        self.original_values = self._compute_values(standard, rule)
        self.ui = interface.Interface(parent, filename, id_,
                                            (interface.StartDateSample,
                                            interface.Interval,
                                            interface.EndDateSample,
                                            interface.AlarmDateSample,
                                            interface.Standard),
                                      self.original_values)

    def apply_rule(self, filename, id_):
        values = self.ui.get_values()
        refstart = values['start_unix_time']
        interval = values['interval']
        intervaln = values['interval_number']
        intervalu = values['interval_unit']
        endtype = values['end_type']
        rend = values['end_relative_time']
        rendn = values['end_relative_number']
        rendu = values['end_relative_unit']
        alarmtype = values['alarm_type']
        ralarm = values['alarm_relative_time']
        ralarmn = values['alarm_relative_number']
        ralarmu = values['alarm_relative_unit']
        standard = values['time_standard']

        try:
            if standard == 'UTC':
                ruled = organism_basicrules_api.make_occur_regularly_rule_UTC(
                  refstart, interval, rend, ralarm, (None, endtype, alarmtype))
            else:
                ruled = organism_basicrules_api.make_occur_regularly_rule_local(
                  refstart, interval, rend, ralarm, (None, endtype, alarmtype))
        except organism_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule(msgboxes.end_time).ShowModal()
        else:
            label = self._make_label(intervaln, intervalu, refstart, rend,
                                            ralarm, endtype, alarmtype, rendn,
                                            rendu, ralarmn, ralarmu, standard)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        standard = 'UTC' if rule['rule'] == 'occur_regularly_UTC' else 'local'
        values = cls._compute_values(standard, rulev)
        label = cls._make_label(values['interval_number'],
                                values['interval_unit'],
                                values['reference_start'],
                                values['end_relative_time'],
                                values['alarm_relative_time'],
                                values['end_type'],
                                values['alarm_type'],
                                values['end_relative_number'],
                                values['end_relative_unit'],
                                values['alarm_relative_number'],
                                values['alarm_relative_unit'],
                                values['time_standard'])
        wxscheduler_api.insert_rule(filename, id_, rule, label)

    @classmethod
    def _compute_values(cls, standard, rule):
        # Remember to support also time zones that differ from UTC by not
        # exact hours (e.g. Australia/Adelaide)
        if not rule:
            nextdate = _datetime.datetime.now() + _datetime.timedelta(hours=1)
            refmin = int(_time.time()) // 86400 * 86400 + nextdate.hour * 3600
            refmax = refmin + 3600

            values = {
                'reference_min': refmin,
                'reference_max': refmax,
                'reference_start': refmin,
                'reference_span': refmax - refmin,
                'interval': 86400,
                'start_relative_time': 0,
                'end_relative_time': 3600,
                'alarm_relative_time': 0,
                'end_type': 0,
                'alarm_type': 0,
                'time_standard': standard,
            }
        else:
            values = {
                'reference_min': rule[0] - rule[1],
                'reference_max': rule[0],
                'reference_start': rule[0] - rule[1] + rule[3],
                'reference_span': rule[1],
                'interval': rule[2],
                'start_relative_time': rule[3],
                'end_relative_time': rule[4] if rule[4] is not None else 3600,
                'alarm_relative_time': rule[5] if rule[5] is not None else 0,
                'end_type': rule[6][1],
                'alarm_type': rule[6][2],
                'time_standard': standard,
            }

        wstart = _datetime.datetime.utcfromtimestamp(
                                            values['reference_start'])
        wend = _datetime.datetime.utcfromtimestamp(
                                            values['reference_start'] +
                                            values['end_relative_time'])
        walarm = _datetime.datetime.utcfromtimestamp(
                                            values['reference_start'] -
                                            values['alarm_relative_time'])

        values['interval_number'], values['interval_unit'] = \
                                    TimeSpanCtrl.compute_widget_values(
                                    values['interval'])

        values['end_relative_number'], values['end_relative_unit'] = \
                                    TimeSpanCtrl.compute_widget_values(
                                    values['end_relative_time'])

        # ralarm could be negative
        values['alarm_relative_number'], values['alarm_relative_unit'] = \
                                    TimeSpanCtrl.compute_widget_values(
                                    max((0, values['alarm_relative_time'])))

        values.update({
            'start_year': wstart.year,
            'start_month': wstart.month - 1,
            'start_day': wstart.day,
            'start_hour': wstart.hour,
            'start_minute': wstart.minute,
            'end_year': wend.year,
            'end_month': wend.month - 1,
            'end_day': wend.day,
            'end_hour': wend.hour,
            'end_minute': wend.minute,
            'alarm_year': walarm.year,
            'alarm_month': walarm.month - 1,
            'alarm_day': walarm.day,
            'alarm_hour': walarm.hour,
            'alarm_minute': walarm.minute,
        })

        return values

    @staticmethod
    def _make_label(intervaln, intervalu, refstart, rend, ralarm, endtype,
                        alarmtype, rendn, rendu, ralarmn, ralarmu, standard):
        label = 'Occur every {} {}'.format(intervaln, intervalu)

        label += ', for example on {} ({})'.format(_time.strftime(
                    '%a %d %b %Y at %H:%M', _time.gmtime(refstart)), standard)

        if endtype == 1:
            label += ' for {} {}'.format(rendn, rendu)
        elif endtype == 2:
            label += _time.strftime(' until %a %d %b %Y at %H:%M',
                                              _time.gmtime(refstart + rend))

        if alarmtype == 1:
            label += ', activate alarm {} {} before'.format(ralarmn, ralarmu)
        elif alarmtype == 2:
            label += _time.strftime(', alarm set on %a %d %b %Y at %H:%M',
                                            _time.gmtime(refstart - ralarm))

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

        stdn = random.randint(0, 1)

        if stdn == 0:
            return organism_basicrules_api.make_occur_regularly_rule_local(
                  refstart, interval, rend, ralarm, (None, endtype, alarmtype))
        else:
            return organism_basicrules_api.make_occur_regularly_rule_UTC(
                  refstart, interval, rend, ralarm, (None, endtype, alarmtype))
