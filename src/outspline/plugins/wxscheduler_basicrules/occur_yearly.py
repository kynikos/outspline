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

from outspline.static.wxclasses.timectrls import DateHourCtrl, TimeSpanCtrl

import outspline.extensions.organism_basicrules_api as organism_basicrules_api
import outspline.plugins.wxscheduler_api as wxscheduler_api

import interface
import msgboxes


class Rule(object):
    def __init__(self, parent, filename, id_, standard, rule):
        self.original_values = self._compute_values(standard, rule)
        self.ui = interface.Interface(parent, filename, id_,
                                            (interface.StartDateSample,
                                            interface.IntervalYears,
                                            interface.EndTime,
                                            interface.AlarmTime,
                                            interface.Standard),
                                      self.original_values)

    def apply_rule(self, filename, id_):
        values = self.ui.get_values()
        refstart = values['start_unix_time']
        refyear = values['start_year']
        month = values['start_month'] + 1
        day = values['start_day']
        rstartH = values['start_hour']
        rstartM = values['start_minute']
        interval = values['interval_years']
        endtype = values['end_type']
        rend = values['end_relative_time']
        fend = values['end_next_day']
        rendn = values['end_relative_number']
        rendu = values['end_relative_unit']
        rendH = values['end_hour']
        rendM = values['end_minute']
        alarmtype = values['alarm_type']
        ralarm = values['alarm_relative_time']
        palarm = values['alarm_previous_day']
        ralarmn = values['alarm_relative_number']
        ralarmu = values['alarm_relative_unit']
        ralarmH = values['alarm_hour']
        ralarmM = values['alarm_minute']
        standard = values['time_standard']

        try:
            if standard == 'UTC':
                ruled = organism_basicrules_api.make_occur_yearly_rule_UTC(
                            interval, refyear, month, day, rstartH, rstartM,
                            rend, ralarm, (endtype, alarmtype))
            else:
                ruled = organism_basicrules_api.make_occur_yearly_rule_local(
                            interval, refyear, month, day, rstartH, rstartM,
                            rend, ralarm, (endtype, alarmtype))
        except organism_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule(msgboxes.generic).ShowModal()
        else:
            label = self._make_label(interval, refyear, month, day, rstartH,
                                    rstartM, rendH, rendM, ralarmH, ralarmM,
                                    rendn, rendu, ralarmn, ralarmu, endtype,
                                    alarmtype, fend, palarm, standard)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        standard = 'UTC' if rule['rule'] == 'occur_yearly_UTC' else 'local'
        values = cls._compute_values(standard, rulev)
        label = cls._make_label(values['interval_years'],
                                values['start_year'],
                                values['start_month'] + 1,
                                values['start_day'],
                                values['start_hour'],
                                values['start_minute'],
                                values['end_hour'],
                                values['end_minute'],
                                values['alarm_hour'],
                                values['alarm_minute'],
                                values['end_relative_number'],
                                values['end_relative_unit'],
                                values['alarm_relative_number'],
                                values['alarm_relative_unit'],
                                values['end_type'],
                                values['alarm_type'],
                                values['end_next_day'],
                                values['alarm_previous_day'],
                                values['time_standard'])
        wxscheduler_api.insert_rule(filename, id_, rule, label)

    @classmethod
    def _compute_values(cls, standard, rule):
        # Remember to support also time zones that differ from UTC by not
        # exact hours (e.g. Australia/Adelaide)
        if not rule:
            nextdate = _datetime.datetime.now() + _datetime.timedelta(hours=1)
            sdate = _datetime.datetime.combine(nextdate.date(),
                                            _datetime.time(hour=nextdate.hour))

            values = {
                'interval_years': 1,
                'start_year': sdate.year,
                'start_month_1': sdate.month,
                'start_day':sdate.day,
                'start_hour': sdate.hour,
                'start_minute': 0,
                'end_relative_time': 3600,
                'alarm_relative_time': 0,
                'end_type': 0,
                'alarm_type': 0,
                'time_standard': standard,
            }
        else:
            values = {
                'maxoverlap': rule[0],
                'interval_years': rule[1],
                'start_year': rule[2],
                'start_month_1': rule[3],
                'start_day': rule[4],
                'start_hour': rule[5],
                'start_minute': rule[6],
                'end_relative_time': rule[7] if rule[7] is not None else 3600,
                'alarm_relative_time': rule[8] if rule[8] is not None else 0,
                'end_type': rule[9][0],
                'alarm_type': rule[9][1],
                'time_standard': standard,
            }

            sdate = _datetime.datetime(values['start_year'],
                                values['start_month_1'], values['start_day'],
                                values['start_hour'], values['start_minute'])

        values['end_relative_number'], values['end_relative_unit'] = \
                                    TimeSpanCtrl.compute_widget_values(
                                    values['end_relative_time'])

        # ralarm could be negative
        values['alarm_relative_number'], values['alarm_relative_unit'] = \
                                    TimeSpanCtrl.compute_widget_values(
                                    max((0, values['alarm_relative_time'])))

        rstart = values['start_hour'] * 3600 + values['start_minute'] * 60

        rrend = rstart + values['end_relative_time']
        values['end_next_day'] = False

        # End time could be set after 23:59 of the start day
        if rrend > 86399:
            rrend = rrend % 86400
            values['end_next_day'] = True

        rralarm = rstart - values['alarm_relative_time']
        values['alarm_previous_day'] = False

        # Alarm time could be set before 00:00 of the start day
        if rralarm < 0:
            rralarm = 86400 - abs(rralarm) % 86400
            values['alarm_previous_day'] = True

        values.update({
            'start_month': values['start_month_1'] - 1,
            'end_hour': rrend // 3600,
            'end_minute': rrend % 3600 // 60,
            'alarm_hour': rralarm // 3600,
            'alarm_minute': rralarm % 3600 // 60,
        })

        return values

    @staticmethod
    def _make_label(interval, refyear, month, day, rstartH, rstartM,
                rendH, rendM, ralarmH, ralarmM, rendn, rendu,
                ralarmn, ralarmu, endtype, alarmtype, fend, palarm, standard):
        label = 'Occur on {} {} at {}:{} ({}) every {} years (e.g. {})'.format(
                                day, DateHourCtrl.compute_month_label(month),
                                str(rstartH).zfill(2), str(rstartM).zfill(2),
                                standard, interval, refyear)

        if endtype == 1:
            label += ' for {} {}'.format(rendn, rendu)
        elif endtype == 2:
            label += ' until {}:{}'.format(str(rendH).zfill(2),
                                                           str(rendM).zfill(2))
            if fend:
                label += ' of the following day'

        if alarmtype == 1:
            label += ', activate alarm {} {} before'.format(ralarmn, ralarmu)
        elif alarmtype == 2:
            label += ', activate alarm at {}:{}'.format(
                                  str(ralarmH).zfill(2), str(ralarmM).zfill(2))
            if palarm:
                label += ' of the previous day'

        return label

    @staticmethod
    def create_random_rule():
        interval = random.randint(1, 3)
        refyear = random.randint(1990, 2020)
        month = random.randint(1, 12)

        while True:
            day = random.randint(1, 31)

            try:
                _datetime.date(refyear, month, day)
            except ValueError:
                continue
            else:
                break

        hour = random.randint(0, 23)
        minute = random.randint(0, 59)

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
            return organism_basicrules_api.make_occur_yearly_rule_local(
                                interval, refyear, month, day, hour, minute,
                                rend, ralarm, (endtype, alarmtype))
        else:
            return organism_basicrules_api.make_occur_yearly_rule_UTC(
                                interval, refyear, month, day, hour, minute,
                                rend, ralarm, (endtype, alarmtype))
