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

from outspline.static.pyaux import timeaux
from outspline.static.wxclasses.choices import WidgetChoiceCtrl
from outspline.static.wxclasses.timectrls import (HourCtrl, DateHourCtrl,
                    TimeSpanCtrl, WeekDayHourCtrl, WeekdaysCtrl, MonthsCtrl,
                    MonthDayHourCtrl, MonthInverseDayHourCtrl,
                    MonthWeekdayHourCtrl, MonthInverseWeekdayHourCtrl)
from outspline.static.wxclasses.misc import NarrowSpinCtrl
import outspline.plugins.wxscheduler_api as wxscheduler_api

# Temporary workaround for bug #332
import outspline.interfaces.wxgui_api as wxgui_api


class Interface(object):
    def __init__(self, parent, filename, id_, Widgets, input_values):
        self.input_values = input_values
        self.mpanel = wx.Panel(parent)

        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.mpanel.SetSizer(self.pbox)

        self.widgets = []

        for Widget in Widgets:
            widget = Widget(self.mpanel, self.input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)

            self.widgets.append(widget)
            self.pbox.Add(widget.get_main_window(), flag=wx.BOTTOM, border=4)

        wxscheduler_api.change_rule(filename, id_, self.mpanel)

        self._align_first_column()

    def _align_first_column(self):
        widths = []

        for widget in self.widgets:
            widths.append(widget.get_first_column_width())

        maxw = max(widths)

        for widget in self.widgets:
            widget.set_first_column_width(maxw)

        self.mpanel.Layout()

    def get_values(self):
        values = {}

        for widget in self.widgets:
            values.update(widget.get_values(values))

        return values


class WeekDays(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.dlabel = wx.StaticText(parent, label='Days:')
        self.box.Add(self.dlabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.daysw = WeekdaysCtrl(parent)
        self.daysw.set_days(input_values['selected_weekdays'])
        self.box.Add(self.daysw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.dlabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        dminh = self.dlabel.GetMinHeight()
        self.dlabel.SetMinSize((width, dminh))

    def get_values(self, values):
        return {'selected_weekdays': self.daysw.get_days()}


class Months(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.mlabel = wx.StaticText(parent, label='Months:')
        self.box.Add(self.mlabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.monthsw = MonthsCtrl(parent)
        self.monthsw.set_months(input_values['selected_months'])
        self.box.Add(self.monthsw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.mlabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        mminh = self.mlabel.GetMinHeight()
        self.mlabel.SetMinSize((width, mminh))

    def get_values(self, values):
        return {'selected_months': self.monthsw.get_months()}


class _StartDate(object):
    def __init__(self, parent, label, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.slabel = wx.StaticText(parent, label=label)
        self.box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.startw = DateHourCtrl(parent)
        self.startw.set_values(input_values['start_year'],
                               input_values['start_month'],
                               input_values['start_day'],
                               input_values['start_hour'],
                               input_values['start_minute'])
        self.box.Add(self.startw.get_main_panel())

        # Temporary workaround for bug #332
        # This widget is always placed at the top, so the previous
        #  Tab-traversal element is always the OK button
        wxgui_api.Bug332Workaround(self.startw.datectrl,
                            wxscheduler_api.work_around_bug332(filename, id_),
                            self.startw.hourctrl.hourctrl)

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.slabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((width, sminh))

    def get_values(self, values):
        start = self.startw.get_unix_time()
        utcoffset = timeaux.UTCOffset.compute2(start)
        ostart = self.startw.get_unix_time() - utcoffset

        return {'utc_offset': utcoffset,
                'start_unix_time': ostart,
                'start_relative_time': ostart % 86400,
                'start_year': self.startw.get_year(),
                'start_month': self.startw.get_month(),
                'start_day': self.startw.get_day(),
                'start_hour': self.startw.get_hour(),
                'start_minute': self.startw.get_minute()}


class StartDate(_StartDate):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(StartDate, self).__init__(parent, 'Start date:', input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class StartDateSample(_StartDate):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(StartDateSample, self).__init__(parent, 'Sample start:',
                                                                input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class StartTime(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.slabel = wx.StaticText(parent, label='Start time:')
        self.box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.startw = HourCtrl(parent)
        self.startw.set_values(input_values['start_hour'],
                               input_values['start_minute'])
        self.box.Add(self.startw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.slabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((width, sminh))

    def get_values(self, values):
        return {'start_relative_time': self.startw.get_relative_time(),
                'start_hour': self.startw.get_hour(),
                'start_minute': self.startw.get_minute()}


class StartWeekDay(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.slabel = wx.StaticText(parent, label='Start day:')
        self.box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.startw = WeekDayHourCtrl(parent)
        self.startw.set_values(input_values['start_weekday'],
                               input_values['start_hour'],
                               input_values['start_minute'])
        self.box.Add(self.startw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.slabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((width, sminh))

    def get_values(self, values):
        return {'start_relative_week_time':
                                    self.startw.get_relative_unix_week_time(),
                'start_relative_time': self.startw.get_relative_time(),
                'start_weekday': self.startw.get_day(),
                'start_hour': self.startw.get_hour(),
                'start_minute': self.startw.get_minute()}


class _StartMonthDay(object):
    def __init__(self, parent, Widget, input_values):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.slabel = wx.StaticText(parent, label='Start day:')
        self.box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.startw = Widget(parent)
        self.startw.set_values(input_values['start_day'],
                               input_values['start_hour'],
                               input_values['start_minute'])
        self.box.Add(self.startw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.slabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((width, sminh))

    def get_values(self, values):
        return {'start_relative_month_time':
                                        self.startw.get_relative_month_time(),
                'start_relative_time': self.startw.get_relative_time(),
                'start_day': self.startw.get_day(),
                'start_hour': self.startw.get_hour(),
                'start_minute': self.startw.get_minute()}


class StartMonthDay(_StartMonthDay):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(StartMonthDay, self).__init__(parent, MonthDayHourCtrl,
                                                                input_values)


class StartMonthDayInverse(_StartMonthDay):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(StartMonthDayInverse, self).__init__(parent,
                                        MonthInverseDayHourCtrl, input_values)


class _StartNthWeekDay(object):
    def __init__(self, parent, Widget, input_values):
        self.Widget = Widget

        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.slabel = wx.StaticText(parent, label='Start day:')
        self.box.Add(self.slabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.startw = Widget(parent)
        self.startw.set_values(input_values['start_weekday_number'],
                               input_values['start_weekday'],
                               input_values['start_hour'],
                               input_values['start_minute'])
        self.box.Add(self.startw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.slabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        sminh = self.slabel.GetMinHeight()
        self.slabel.SetMinSize((width, sminh))

    def get_values(self, values):
        rstartA = self.startw.get_weekday()

        return {'start_relative_time': self.startw.get_relative_time(),
                'start_weekday': rstartA,
                'start_weekday_number': self.startw.get_weekday_number(),
                'start_weekday_index':
                                    self.Widget.compute_weekday_label(rstartA),
                'start_hour': self.startw.get_hour(),
                'start_minute': self.startw.get_minute()}


class StartNthWeekDay(_StartNthWeekDay):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(StartNthWeekDay, self).__init__(parent, MonthWeekdayHourCtrl,
                                                                input_values)


class StartNthWeekDayInverse(_StartNthWeekDay):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(StartNthWeekDayInverse, self).__init__(parent,
                                    MonthInverseWeekdayHourCtrl, input_values)


class _End(object):
    def __init__(self, parent, mode, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        widgets = {0: (('No duration', None),
                       ('Duration:', self._create_duration_widget),
                       ('End date:', self._create_end_date_widget)),
                   1: (('End date:', self._create_end_date_widget),
                       ('Duration:', self._create_duration_widget)),
                   2: (('No duration', None),
                       ('Duration:', self._create_duration_widget),
                       ('Sample end:', self._create_end_date_widget)),
                   3: (('Sample end:', self._create_end_date_widget),
                       ('Duration:', self._create_duration_widget)),
                   4: (('No duration', None),
                       ('Duration:', self._create_duration_widget),
                       ('End time:', self._create_end_time_widget))}

        type_values = {0: (self._get_values_none,
                           self._get_values_duration,
                           self._get_values_date),
                       1: (self._get_values_date,
                           self._get_values_duration),
                       2: (self._get_values_none,
                           self._get_values_duration,
                           self._get_values_date),
                       3: (self._get_values_date,
                           self._get_values_duration),
                       4: (self._get_values_none,
                           self._get_values_duration,
                           self._get_values_time)}

        self.type_values = type_values[mode]

        self.input_values = input_values
        self.endchoicew = WidgetChoiceCtrl(parent, widgets[mode],
                                            self.input_values['end_type'], 4)
        self.endchoicew.force_update()

    def get_main_window(self):
        return self.endchoicew.get_main_panel()

    def _create_duration_widget(self):
        self.endw = TimeSpanCtrl(self.endchoicew.get_main_panel(), 1, 999)
        self.endw.set_values(self.input_values['end_relative_number'],
                             self.input_values['end_relative_unit'])

        return self.endw.get_main_panel()

    def _create_end_date_widget(self):
        self.endw = DateHourCtrl(self.endchoicew.get_main_panel())
        self.endw.set_values(self.input_values['end_year'],
                             self.input_values['end_month'],
                             self.input_values['end_day'],
                             self.input_values['end_hour'],
                             self.input_values['end_minute'])

        # Temporary workaround for bug #332
        wxgui_api.Bug332Workaround(self.endw.datectrl,
                                                self.endchoicew.choicectrl,
                                                self.endw.hourctrl.hourctrl)

        return self.endw.get_main_panel()

    def _create_end_time_widget(self):
        self.endw = HourCtrl(self.endchoicew.get_main_panel())
        self.endw.set_values(self.input_values['end_hour'],
                             self.input_values['end_minute'])

        return self.endw.get_main_panel()

    def get_first_column_width(self):
        return self.endchoicew.get_choice_width()

    def set_first_column_width(self, width):
        self.endchoicew.set_choice_min_width(width)

    def get_values(self, in_values):
        endtype = self.endchoicew.get_selection()
        values = {'end_type': endtype}
        values.update(self.type_values[endtype](in_values))

        return values

    def _get_values_none(self, in_values):
        return {'end_unix_time': None,
                'end_relative_time': None,
                'end_next_day': False,
                'end_relative_number': None,
                'end_relative_unit': None,
                'end_hour': None,
                'end_minute': None}

    def _get_values_duration(self, in_values):
        start = in_values.get('start_unix_time')
        rend = self.endw.get_time_span()

        try:
            end = start + rend
        except TypeError:
            end = None

        return {'end_unix_time': end,
                'end_relative_time': rend,
                'end_next_day': False,
                'end_relative_number': self.endw.get_number(),
                'end_relative_unit': self.endw.get_unit(),
                'end_hour': None,
                'end_minute': None}

    def _get_values_time(self, in_values):
        rstart = in_values['start_relative_time']

        endrt = self.endw.get_relative_time()

        # If time is set earlier than or equal to start, interpret it as
        # referring to the following day
        if endrt > rstart:
            rend = endrt - rstart
            fend = False
        else:
            rend = 86400 - rstart + endrt
            fend = True

        return {'end_unix_time': None,
                'end_relative_time': rend,
                'end_next_day': fend,
                'end_relative_number': None,
                'end_relative_unit': None,
                'end_hour': self.endw.get_hour(),
                'end_minute': self.endw.get_minute()}

    def _get_values_date(self, in_values):
        start = in_values['start_unix_time']
        utcoffset = in_values['utc_offset']

        end = self.endw.get_unix_time() - utcoffset

        return {'end_unix_time': end,
                'end_relative_time': end - start,
                'end_next_day': False,
                'end_relative_number': None,
                'end_relative_unit': None,
                'end_hour': None,
                'end_minute': None}


class EndDate(_End):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(EndDate, self).__init__(parent, 0, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class EndDate2(_End):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(EndDate2, self).__init__(parent, 1, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class EndDateSample(_End):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(EndDateSample, self).__init__(parent, 2, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class EndDateSample2(_End):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(EndDateSample2, self).__init__(parent, 3, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class EndTime(_End):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(EndTime, self).__init__(parent, 4, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class _Alarm(object):
    def __init__(self, parent, mode, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        widgets = {0: (('No alarm', None),
                       ('Alarm advance:', self._create_alarm_advance_widget),
                       ('Alarm date:', self._create_alarm_date_widget)),
                   1: (('No alarm', None),
                       ('Alarm advance:', self._create_alarm_advance_widget),
                       ('Sample alarm:', self._create_alarm_date_widget)),
                   2: (('No alarm', None),
                       ('Alarm advance:', self._create_alarm_advance_widget),
                       ('Alarm time:', self._create_alarm_time_widget))}

        type_values = {0: (self._get_values_none,
                           self._get_values_duration,
                           self._get_values_date),
                       1: (self._get_values_none,
                           self._get_values_duration,
                           self._get_values_date),
                       2: (self._get_values_none,
                           self._get_values_duration,
                           self._get_values_time)}

        self.type_values = type_values[mode]

        self.input_values = input_values
        self.alarmchoicew = WidgetChoiceCtrl(parent, widgets[mode],
                                            self.input_values['alarm_type'], 4)
        self.alarmchoicew.force_update()

    def get_main_window(self):
        return self.alarmchoicew.get_main_panel()

    def _create_alarm_advance_widget(self):
        self.alarmw = TimeSpanCtrl(self.alarmchoicew.get_main_panel(), 0, 999)
        self.alarmw.set_values(self.input_values['alarm_relative_number'],
                               self.input_values['alarm_relative_unit'])

        return self.alarmw.get_main_panel()

    def _create_alarm_date_widget(self):
        self.alarmw = DateHourCtrl(self.alarmchoicew.get_main_panel())
        self.alarmw.set_values(self.input_values['alarm_year'],
                               self.input_values['alarm_month'],
                               self.input_values['alarm_day'],
                               self.input_values['alarm_hour'],
                               self.input_values['alarm_minute'])

        # Temporary workaround for bug #332
        wxgui_api.Bug332Workaround(self.alarmw.datectrl,
                                                self.alarmchoicew.choicectrl,
                                                self.alarmw.hourctrl.hourctrl)

        return self.alarmw.get_main_panel()

    def _create_alarm_time_widget(self):
        self.alarmw = HourCtrl(self.alarmchoicew.get_main_panel())
        self.alarmw.set_values(self.input_values['alarm_hour'],
                               self.input_values['alarm_minute'])

        return self.alarmw.get_main_panel()

    def get_first_column_width(self):
        return self.alarmchoicew.get_choice_width()

    def set_first_column_width(self, width):
        self.alarmchoicew.set_choice_min_width(width)

    def get_values(self, in_values):
        alarmtype = self.alarmchoicew.get_selection()
        values = {'alarm_type': alarmtype}
        values.update(self.type_values[alarmtype](in_values))

        return values

    def _get_values_none(self, in_values):
        return {'alarm_unix_time': None,
                'alarm_relative_time': None,
                'alarm_previous_day': False,
                'alarm_relative_number': None,
                'alarm_relative_unit': None,
                'alarm_hour': None,
                'alarm_minute': None}

    def _get_values_duration(self, in_values):
        start = in_values.get('start_unix_time')
        ralarm = self.alarmw.get_time_span()

        try:
            alarm = start - ralarm
        except TypeError:
            alarm = None

        return {'alarm_unix_time': alarm,
                'alarm_relative_time': ralarm,
                'alarm_previous_day': False,
                'alarm_relative_number': self.alarmw.get_number(),
                'alarm_relative_unit': self.alarmw.get_unit(),
                'alarm_hour': None,
                'alarm_minute': None}

    def _get_values_time(self, in_values):
        rstart = in_values['start_relative_time']

        alarmrt = self.alarmw.get_relative_time()

        # If time is set later than start, interpret it as referring to the
        # previous day
        if alarmrt <= rstart:
            ralarm = rstart - alarmrt
            palarm = False
        else:
            ralarm = 86400 - alarmrt + rstart
            palarm = True

        return {'alarm_unix_time': None,
                'alarm_relative_time': ralarm,
                'alarm_previous_day': palarm,
                'alarm_relative_number': None,
                'alarm_relative_unit': None,
                'alarm_hour': self.alarmw.get_hour(),
                'alarm_minute': self.alarmw.get_minute()}

    def _get_values_date(self, in_values):
        start = in_values['start_unix_time']
        utcoffset = in_values['utc_offset']

        alarm = self.alarmw.get_unix_time() - utcoffset

        return {'alarm_unix_time': alarm,
                'alarm_relative_time': start - alarm,
                'alarm_previous_day': False,
                'alarm_relative_number': None,
                'alarm_relative_unit': None,
                'alarm_hour': None,
                'alarm_minute': None}


class AlarmDate(_Alarm):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(AlarmDate, self).__init__(parent, 0, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class AlarmDateSample(_Alarm):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(AlarmDateSample, self).__init__(parent, 1, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class AlarmTime(_Alarm):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        super(AlarmTime, self).__init__(parent, 2, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_)


class Interval(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.ilabel = wx.StaticText(parent, label='Interval time:')
        self.box.Add(self.ilabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.intervalw = TimeSpanCtrl(parent, 1, 999)
        self.intervalw.set_values(input_values['interval_number'],
                                  input_values['interval_unit'])
        self.box.Add(self.intervalw.get_main_panel())

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.ilabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        iminh = self.ilabel.GetMinHeight()
        self.ilabel.SetMinSize((width, iminh))

    def get_values(self, values):
        return {'interval': self.intervalw.get_time_span(),
                'interval_number': self.intervalw.get_number(),
                'interval_unit': self.intervalw.get_unit()}


class IntervalYears(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.ilabel = wx.StaticText(parent, label='Interval (years):')
        self.box.Add(self.ilabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.intervalw = NarrowSpinCtrl(parent, min=1, max=99,
                                                        style=wx.SP_ARROW_KEYS)
        self.intervalw.SetValue(input_values['interval_years'])
        self.box.Add(self.intervalw, flag=wx.ALIGN_CENTER_VERTICAL)

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.ilabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        iminh = self.ilabel.GetMinHeight()
        self.ilabel.SetMinSize((width, iminh))

    def get_values(self, values):
        return {'interval_years': self.intervalw.GetValue()}


class Inclusive(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.inclusivew = wx.CheckBox(parent, label='Inclusive')
        self.inclusivew.SetValue(input_values['inclusive'])

    def get_main_window(self):
        return self.inclusivew

    def get_first_column_width(self):
        return 0

    def set_first_column_width(self, width):
        pass

    def get_values(self, values):
        return {'inclusive': self.inclusivew.GetValue()}


class Standard(object):
    def __init__(self, parent, input_values,
                                            # Temporary workaround for bug #332
                                            filename, id_):
        self.box = wx.BoxSizer(wx.HORIZONTAL)

        self.zlabel = wx.StaticText(parent, label='Time standard:')
        self.box.Add(self.zlabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                      border=4)

        self.standardw_local = wx.RadioButton(parent, label='local',
                                                            style=wx.RB_GROUP)
        self.box.Add(self.standardw_local, flag=wx.RIGHT, border=4)

        self.standardw_utc = wx.RadioButton(parent, label='UTC')
        self.box.Add(self.standardw_utc)

        if input_values['time_standard'] == 'UTC':
            self.standardw_utc.SetValue(True)
        else:
            self.standardw_local.SetValue(True)

    def get_main_window(self):
        return self.box

    def get_first_column_width(self):
        return self.zlabel.GetSizeTuple()[0]

    def set_first_column_width(self, width):
        zminh = self.zlabel.GetMinHeight()
        self.zlabel.SetMinSize((width, zminh))

    def get_values(self, values):
        return {'time_standard': 'UTC' if self.standardw_utc.GetValue() else \
                                                                    'local'}
