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
import time as _time
import datetime as _datetime
import copy as copy_
from collections import OrderedDict

from outspline.static.pyaux import timeaux
from outspline.static.wxclasses.choices import WidgetChoiceCtrl
from outspline.static.wxclasses.timectrls import DateHourCtrl, TimeSpanCtrl
from outspline.static.wxclasses.misc import NarrowSpinCtrl

import outspline.coreaux_api as coreaux_api
import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.interfaces.wxgui_api as wxgui_api

from exceptions import OutOfRangeError


class Navigator(object):
    def __init__(self, tasklist):
        # tasklist.list_ hasn't been instantiated yet here
        self.tasklist = tasklist
        self.parent = tasklist.panel
        self.panel = wx.Panel(self.parent)
        self.fbox = wx.WrapSizer(orient=wx.HORIZONTAL)
        self.panel.SetSizer(self.fbox)


        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

        self.limits = (self.config.get_int('minimum_year'),
                                        self.config.get_int('maximum_year'))

        self.configuration = FilterConfiguration(self.limits)

        self._init_buttons()
        self._init_filter()

        if self.config.get_bool('show_navigator'):
            self._show()

    def _init_buttons(self):
        buttons = self.config['navigator_buttons'].split(',')

        creators = {
            'previous': self._init_button_previous,
            'next': self._init_button_next,
            'reset': self._init_button_reset,
            'set': self._init_button_set,
            'apply': self._init_button_apply,
        }

        for button in buttons:
            try:
                creators[button]()
            except KeyError:
                pass

    def _init_button_previous(self):
        button_previous = wx.Button(self.panel, label='<',
                                                        style=wx.BU_EXACTFIT)
        self.fbox.Add(button_previous, flag=wx.EXPAND | wx.BOTTOM, border=4)

        # Use spacers instead of margins: a spacer will be ignored by the
        # WrapSizer if the next item wraps
        self.fbox.AddSpacer(4)

        self.panel.Bind(wx.EVT_BUTTON, self._show_previous_page,
                                                            button_previous)

    def _init_button_next(self):
        button_next = wx.Button(self.panel, label='>', style=wx.BU_EXACTFIT)
        self.fbox.Add(button_next, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.fbox.AddSpacer(4)

        self.panel.Bind(wx.EVT_BUTTON, self._show_next_page, button_next)

    def _init_button_reset(self):
        button_reset = wx.Button(self.panel, label='Reset',
                                                        style=wx.BU_EXACTFIT)
        self.fbox.Add(button_reset, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.fbox.AddSpacer(4)

        self.panel.Bind(wx.EVT_BUTTON, self._reset, button_reset)

    def _init_button_set(self):
        button_set = wx.Button(self.panel, label='Set', style=wx.BU_EXACTFIT)
        self.fbox.Add(button_set, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.fbox.AddSpacer(4)

        self.panel.Bind(wx.EVT_BUTTON, self._set, button_set)

    def _init_button_apply(self):
        button_apply = wx.Button(self.panel, label='Apply',
                                                        style=wx.BU_EXACTFIT)
        self.fbox.Add(button_apply, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.fbox.AddSpacer(4)

        self.panel.Bind(wx.EVT_BUTTON, self._apply, button_apply)

    def _init_filter(self):
        self.choice = wx.Choice(self.panel, choices=())

        self.choice.Append("Relative", clientData=FilterInterfaceRelative)
        self.choice.Append("Date", clientData=FilterInterfaceDate)
        self.choice.Append("Month", clientData=FilterInterfaceMonth)

        self.fbox.Add(self.choice, flag=wx.BOTTOM, border=4)

        self.fbox.AddSpacer(4)

        config = self.configuration.get_saved()
        choice = self._set_filter_selection(config)

        self.sfilter = self.choice.GetClientData(choice)(self.panel,
                                                        self.limits, config)
        self.fbox.Add(self.sfilter.panel, flag=wx.BOTTOM, border=4)
        self.parent.Layout()

        self.panel.Bind(wx.EVT_CHOICE, self._handle_filter_choice, self.choice)

    def _handle_filter_choice(self, event):
        self._show_filter(event.GetInt(),
                    self.configuration.get_current_or_default(event.GetInt()))

    def _show_filter(self, choice, config):
        fpanel = self.choice.GetClientData(choice)(self.panel, self.limits,
                                                                        config)
        self.fbox.Replace(self.sfilter.panel, fpanel.panel)
        self.sfilter.panel.Destroy()
        self.sfilter = fpanel
        self.parent.Layout()

    def _set_filter_selection(self, config):
        choice = {'relative': 0, 'date': 1, 'month': 2}[config['mode']]
        self.choice.SetSelection(choice)
        return choice

    def _reset_filter(self, config):
        choice = self._set_filter_selection(config)
        self._show_filter(choice, config)

    def _apply_filter(self, config):
        try:
            self.tasklist.list_.set_filter(config)
        except OutOfRangeError:
            self.tasklist.list_.warn_out_of_range()
        else:
            self.tasklist.list_.refresh()

    def _show_previous_page(self, event):
        self.show_previous_page()

    def show_previous_page(self):
        cconfig = self.configuration.get_current()

        try:
            nconfig = self.configuration.compute_previous_configuration(
                                                                    cconfig)
        except OutOfRangeError:
            self.tasklist.list_.warn_out_of_range()
        else:
            self._reset_filter(nconfig)
            self._show_filter(self.choice.GetSelection(), nconfig)
            self._apply_filter(nconfig)

    def _show_next_page(self, event):
        self.show_next_page()

    def show_next_page(self):
        cconfig = self.configuration.get_current()

        try:
            nconfig = self.configuration.compute_next_configuration(cconfig)
        except OutOfRangeError:
            self.tasklist.list_.warn_out_of_range()
        else:
            self._reset_filter(nconfig)
            self._show_filter(self.choice.GetSelection(), nconfig)
            self._apply_filter(nconfig)

    def _reset(self, event):
        self.reset()

    def reset(self):
        config = self.configuration.restore_saved()
        self._reset_filter(config)
        self._apply_filter(config)

    def _set(self, event):
        self.set()

    def set(self):
        # Note that the configuration is exported to the file only when exiting
        # Outspline
        intvalues = self.sfilter.get_values()

        try:
            config = self.configuration.set_current_from_interface(intvalues)
        except OutOfRangeError:
            self.tasklist.list_.warn_out_of_range()
        else:
            self._apply_filter(config)

            # Store *after* applying the filter, i.e. after setting the current
            # values
            self.configuration.set_saved()

    def _apply(self, event):
        self.apply()

    def apply(self):
        intvalues = self.sfilter.get_values()

        try:
            config = self.configuration.set_current_from_interface(intvalues)
        except OutOfRangeError:
            self.tasklist.list_.warn_out_of_range()
        else:
            self._apply_filter(config)

    def _show(self):
        self.parent.GetSizer().Prepend(self.panel, flag=wx.EXPAND)
        # Show explicitly because self._hide has to hide it
        self.panel.Show()
        self.parent.GetSizer().Layout()

    def _hide(self):
        self.parent.GetSizer().Detach(self.panel)
        # Also hide, otherwise the border of the buttons will still be visible
        # at the top of the tasklist, see #318
        self.panel.Hide()
        self.parent.GetSizer().Layout()

    def is_shown(self):
        return self.panel.GetContainingSizer() is not None

    def toggle_shown(self):
        if self.is_shown():
            self._hide()
        else:
            self._show()

    def get_current_configuration(self):
        return self.configuration.get_current()

    def get_default_configuration(self):
        return self.configuration.get_default()

    def save_configuration(self):
        self.config['show_navigator'] = 'yes' if self.is_shown() else 'no'
        self.configuration.clear_on_file()


class FilterConfiguration(object):
    def __init__(self, limits):
        self.section = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                            'DefaultFilter')

        self.modes_to_filters = {
            'relative': FilterConfigurationRelative(limits),
            'date': FilterConfigurationDate(limits),
            'month': FilterConfigurationMonth(limits),
        }

        options = self.section.get_options()
        self.filterconf = self.modes_to_filters[options['mode']]

        try:
            self.saved = self.filterconf.compute_from_file(options)
        except OutOfRangeError:
            self.saved = self.filterconf.get_defaults()

        self.current = copy_.deepcopy(self.saved)

    def _set_current(self, config):
        self.current = config
        self.filterconf = self.modes_to_filters[self.current['mode']]

    def set_current_from_interface(self, intvalues):
        self.filterconf = self.modes_to_filters[intvalues['mode']]
        config = self.filterconf.compute_from_interface(intvalues)
        self.current = config
        return config

    def get_current(self):
        return self.current

    def get_default(self):
        return self.filterconf.get_defaults()

    def get_current_or_default(self, choice):
        mode = ('relative', 'date', 'month')[choice]

        if self.current['mode'] == mode:
            return self.current
        else:
            return self.modes_to_filters[mode].get_defaults()

    def set_saved(self):
        self.saved = copy_.deepcopy(self.current)
        self.section.reset(self.filterconf.compose_for_file(self.saved))

    def restore_saved(self):
        self._set_current(self.saved)
        return self.saved

    def get_saved(self):
        return self.saved

    def compute_next_configuration(self, config):
        nconfig = self.filterconf.compute_adjacent(config, 1)
        self._set_current(nconfig)
        return nconfig

    def compute_previous_configuration(self, config):
        nconfig = self.filterconf.compute_adjacent(config, -1)
        self._set_current(nconfig)
        return nconfig

    def clear_on_file(self):
        # The DefaultFilter section must be reset (not simply upgraded) in the
        # configuration file, otherwise the old options will be left
        self.section.export_reset(coreaux_api.get_user_config_file())


class FilterConfigurationRelative(object):
    def __init__(self, limits):
        self.limits = limits
        self.units = ('minutes', 'hours', 'days', 'weeks', 'months', 'years')
        self.default = {
            'mode': 'relative',
            # The default value in the .config file is -5, but setting the same
            # here would feel weird when changing filters, and also a similar
            # thing as for 'high' should be done, otherwise also units like
            # years would take a low of -5, which would be bad
            'low': {0: 0,
                    1: 0,
                    2: 0,
                    3: 0,
                    4: 0,
                    5: 0},
            'high': {'to':
                        {0: 1439,
                         1: 23,
                         2: 0,
                         3: 0,
                         4: 0,
                         5: 0},
                     'for':
                        {0: 1440,
                         1: 24,
                         2: 1,
                         3: 1,
                         4: 1,
                         5: 1},
                    },
            'type': 'to',
            'unit': 'minutes',
            'uniti': 0,
        }

    def _compute(self, low, high, type_, unit):
        if type_ == 'to':
            limits = [low, high]
            limits.sort()
            low, high = limits

        config = copy_.deepcopy(self.default)
        uniti = self.units.index(unit)

        config.update({
            'type': type_,
            'unit': unit,
            'uniti': uniti,
        })

        config['low'][uniti] = low
        config['high'][config['type']][uniti] = high

        return config

    def compute_from_file(self, fileconfig):
        return self._compute(int(fileconfig['low']), int(fileconfig['high']),
                                        fileconfig['type'], fileconfig['unit'])

    def compute_from_interface(self, intvalues):
        return self._compute(intvalues['low'], intvalues['high'],
                            intvalues['type'], self.units[intvalues['uniti']])

    def get_defaults(self):
        return self.default

    def compute_adjacent(self, cconfig, mode):
        nconfig = copy_.deepcopy(cconfig)
        uniti = cconfig['uniti']

        if cconfig['type'] == 'for':
            nconfig['low'][uniti] = cconfig['low'][uniti] + \
                                cconfig['high'][cconfig['type']][uniti] * mode
        else:
            span = cconfig['high'][cconfig['type']][uniti] - \
                                                    cconfig['low'][uniti] + 1
            nconfig['low'][uniti] = cconfig['low'][uniti] + span * mode
            nconfig['high'][cconfig['type']][uniti] = \
                        cconfig['high'][cconfig['type']][uniti] + span * mode

        return nconfig

    def compose_for_file(self, config):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        return OrderedDict((
            ('mode', config['mode']),
            ('low', str(config['low'][config['uniti']])),
            ('high', str(config['high'][config['type']][config['uniti']])),
            ('type', config['type']),
            ('unit', config['unit']),
        ))


class FilterConfigurationDate(object):
    def __init__(self, limits):
        self.limits = limits
        self.default = {
            'mode': 'date',
            'lowdate': None,
            'highdate': None,
            'type': 'for',
            'span': 1,
            'unit': 'days',
        }

    def _compute(self, lowdate, highdate, type_, unit):
        limits = [lowdate, highdate]
        # Always sort, even if type is "for", in fact the span is always
        # computed in this case
        limits.sort()
        lowdate, highdate = limits

        return {
            'mode': 'date',
            'lowdate': lowdate,
            'highdate': highdate,
            'type': type_,
            # Add 1 day because the stored high date is included in the
            # range
            'span': self._compute_span(lowdate, highdate, unit),
            'unit': unit,
        }

    def _compute_span(self, lowdate, highdate, unit):
        days = (highdate + _datetime.timedelta(days=1) - lowdate).days

        if unit == 'weeks':
            return days // 7
        else:
            return days

    def compute_from_file(self, fileconfig):
        lowdate = _datetime.datetime.strptime(fileconfig['lowdate'],
                                                                    '%Y-%m-%d')
        highdate = _datetime.datetime.strptime(fileconfig['highdate'],
                                                                    '%Y-%m-%d')

        if self.limits[0] <= lowdate.year <= self.limits[1] and \
                            self.limits[0] <= highdate.year <= self.limits[1]:
            return self._compute(lowdate, highdate, fileconfig['type'],
                                                            fileconfig['unit'])
        else:
            raise OutOfRangeError()

    def compute_from_interface(self, intvalues):
        # The values are already sanitized by the date widgets
        ld = intvalues['lowdate']
        lowdate = _datetime.datetime(year=ld.GetYear(),
                                    month=ld.GetMonth() + 1, day=ld.GetDay())
        type_ = intvalues['type']

        if type_ == 'to':
            hd = intvalues['highdate']
            highdate = _datetime.datetime(year=hd.GetYear(),
                                    month=hd.GetMonth() + 1, day=hd.GetDay())
            unit = 'days'
            return self._compute(lowdate, highdate, type_, unit)
        else:
            unit = intvalues['unit']
            span = intvalues['number']

            if unit == 'weeks':
                spand = _datetime.timedelta(weeks=span)
            else:
                spand = _datetime.timedelta(days=span)

            try:
                # Subtract 1 day because the stored high date is included in
                # the range
                highdate = lowdate + spand - _datetime.timedelta(days=1)
            except OverflowError:
                raise OutOfRangeError()

            return {
                'mode': 'date',
                'lowdate': lowdate,
                'highdate': highdate,
                'type': type_,
                # Add 1 day because the stored high date is included in the
                # range
                'span': span,
                'unit': unit,
            }

    def get_defaults(self):
        config = copy_.deepcopy(self.default)
        today = _datetime.date.today()

        config.update({
            'lowdate': today,
            # Still use today because the stored high date is included in
            # the range
            'highdate': today,
        })

        return config

    def compute_adjacent(self, cconfig, mode):
        nconfig = copy_.deepcopy(cconfig)

        lowdate = cconfig['lowdate']
        highdate = cconfig['highdate']
        delta = highdate + _datetime.timedelta(days=1) - lowdate

        try:
            if mode > 0:
                lowdate += delta
                highdate += delta
            else:
                lowdate -= delta
                highdate -= delta
        except OverflowError:
            raise OutOfRangeError()

        if lowdate.year >= self.limits[0] and highdate.year <= self.limits[1]:
            nconfig.update({
                'lowdate': lowdate,
                'highdate': highdate,
            })

            return nconfig
        else:
            raise OutOfRangeError()

    def compose_for_file(self, config):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        return OrderedDict((
            ('mode', config['mode']),
            ('lowdate', config['lowdate'].strftime('%Y-%m-%d')),
            ('highdate', config['highdate'].strftime('%Y-%m-%d')),
            ('type', config['type']),
            ('unit', config['unit']),
        ))


class FilterConfigurationMonth(object):
    def __init__(self, limits):
        self.limits = limits
        self.default = {
            'mode': 'month',
            'lowyear': 2011,
            'lowmonth0': 0,
            # Still use today because the stored high date is included in
            # the range
            'highyear': 2011,
            'highmonth0': 0,
            'type': 'for',
            'span': 1,
            'unit': 'months',
        }

    def _compute(self, lowyear, lowmonth0, highyear, highmonth0, type_, unit):
        if lowyear < highyear or (lowyear == highyear and
                                                    lowmonth0 <= highmonth0):
            slowyear = lowyear
            slowmonth0 = lowmonth0
            shighyear = highyear
            shighmonth0 = highmonth0
        else:
            slowyear = highyear
            slowmonth0 = highmonth0
            shighyear = lowyear
            shighmonth0 = lowmonth0

        span = self._compute_span(slowmonth0, slowyear, shighmonth0, shighyear,
                                                                        unit)

        return {
            'mode': 'month',
            'lowyear': slowyear,
            'lowmonth0': slowmonth0,
            'highyear': shighyear,
            'highmonth0': shighmonth0,
            'type': type_,
            'span': span,
            'unit': unit,
        }

    def _compute_span(self, lowmonth0, lowyear, highmonth0, highyear, unit):
        # Add 1 month because the stored high date is included in the range
        months = (13 - lowmonth0) + (highyear - lowyear - 1) * 12 + highmonth0

        if unit == 'years':
            return months // 12
        else:
            return months

    def compute_from_file(self, fileconfig):
        lowyear = int(fileconfig['lowyear'])
        lowmonth0 = int(fileconfig['lowmonth']) - 1
        highyear = int(fileconfig['highyear'])
        highmonth0 = int(fileconfig['highmonth']) - 1

        if self.limits[0] <= lowyear <= self.limits[1] and \
                                self.limits[0] <= highyear <= self.limits[1]:
            return self._compute(lowyear, lowmonth0, highyear, highmonth0,
                                        fileconfig['type'], fileconfig['unit'])
        else:
            raise OutOfRangeError()

    def compute_from_interface(self, intvalues):
        # The values are already sanitized by the date widgets
        lowyear = intvalues['lowyear']
        lowmonth0 = intvalues['lowmonth0']
        type_ = intvalues['type']

        if type_ == 'to':
            highyear = intvalues['highyear']
            highmonth0 = intvalues['highmonth0']
            unit = 'months'
            return self._compute(lowyear, lowmonth0, highyear, highmonth0,
                                                                type_, unit)
        else:
            unit = intvalues['unit']
            span = intvalues['number']

            if unit == 'years':
                if lowmonth0 > 0:
                    highyear = lowyear + span
                    # Subtract 1 month because the stored high date is included
                    # in the range
                    highmonth0 = lowmonth0 - 1
                else:
                    highyear = lowyear + span - 1
                    # Subtract 1 month because the stored high date is included
                    # in the range
                    highmonth0 = 11
            else:
                # Subtract 1 month because the stored high date is included in
                # the range
                tempmonth0 = lowmonth0 - 1 + span
                yspan, highmonth0 = divmod(tempmonth0, 12)
                highyear = lowyear + yspan

            return {
                'mode': 'month',
                'lowyear': lowyear,
                'lowmonth0': lowmonth0,
                'highyear': highyear,
                'highmonth0': highmonth0,
                'type': type_,
                'span': span,
                'unit': unit,
            }

    def get_defaults(self):
        config = copy_.deepcopy(self.default)
        today = _datetime.date.today()

        config.update({
            'lowyear': today.year,
            'lowmonth0': today.month - 1,
            # Still use today because the stored high date is included in
            # the range
            'highyear': today.year,
            'highmonth0': today.month - 1,
        })

        return config

    def compute_adjacent(self, cconfig, mode):
        nconfig = copy_.deepcopy(cconfig)

        span = cconfig['span']

        if cconfig['unit'] == 'years':
            span *= 12

        rlyear, nconfig['lowmonth0'] = divmod(cconfig['lowmonth0'] +
                                                            span * mode, 12)
        rhyear, nconfig['highmonth0'] = divmod(cconfig['highmonth0'] +
                                                            span * mode, 12)

        nconfig['lowyear'] = cconfig['lowyear'] + rlyear
        nconfig['highyear'] = cconfig['highyear'] + rhyear

        if nconfig['lowyear'] >= self.limits[0] and \
                                        nconfig['highyear'] <= self.limits[1]:
            return nconfig
        else:
            raise OutOfRangeError()

    def compose_for_file(self, config):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        return OrderedDict((
            ('mode', config['mode']),
            ('lowyear', str(config['lowyear'])),
            ('lowmonth', str(config['lowmonth0'] + 1)),
            ('highyear', str(config['highyear'])),
            ('highmonth', str(config['highmonth0'] + 1)),
            ('type', config['type']),
            ('unit', config['unit']),
        ))


class FilterInterfaceRelative(object):
    def __init__(self, parent, limits, config):
        self.limits = limits
        self.units = ('minutes', 'hours', 'days', 'weeks', 'months', 'years')
        self.config = config

        self.panel = wx.Panel(parent)
        self.fbox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.fbox)

        lowlabel = wx.StaticText(self.panel, label='From')
        self.fbox.Add(lowlabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.lowlimit = NarrowSpinCtrl(self.panel, min=-9999, max=9999,
                                                        style=wx.SP_ARROW_KEYS)
        self.lowlimit.SetValue(self.config['low'][self.config['uniti']])
        self.fbox.Add(self.lowlimit, flag=wx.ALIGN_CENTER_VERTICAL |
                                                            wx.RIGHT, border=4)

        self.unitchoice = wx.Choice(self.panel, choices=self.units)
        self.unitchoice.SetSelection(self.config['uniti'])
        self.panel.Bind(wx.EVT_CHOICE, self._handle_choice, self.unitchoice)
        # unitchoice must be created before highchoice, but added to the sizer
        # after

        choice = ('to', 'for').index(self.config['type'])
        # Use layout_ancestors=3 because 2 makes the sizer expand to the right
        # if the new widgets need more room, and 3 adds/removes a row if the
        # window is too narrow
        self.highchoice = WidgetChoiceCtrl(self.panel, (
                                            ('to', self._create_to_widget),
                                            ('for', self._create_for_widget)),
                                            choice, 4, layout_ancestors=3)
        self.highchoice.force_update()
        self.fbox.Add(self.highchoice.get_main_panel(),
                            flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        # unitchoice must be created before highchoice, but added to the sizer
        # after
        self.fbox.Add(self.unitchoice, flag=wx.ALIGN_CENTER_VERTICAL)

    def _handle_choice(self, event):
        self.lowlimit.SetValue(self.config['low'][event.GetInt()])
        self.highlimit.SetValue(
                self.config['high'][self._get_high_choice()][event.GetInt()])

    def _create_to_widget(self):
        self.highlimit = NarrowSpinCtrl(self.highchoice.get_main_panel(),
                                min=-9999, max=9999, style=wx.SP_ARROW_KEYS)
        self.highlimit.SetValue(self.config['high'][self._get_high_choice()][
                                            self.unitchoice.GetSelection()])

        return self.highlimit

    def _create_for_widget(self):
        self.highlimit = NarrowSpinCtrl(self.highchoice.get_main_panel(),
                                    min=1, max=9999, style=wx.SP_ARROW_KEYS)
        self.highlimit.SetValue(self.config['high'][self._get_high_choice()][
                                            self.unitchoice.GetSelection()])

        return self.highlimit

    def _get_high_choice(self):
        return ('to', 'for')[self.highchoice.get_selection()]

    def get_values(self):
        values = {
            'mode': 'relative',
            'type': self._get_high_choice(),
            'uniti': self.unitchoice.GetSelection(),
            'low': self.lowlimit.GetValue(),
            'high': self.highlimit.GetValue(),
        }

        return values


class FilterInterfaceDate(object):
    def __init__(self, parent, limits, config):
        self.limits = limits
        self.config = config

        self.panel = wx.Panel(parent)
        self.fbox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.fbox)

        lowlabel = wx.StaticText(self.panel, label='From')
        self.fbox.Add(lowlabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.lowdate = wx.DatePickerCtrl(self.panel)
        sdate = wx.DateTime()
        lowdate = self.config['lowdate']
        sdate.Set(year=lowdate.year, month=lowdate.month - 1, day=lowdate.day)
        self.lowdate.SetValue(sdate)
        ldate = wx.DateTime()
        hdate = wx.DateTime()
        ldate.Set(year=self.limits[0], month=0, day=1)
        hdate.Set(year=self.limits[1], month=11, day=31)
        self.lowdate.SetRange(ldate, hdate)
        self.fbox.Add(self.lowdate, flag=wx.ALIGN_CENTER_VERTICAL |
                                                            wx.RIGHT, border=4)

        choice = ('for', 'to').index(self.config['type'])
        # Use layout_ancestors=3 because 2 makes the sizer expand to the right
        # if the new widgets need more room, and 3 adds/removes a row if the
        # window is too narrow
        self.highchoice = WidgetChoiceCtrl(self.panel, (
                                            ('for', self._create_for_widget),
                                            ('to', self._create_to_widget)),
                                            choice, 4, layout_ancestors=3)
        self.highchoice.force_update()
        self.fbox.Add(self.highchoice.get_main_panel(),
                                                flag=wx.ALIGN_CENTER_VERTICAL)

    def _create_for_widget(self):
        panel = wx.Panel(self.highchoice.get_main_panel())
        box = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(box)

        self.highlimit = NarrowSpinCtrl(panel,
                                    min=1, max=999, style=wx.SP_ARROW_KEYS)
        self.highlimit.SetValue(self.config['span'])
        box.Add(self.highlimit, flag=wx.ALIGN_CENTER_VERTICAL |
                                                            wx.RIGHT, border=4)

        self.unitchoice = wx.Choice(panel, choices=('days', 'weeks'))
        self.unitchoice.SetSelection(self.unitchoice.FindString(
                                                        self.config['unit']))
        box.Add(self.unitchoice, flag=wx.ALIGN_CENTER_VERTICAL)

        return panel

    def _create_to_widget(self):
        self.highdate = wx.DatePickerCtrl(self.highchoice.get_main_panel())
        sdate = wx.DateTime()
        highdate = self.config['highdate']
        sdate.Set(year=highdate.year, month=highdate.month - 1,
                                                            day=highdate.day)
        self.highdate.SetValue(sdate)
        ldate = wx.DateTime()
        hdate = wx.DateTime()
        ldate.Set(year=self.limits[0], month=0, day=1)
        hdate.Set(year=self.limits[1], month=11, day=31)
        self.highdate.SetRange(ldate, hdate)

        return self.highdate

    def get_values(self):
        values = {
            'mode': 'date',
            'lowdate': self.lowdate.GetValue()
        }

        if self.highchoice.get_selection() == 1:
            values.update({
                'type': 'to',
                'highdate': self.highdate.GetValue(),
            })
        else:
            values.update({
                'type': 'for',
                'number': self.highlimit.GetValue(),
                # GetString returns a unicode object, it's necessary to convert
                # it into a normal string because the configfile module doesn't
                # support unicode objects
                'unit': str(self.unitchoice.GetString(
                                            self.unitchoice.GetSelection())),
            })

        return values


class FilterInterfaceMonth(object):
    def __init__(self, parent, limits, config):
        self.limits = limits
        self.config = config

        self.panel = wx.Panel(parent)
        self.fbox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.fbox)

        lowlabel = wx.StaticText(self.panel, label='From')
        self.fbox.Add(lowlabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.lowmonth = wx.Choice(self.panel, choices=('January',
                           'February', 'March', 'April', 'May', 'June', 'July',
                     'August', 'September', 'October', 'November', 'December'))
        self.lowmonth.SetSelection(self.config['lowmonth0'])
        self.fbox.Add(self.lowmonth, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.lowyear = NarrowSpinCtrl(self.panel, min=self.limits[0],
                                    max=self.limits[1], style=wx.SP_ARROW_KEYS)
        self.lowyear.SetValue(self.config['lowyear'])
        self.fbox.Add(self.lowyear, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        choice = ('for', 'to').index(self.config['type'])
        # Use layout_ancestors=3 because 2 makes the sizer expand to the right
        # if the new widgets need more room, and 3 adds/removes a row if the
        # window is too narrow
        self.highchoice = WidgetChoiceCtrl(self.panel, (
                                            ('for', self._create_for_widget),
                                            ('to', self._create_to_widget)),
                                            choice, 4, layout_ancestors=3)
        self.highchoice.force_update()
        self.fbox.Add(self.highchoice.get_main_panel(),
                                                flag=wx.ALIGN_CENTER_VERTICAL)

    def _create_for_widget(self):
        panel = wx.Panel(self.highchoice.get_main_panel())
        box = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(box)

        self.highlimit = NarrowSpinCtrl(panel,
                                    min=1, max=99, style=wx.SP_ARROW_KEYS)
        self.highlimit.SetValue(self.config['span'])
        box.Add(self.highlimit, flag=wx.ALIGN_CENTER_VERTICAL |
                                                            wx.RIGHT, border=4)

        self.unitchoice = wx.Choice(panel, choices=('months', 'years'))
        self.unitchoice.SetSelection(self.unitchoice.FindString(
                                                        self.config['unit']))
        box.Add(self.unitchoice, flag=wx.ALIGN_CENTER_VERTICAL)

        return panel

    def _create_to_widget(self):
        panel = wx.Panel(self.highchoice.get_main_panel())
        box = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(box)

        self.highmonth = wx.Choice(panel, choices=('January',
                           'February', 'March', 'April', 'May', 'June', 'July',
                     'August', 'September', 'October', 'November', 'December'))
        self.highmonth.SetSelection(self.config['highmonth0'])
        box.Add(self.highmonth, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.highyear = NarrowSpinCtrl(panel, min=self.limits[0],
                                    max=self.limits[1], style=wx.SP_ARROW_KEYS)
        self.highyear.SetValue(self.config['highyear'])
        box.Add(self.highyear, flag=wx.ALIGN_CENTER_VERTICAL)

        return panel

    def get_values(self):
        values = {
            'mode': 'month',
            'lowyear': self.lowyear.GetValue(),
            'lowmonth0': self.lowmonth.GetSelection(),
        }

        if self.highchoice.get_selection() == 1:
            values.update({
                'type': 'to',
                'highyear': self.highyear.GetValue(),
                'highmonth0': self.highmonth.GetSelection(),
            })
        else:
            values.update({
                'type': 'for',
                'number': self.highlimit.GetValue(),
                # GetString returns a unicode object, it's necessary to convert
                # it into a normal string because the configfile module doesn't
                # support unicode objects
                'unit': str(self.unitchoice.GetString(
                                            self.unitchoice.GetSelection())),
            })

        return values


class FilterRelative(object):
    def __init__(self, config):
        low = config['low'][config['uniti']]

        if config['type'] == 'for':
            high = low + config['high'][config['type']][config['uniti']]
        else:
            # Add 1 because e.g. 'from 0 to 0' must show the current period,
            # just like 'from 0 for 1', and unlike 'from 0 to 1', which should
            # show also the next period
            high = config['high'][config['type']][config['uniti']] + 1

        self.filter = {
            'minutes': FilterRelativeMinutes,
            'hours': FilterRelativeHours,
            'days': FilterRelativeDays,
            'weeks': FilterRelativeWeeks,
            'months': FilterRelativeMonths,
            'years': FilterRelativeYears,
        }[config['unit']](low, high)

    def compute_limits(self, now):
        return self.filter.compute_limits(now)

    def compute_delay(self, occsobj, now, mint, maxt):
        return self.filter.compute_delay(occsobj, now, mint, maxt)


class FilterRelativeMinutes(object):
    def __init__(self, low, high):
        self.CORRECTION = 1
        self.low = low * 60
        self.high = high * 60

    def compute_limits(self, now):
        # Base all calculations on exact minutes, in order to limit the
        # possible cases and simplify debugging; occurrences cannot happen on
        # non-exact minutes anyway
        anow = now // 60 * 60
        mint = anow + self.low
        # Subtract self.CORRECTION seconds because if setting 'to 0'/'for 1'
        # it's expected to only show the current minute, and not occurrences
        # starting at the next minute
        maxt = anow + self.high - self.CORRECTION
        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        next_completion = occsobj.get_next_completion_time()

        filenames = organism_api.get_supported_open_databases()

        # Note that this does *not* use
        # organism_timer_api.search_next_occurrences which would signal
        # search_next_occurrences_event, thus making this very method recur
        # infinitely
        search = organism_timer_api.get_next_occurrences(base_time=maxt,
                                                        filenames=filenames)
        # For the moment there seems to be no need to stop the search if a
        # database is closed, in fact the search seems to terminate cleanly
        # and it should take a reasonable time to complete
        search.start()
        nextoccs = search.get_results()

        # Note that next_occurrence could even be a time of an occurrence
        # that's already displayed in the list (e.g. if an occurrence has a
        # start time within the queried range but an end time later than the
        # maximum end)
        next_occurrence = nextoccs.get_next_occurrence_time()

        delays = []

        try:
            d1 = next_completion - mint
        except TypeError:
            # next_completion could be None
            pass
        else:
            delays.append(d1)

        try:
            # Subtract self.CORRECTION because when the actual delay is
            # calculated later (`min(delays) ...`) all the values are assumed
            # being exact minutes
            d2 = next_occurrence - maxt - self.CORRECTION
        except TypeError:
            # next_occurrence could be None
            pass
        else:
            delays.append(d2)

        try:
            # Note that the delay can still be further limited in
            # RefreshEngine._restart
            # Add `60 - now % 60` so that:
            # * the refresh will occur at an exact minute
            # * in case of completion times, the refresh will correctly happen
            #   when the completion minute ends
            # * the delay will never be 0, which would make the tasklist
            #   refresh continuously until the end of the current minute
            # Note that this by itself would for example prevent the state
            # of an occurrence to be updated from future to ongoing
            # immediately (but it would happen with 60 seconds of delay),
            # however in that case the change of state is triggered by the
            # search_next_occurrences event at the correct time
            return min(delays) + 60 - now % 60
        except ValueError:
            # delays could be empty
            return None


class FilterRelativeHours(object):
    def __init__(self, low, high):
        self.low = low * 3600
        self.high = high * 3600

    def compute_limits(self, now):
        anow = now // 3600 * 3600
        mint = anow + self.low
        # Subtract 1 second because if setting 'to 0'/'for 1' it's expected to
        # only show the current hour, and not occurrences starting at the next
        # hour
        maxt = anow + self.high - 1
        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        # Note that the delay can still be further limited in
        # RefreshEngine._restart
        return 3600 - now % 3600


class FilterRelativeDays(object):
    def __init__(self, low, high):
        self.utcoffset = timeaux.UTCOffset()
        self.low = low * 86400
        self.high = high * 86400

    def compute_limits(self, now):
        try:
            # 'now' is not necessarily the actual current time, it's the search
            # reference time, so it must be protected
            self.nowoffset = self.utcoffset.compute(now)
        except ValueError:
            raise OutOfRangeError()
        else:
            # It's necessary to first subtract self.nowoffset to get the
            # correct date, otherwise for positive UTC values the next day will
            # be shown too early, and for negative UTC values it will be shown
            # too late; eventually self.nowoffset must be re-added to get the
            # correct local time
            anow = (now - self.nowoffset) // 86400 * 86400 + self.nowoffset
            mint = anow + self.low
            # Subtract 1 second because if setting 'to 0'/'for 1' it's expected
            # to only show the current day, and not occurrences starting at
            # the next day
            maxt = anow + self.high - 1
            return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        # Note that the delay can still be further limited in
        # RefreshEngine._restart
        # Subtract self.nowoffset *before* modding by 86400 or negative values
        # may be returned
        return 86400 - (now - self.nowoffset) % 86400


class FilterRelativeWeeks(object):
    def __init__(self, low, high):
        self.low = low * 604800
        self.high = high * 604800
        self.firstweekday = coreaux_api.get_plugin_configuration('wxtasklist'
                                                    ).get_int('first_weekday')

    def compute_limits(self, now):
        try:
            # 'now' is not necessarily the actual current time, it's the search
            # reference time, so it must be protected
            dnow = _datetime.date.fromtimestamp(now)
            weekday = dnow.weekday()
            relweekdaystart = (7 - self.firstweekday + weekday) % 7 * 86400
            self.weekstart = int(_time.mktime(dnow.timetuple())
                                                            ) - relweekdaystart
        except ValueError:
            raise OutOfRangeError()
        else:
            mint = self.weekstart + self.low
            # Subtract 1 second because if setting 'to 0'/'for 1' it's expected
            # to only show the current week, and not occurrences starting at
            # the next week
            maxt = self.weekstart + self.high - 1
            return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        # Note that the delay can still be further limited in
        # RefreshEngine._restart
        return self.weekstart + 604800 - now


class FilterRelativeMonths(object):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def compute_limits(self, now):
        try:
            # 'now' is not necessarily the actual current time, it's the search
            # reference time, so it must be protected
            self.dnow = _datetime.date.fromtimestamp(now)
            rminyears, minmonth = divmod(self.dnow.month - 1 + self.low, 12)

            dmin = _datetime.date(year=self.dnow.year + rminyears,
                                                    month=minmonth + 1, day=1)
            rmaxyears, maxmonth = divmod(self.dnow.month - 1 + self.high, 12)
            dmax = _datetime.date(year=self.dnow.year + rmaxyears,
                                                    month=maxmonth + 1, day=1)
            mint = int(_time.mktime(dmin.timetuple()))
            # Subtract 1 second because if setting 'to 0'/'for 1' it's expected
            # to only show the current month, and not occurrences starting at
            # the next month
            maxt = int(_time.mktime(dmax.timetuple())) - 1
        except ValueError:
            raise OutOfRangeError()
        else:
            return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        # I should add 1 to self.dnow.month, but I should also subtract 1
        # because I need 0-based months
        rnyear, nmonth = divmod(self.dnow.month, 12)
        ndate = _datetime.date(year=self.dnow.year + rnyear, month=nmonth + 1,
                                                                        day=1)
        # Note that the delay can still be further limited in
        # RefreshEngine._restart
        return int(_time.mktime(ndate.timetuple())) - now


class FilterRelativeYears(object):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def compute_limits(self, now):
        try:
            # 'now' is not necessarily the actual current time, it's the search
            # reference time, so it must be protected
            self.dnow = _datetime.date.fromtimestamp(now)

            dmin = _datetime.date(year=self.dnow.year + self.low, month=1,
                                                                        day=1)
            dmax = _datetime.date(year=self.dnow.year + self.high, month=1,
                                                                        day=1)

            mint = int(_time.mktime(dmin.timetuple()))
            # Subtract 1 second because if setting 'to 0'/'for 1' it's expected
            # to only show the current year, and not occurrences starting at
            # the next year
            maxt = int(_time.mktime(dmax.timetuple())) - 1
        except ValueError:
            raise OutOfRangeError()
        else:
            return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        ndate = _datetime.date(year=self.dnow.year + 1, month=1, day=1)
        # Note that the delay can still be further limited in
        # RefreshEngine._restart
        return int(_time.mktime(ndate.timetuple())) - now


class FilterDate(object):
    def __init__(self, config):
        # The values are already validated in the FilterConfigurationDate
        self.low = int(_time.mktime(config['lowdate'].timetuple()))
        # Add 86400 because the stored date is included in the range, but I
        # need the midnight of the following day
        # Subtract 1 second because if setting 'for 1' it's expected to not see
        # the occurrences starting at the end of the interval
        self.high = int(_time.mktime(config['highdate'].timetuple())) + 86399

    def compute_limits(self, now):
        return (self.low, self.high)

    def compute_delay(self, occsobj, now, mint, maxt):
        return None


class FilterMonth(object):
    def __init__(self, config):
        # The values are already validated in the FilterConfigurationMonth
        lowdate = _datetime.date(config['lowyear'], config['lowmonth0'] + 1, 1)
        highdate = _datetime.date(config['highyear'], config['highmonth0'] + 1,
                                                                            1)

        # I should add 1 to highmonth because the stored month is included in
        # the range, and I'd need the midnight of the first day of the
        # following month; however I should also subtract 1 because I need a
        # 0-based value here
        # This in practice just allows going to next year if highmonth is 12
        rnyear, nextmonth = divmod(highdate.month, 12)

        nextdate = _datetime.date(highdate.year + rnyear, nextmonth + 1, 1)

        self.low = int(_time.mktime(lowdate.timetuple()))
        # Subtract 1 second because if setting 'for 1' it's expected to not see
        # the occurrences starting at the end of the interval
        self.high = int(_time.mktime(nextdate.timetuple())) - 1

    def compute_limits(self, now):
        return (self.low, self.high)

    def compute_delay(self, occsobj, now, mint, maxt):
        return None
