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
                                                (interface.StartTime,
                                                interface.EndTime,
                                                interface.AlarmTime,
                                                interface.Standard),
                                        self.original_values)

    def apply_rule(self, filename, id_):
        values = self.ui.get_values()
        rstart = values['start_relative_time']
        rstartH = values['start_hour']
        rstartM = values['start_minute']
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

        refstart = int(_time.time()) // 86400 * 86400 + rstart

        try:
            if standard == 'UTC':
                ruled = organism_basicrules_api.make_occur_regularly_rule_UTC(
                  refstart, 86400, rend, ralarm, ('1d', endtype, alarmtype))
            else:
                ruled = organism_basicrules_api.make_occur_regularly_rule_local(
                  refstart, 86400, rend, ralarm, ('1d', endtype, alarmtype))
        except organism_basicrules_api.BadRuleError:
            msgboxes.warn_bad_rule(msgboxes.generic).ShowModal()
        else:
            label = self._make_label(rstartH, rstartM, rendH, rendM, ralarmH,
                                    ralarmM, rendn, rendu, ralarmn, ralarmu,
                                    endtype, alarmtype, fend, palarm, standard)
            wxscheduler_api.apply_rule(filename, id_, ruled, label)

    @classmethod
    def insert_rule(cls, filename, id_, rule, rulev):
        standard = 'UTC' if rule['rule'] == 'occur_regularly_UTC' else 'local'
        values = cls._compute_values(standard, rulev)
        label = cls._make_label(values['start_hour'],
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
            rrstart = nextdate.hour * 3600
            refstart = int(_time.time()) // 86400 * 86400 + rrstart

            values = {
                'reference_start': refstart,
                'interval': 86400,
                'overlaps': 0,
                'bgap': 86400 - 3600,
                'end_relative_time': 3600,
                'alarm_relative_time': 0,
                'end_type': 0,
                'alarm_type': 0,
                'time_standard': standard,
            }
        else:
            values = {
                'reference_start': rule[0],
                'interval': rule[1],
                'overlaps': rule[2],
                'bgap': rule[3],
                'end_relative_time': rule[4] if rule[4] is not None else 3600,
                'alarm_relative_time': rule[5] if rule[5] is not None else 0,
                'end_type': rule[6][1],
                'alarm_type': rule[6][2],
                'time_standard': standard,
            }

            rrstart = values['reference_start'] % 86400

        values['end_relative_number'], values['end_relative_unit'] = \
                                TimeSpanCtrl.compute_widget_values(
                                values['end_relative_time'])

        # ralarm could be negative
        values['alarm_relative_number'], values['alarm_relative_unit'] = \
                                TimeSpanCtrl.compute_widget_values(
                                max((0, values['alarm_relative_time'])))

        rrend = rrstart + values['end_relative_time']
        values['end_next_day'] = False

        # End time could be set after 23:59 of the start day
        if rrend > 86399:
            rrend = rrend % 86400
            values['end_next_day'] = True

        rralarm = rrstart - values['alarm_relative_time']
        values['alarm_previous_day'] = False

        # Alarm time could be set before 00:00 of the start day
        if rralarm < 0:
            rralarm = 86400 - abs(rralarm) % 86400
            values['alarm_previous_day'] = True

        values.update({
            'start_hour': rrstart // 3600,
            'start_minute': rrstart % 3600 // 60,
            'end_hour': rrend // 3600,
            'end_minute': rrend % 3600 // 60,
            'alarm_hour': rralarm // 3600,
            'alarm_minute': rralarm % 3600 // 60,
        })

        return values

    @staticmethod
    def _make_label(rstartH, rstartM, rendH, rendM, ralarmH, ralarmM, rendn,
                                            rendu, ralarmn, ralarmu, endtype,
                                            alarmtype, fend, palarm, standard):
        label = 'Occur every day at {}:{} ({})'.format(str(rstartH).zfill(2),
                                            str(rstartM).zfill(2), standard)

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
        refstart = int((random.gauss(_time.time(), 15000)) // 60 * 60)

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
                     refstart, 86400, rend, ralarm, ('1d', endtype, alarmtype))
        else:
            return organism_basicrules_api.make_occur_regularly_rule_UTC(
                     refstart, 86400, rend, ralarm, ('1d', endtype, alarmtype))
