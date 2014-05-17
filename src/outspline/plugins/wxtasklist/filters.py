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
from collections import OrderedDict

from outspline.static.wxclasses.timectrls import DateHourCtrl, TimeSpanCtrl
from outspline.static.wxclasses.misc import NarrowSpinCtrl

import outspline.coreaux_api as coreaux_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.interfaces.wxgui_api as wxgui_api


class Filters(object):
    def __init__(self, tasklist):
        self.DEFAULT_FILTERS = {
            0: {
                'F0': OrderedDict([
                    ('name', 'Next 24 hours'),
                    ('mode', 'relative'),
                    ('low', '-5'),
                    ('high', '1440'),
                ]),
                'F1': OrderedDict([
                    ('name', 'Current week'),
                    ('mode', 'regular'),
                    # A Monday, must be in local time
                    # Note there's not a native way in Python to initialize this to a
                    # Monday or Sunday depending on the local week conventions
                    ('base', '2013-10-21T00:00'),
                    ('span', '10079'),
                    ('advance', '10080'),
                ]),
                'F2': OrderedDict([
                    ('name', 'Current month'),
                    ('mode', 'month'),
                    ('month', '1'),
                    ('span', '1'),
                    ('advance', '1'),
                ]),
            },
        }

        self.editor = False

        # tasklist.list_ hasn't been instantiated yet here
        self.tasklist = tasklist

        self.config = coreaux_api.get_plugin_configuration('wxtasklist')
        self.update_filters()
        self.selected_filter = self.config['selected_filter']

        try:
            config = self.config('Filters')(self.selected_filter)
        except KeyError:
            filter_ = self.filterssorted[0]
            # The configuration is exported to the file only when exiting
            # Outspline
            config = self.get_filter_configuration(filter_)
            self.config['selected_filter'] = filter_
            self.selected_filter = self.config['selected_filter']

    def update_filters(self):
        filters = self.config('Filters')
        self.filterssorted = filters.get_sections()

        if len(self.filterssorted) == 0:
            filters.reset(self.DEFAULT_FILTERS)

            # Re-get the sections after resetting
            self.filterssorted = filters.get_sections()

        # Filters with the same name must be supported, and with the current
        # absence of a way to configure their order in the choice control, they
        # must be sorted alphabetically
        self.filterssorted.sort(key=self._get_sorting_key)

    def _get_sorting_key(self, filter_):
        return self.config('Filters')(filter_)['name']

    def get_filters_sorted(self):
        return self.filterssorted

    def get_filter_configuration(self, filter_):
        return self.config('Filters')(filter_).get_options()

    def get_selected_filter(self):
        return self.selected_filter

    def select_filter(self, filter_, config):
        # Trying to select a filter while one is being edited is not
        # supported, so close any open editor first
        if self.editor:
            self.editor.close()

        self.tasklist.list_.set_filter(config)

        # The configuration is exported to the file only when exiting Outspline
        self.config['selected_filter'] = filter_
        self.selected_filter = filter_

        self.set_tab_title(config['name'])

        self.tasklist.list_.delay_restart()

    def apply_selected_filter(self):
        config = self.get_filter_configuration(self.get_selected_filter())
        self.tasklist.list_.set_filter(config)
        self.tasklist.list_.delay_restart()
        self.set_tab_title(config['name'])

    def create(self):
        if self.editor:
            self.editor.close()

        self.editor = FilterEditor(self.tasklist, self.DEFAULT_FILTERS, None,
                                                                        None)
        self.set_tab_title('New filter')

    def edit_selected(self):
        if self.editor:
            self.editor.close()

        filter_ = self.get_selected_filter()
        config = self.get_filter_configuration(filter_)
        self.editor = FilterEditor(self.tasklist, self.DEFAULT_FILTERS,
                                                            filter_, config)

    def remove_selected(self):
        # If there's only one filter left in the configuration, the remove
        # menu item is disabled; however update_filters can also handle the
        # case where there are no filters in the configuration, so no further
        # tests are needed here
        # Trying to remove a filter that is being edited, and then trying to
        # save the editor, would generate an error, so close any open editors
        # first
        if self.editor:
            self.editor.close()

        filter_ = self.get_selected_filter()
        filters = self.config('Filters')
        filters(filter_).delete()

        self.update_filters()

        # Select the first filter for safe and consistent behavior
        filter_ = self.filterssorted[0]
        config = self.get_filter_configuration(filter_)

        self.select_filter(filter_, config)

    def set_tab_title(self, title):
        wxgui_api.set_right_nb_page_title(self.tasklist.panel, title)


class FilterEditor(object):
    def __init__(self, tasklist, default_filters, filterid, config):
        self.tasklist = tasklist
        self.default_filters = default_filters
        self.parent = tasklist.panel
        self.editid = filterid
        self.filters = tasklist.filters
        self.panel = wx.Panel(self.parent)
        self.fbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.fbox)

        self._init_config(config)
        self._init_header()
        self._init_filter_types()
        self._init_selected_filter()

        self.parent.GetSizer().Prepend(self.panel, flag=wx.EXPAND)
        self.parent.GetSizer().Layout()

    def _init_config(self, config):
        if config:
            self.config = config
        else:
            self.config = self.default_filters[0]['F0']
            self.config['name'] = 'New filter'

    def _init_header(self):
        sheader = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self.panel, label='Name:')
        sheader.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.name = wx.TextCtrl(self.panel, value=self.config['name'])
        sheader.Add(self.name, 1, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        button_save = wx.Button(self.panel, label='Save')
        sheader.Add(button_save, flag=wx.RIGHT, border=4)

        button_preview = wx.Button(self.panel, label='Preview')
        sheader.Add(button_preview, flag=wx.RIGHT, border=4)

        button_cancel = wx.Button(self.panel, label='Cancel')
        sheader.Add(button_cancel)

        self.fbox.Add(sheader, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.panel.Bind(wx.EVT_BUTTON, self._save, button_save)
        self.panel.Bind(wx.EVT_BUTTON, self._preview, button_preview)
        self.panel.Bind(wx.EVT_BUTTON, self._cancel, button_cancel)

    def _compose_configuration(self):
        config = OrderedDict()

        # wx.TextCtrl.GetValue returns a unicode, not a str
        config['name'] = str(self.name.GetValue())

        config.update(self.sfilter.get_config())

        return config

    def _save(self, event):
        # Note that the configuration is exported to the file only when exiting
        # Outspline
        config = self._compose_configuration()

        filtersconfig = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                                     'Filters')

        if self.editid:
            filter_ = self.editid
            filtersconfig(filter_).reset(config)
            self.filters.update_filters()
        else:
            newid = 0

            while True:
                filter_ = ''.join(('F', str(newid)))

                try:
                    filtersconfig(filter_)
                except KeyError:
                    filtersconfig.make_subsection(filter_)
                    filtersconfig(filter_).reset(config)
                    self.filters.update_filters()
                    break
                else:
                    newid += 1

        # self.filters.select_filter will take care of closing the editor,
        # don't call self.close here
        self.filters.select_filter(filter_, config)

    def _preview(self, event):
        config = self._compose_configuration()
        self.tasklist.list_.set_filter(config)
        self.filters.set_tab_title(config['name'])
        self.tasklist.list_.delay_restart()

    def _cancel(self, event):
        self.close()
        self.filters.apply_selected_filter()

    def close(self):
        self.panel.Destroy()
        # Do not just do `del self.filters.editor`, otherwise AttributeError
        # will be raised the next time a rule is attempted to be edited
        self.filters.editor = False
        self.parent.GetSizer().Layout()

    def _init_filter_types(self):
        self.choice = wx.Choice(self.panel, choices=())

        self.choice.Append("Relative interval (dnyamic)",
                                            clientData=FilterRelativeInterface)
        self.choice.Append("Absolute interval (static)",
                                            clientData=FilterAbsoluteInterface)
        self.choice.Append("Regular interval (dnyamic)",
                                             clientData=FilterRegularInterface)
        self.choice.Append("Month-based interval (static)",
                                         clientData=FilterMonthStaticInterface)
        self.choice.Append("Month-based interval (dnyamic)",
                                        clientData=FilterMonthDynamicInterface)


        self.choice.SetSelection({
            'relative': 0,
            'absolute': 1,
            'regular': 2,
            'staticmonth': 3,
            'month': 4,
        }[self.config['mode']])

        self.fbox.Add(self.choice, flag=wx.BOTTOM, border=4)

        self.panel.Bind(wx.EVT_CHOICE, self._choose_filter_type, self.choice)

    def _init_selected_filter(self):
        self.sfilter = self.choice.GetClientData(self.choice.GetSelection()
                                                     )(self.panel, self.config)
        self.fbox.Add(self.sfilter.panel, flag=wx.EXPAND | wx.BOTTOM, border=4)

    def _choose_filter_type(self, event):
        fpanel = event.GetClientData()(self.panel, self.config)
        self.fbox.Replace(self.sfilter.panel, fpanel.panel)
        self.sfilter.panel.Destroy()
        self.sfilter = fpanel
        self.parent.Layout()


class FilterRelativeInterface(object):
    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=2, cols=2, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        lowlabel = wx.StaticText(self.panel, label='Low limit:')
        self.fgrid.Add(lowlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # It must be possible to set up at least to 527039 minutes
        # (1 leap year - 1 minute)
        self.lowlimit = TimeSpanCtrl(self.panel, -999999, 999999)
        self.lowlimit.set_values(*TimeSpanCtrl.compute_widget_values(
                                                           self.values['low']))
        self.fgrid.Add(self.lowlimit.get_main_panel())

        highlabel = wx.StaticText(self.panel, label='High limit:')
        self.fgrid.Add(highlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # It must be possible to set up at least to 527039 minutes
        # (1 leap year - 1 minute)
        self.highlimit = TimeSpanCtrl(self.panel, -999999, 999999)
        self.highlimit.set_values(*TimeSpanCtrl.compute_widget_values(
                                                          self.values['high']))
        self.fgrid.Add(self.highlimit.get_main_panel())

    def _init_config(self, config):
        # config cannot be None here, as it's been initialized in FilterEditor
        if config['mode'] == 'relative':
            # Do not overwrite the values in self.config, as they may be used
            # also by other filters
            limits = [int(config['low']) * 60, int(config['high']) * 60]
            limits.sort()
            self.values = {
                'low': limits[0],
                'high': limits[1],
            }
        else:
            self.values = {
                'low': -300,
                'high': 86400,
            }

    def get_config(self):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        config = OrderedDict()
        config['mode'] = 'relative'
        low = self.lowlimit.get_time_span()
        high = self.highlimit.get_time_span()

        try:
            lowneg = low // abs(low)
        except ZeroDivisionError:
            lowneg = 1

        try:
            highneg = high // abs(high)
        except ZeroDivisionError:
            highneg = 1

        config['low'] = str(abs(low) // 60 * lowneg)
        config['high'] = str(abs(high) // 60 * highneg)
        return config


class FilterAbsoluteInterface(object):
    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=2, cols=2, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        lowlabel = wx.StaticText(self.panel, label='Low limit:')
        self.fgrid.Add(lowlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.lowlimit = DateHourCtrl(self.panel)
        self.lowlimit.set_values(self.values['lowyear'],
                                 self.values['lowmonth'] - 1,
                                 self.values['lowday'],
                                 self.values['lowhour'],
                                 self.values['lowminute'])
        self.fgrid.Add(self.lowlimit.get_main_panel())

        highlabel = wx.StaticText(self.panel, label='High limit:')
        self.fgrid.Add(highlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.highlimit = DateHourCtrl(self.panel)
        self.highlimit.set_values(self.values['highyear'],
                                  self.values['highmonth'] - 1,
                                  self.values['highday'],
                                  self.values['highhour'],
                                  self.values['highminute'])
        self.fgrid.Add(self.highlimit.get_main_panel())

    def _init_config(self, config):
        # config cannot be None here, as it's been initialized in FilterEditor
        if config['mode'] == 'absolute':
            # Do not overwrite the values in self.config, as they may be used
            # also by other filters
            limits = [_time.mktime(_time.strptime(config['low'],
                                                            '%Y-%m-%dT%H:%M')),
                      _time.mktime(_time.strptime(config['high'],
                                                            '%Y-%m-%dT%H:%M'))]
            limits.sort()
            lowdate = _datetime.datetime.fromtimestamp(limits[0])
            highdate = _datetime.datetime.fromtimestamp(limits[1])
            self.values = {
                'lowyear': lowdate.year,
                'lowmonth': lowdate.month,
                'lowday': lowdate.day,
                'lowhour': lowdate.hour,
                'lowminute': lowdate.minute,
                'highyear': highdate.year,
                'highmonth': highdate.month,
                'highday': highdate.day,
                'highhour': highdate.hour,
                'highminute': highdate.minute,
            }
        else:
            today = _datetime.date.today()
            self.values = {
                'lowyear': today.year,
                'lowmonth': today.month,
                'lowday': today.day,
                'lowhour': 0,
                'lowminute': 0,
                'highyear': today.year,
                'highmonth': today.month,
                'highday': today.day,
                'highhour': 23,
                'highminute': 59,
            }

    def get_config(self):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        config = OrderedDict()
        config['mode'] = 'absolute'
        low = self.lowlimit.get_unix_time()
        high = self.highlimit.get_unix_time()
        config['low'] = _time.strftime('%Y-%m-%dT%H:%M', _time.localtime(low))
        config['high'] = _time.strftime('%Y-%m-%dT%H:%M',
                                                         _time.localtime(high))
        return config


class FilterRegularInterface(object):
    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=3, cols=2, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        baselabel = wx.StaticText(self.panel, label='Low limit sample:')
        self.fgrid.Add(baselabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.base = DateHourCtrl(self.panel)
        today = _datetime.date.today()
        self.base.set_values(self.values['baseyear'],
                             self.values['basemonth'] - 1,
                             self.values['baseday'],
                             self.values['basehour'],
                             self.values['baseminute'])
        self.fgrid.Add(self.base.get_main_panel())

        spanlabel = wx.StaticText(self.panel, label='Time span:')
        self.fgrid.Add(spanlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # It must be possible to set up at least to 527039 minutes
        # (1 leap year - 1 minute)
        self.span = TimeSpanCtrl(self.panel, 1, 999999)
        self.span.set_values(*TimeSpanCtrl.compute_widget_values(
                                                          self.values['span']))
        self.fgrid.Add(self.span.get_main_panel())

        advlabel = wx.StaticText(self.panel, label='Advance interval:')
        self.fgrid.Add(advlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # It must be possible to set up at least to 527039 minutes
        # (1 leap year - 1 minute)
        self.advance = TimeSpanCtrl(self.panel, 1, 999999)
        self.advance.set_values(*TimeSpanCtrl.compute_widget_values(
                                                       self.values['advance']))
        self.fgrid.Add(self.advance.get_main_panel())

    def _init_config(self, config):
        # config cannot be None here, as it's been initialized in FilterEditor
        if config['mode'] == 'regular':
            # Do not overwrite the values in self.config, as they may be used
            # also by other filters
            basetime = _time.mktime(_time.strptime(config['base'],
                                                             '%Y-%m-%dT%H:%M'))
            basedate = _datetime.datetime.fromtimestamp(basetime)
            self.values = {
                'baseyear': basedate.year,
                'basemonth': basedate.month,
                'baseday': basedate.day,
                'basehour': basedate.hour,
                'baseminute': basedate.minute,
                'span': max(int(config['span']), 1) * 60,
                'advance': max(int(config['advance']), 1) * 60,
            }
        else:
            today = _datetime.date.today()
            self.values = {
                'baseyear': today.year,
                'basemonth': today.month,
                'baseday': today.day,
                'basehour': 0,
                'baseminute': 0,
                'span': 86340,
                'advance': 86400,
            }

    def get_config(self):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        return OrderedDict([
            ('mode', 'regular'),
            ('base', _time.strftime('%Y-%m-%dT%H:%M',
                                  _time.localtime(self.base.get_unix_time()))),
            ('span', str(self.span.get_time_span() // 60)),
            ('advance', str(self.advance.get_time_span() // 60)),
        ])


class FilterMonthStaticInterface(object):
    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=2, cols=3, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        today = _datetime.date.today()

        monthlabel = wx.StaticText(self.panel, label='Low month:')
        self.fgrid.Add(monthlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.month = wx.Choice(self.panel, choices=('January',
                           'February', 'March', 'April', 'May', 'June', 'July',
                     'August', 'September', 'October', 'November', 'December'))
        self.month.SetSelection(self.values['month'] - 1)
        self.fgrid.Add(self.month)

        self.year = NarrowSpinCtrl(self.panel, min=1970, max=9999,
                                                        style=wx.SP_ARROW_KEYS)
        self.year.SetValue(self.values['year'])
        self.fgrid.Add(self.year)

        spanlabel = wx.StaticText(self.panel, label='Months span:')
        self.fgrid.Add(spanlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.span = NarrowSpinCtrl(self.panel, min=1, max=999,
                                                        style=wx.SP_ARROW_KEYS)
        self.span.SetValue(self.values['span'])
        self.fgrid.Add(self.span)

    def _init_config(self, config):
        # config cannot be None here, as it's been initialized in FilterEditor
        if config['mode'] == 'staticmonth':
            # Do not overwrite the values in self.config, as they may be used
            # also by other filters
            self.values = {
                'month': min(max(int(config['month']), 1), 12),
                'year': max(int(config['year']), 1970),
                'span': max(int(config['span']), 1),
            }
        else:
            today = _datetime.date.today()
            self.values = {
                'month': today.month,
                'year': today.year,
                'span': 1,
            }

    def get_config(self):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        return OrderedDict([
            ('mode', 'staticmonth'),
            ('month', str(self.month.GetSelection() + 1)),
            ('year', str(self.year.GetValue())),
            ('span', str(self.span.GetValue())),
        ])


class FilterMonthDynamicInterface(object):
    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=3, cols=2, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        monthlabel = wx.StaticText(self.panel, label='Low month sample:')
        self.fgrid.Add(monthlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.month = wx.Choice(self.panel, choices=('January',
                           'February', 'March', 'April', 'May', 'June', 'July',
                     'August', 'September', 'October', 'November', 'December'))
        today = _datetime.date.today()
        self.month.SetSelection(self.values['month'] - 1)
        self.fgrid.Add(self.month)

        spanlabel = wx.StaticText(self.panel, label='Months span:')
        self.fgrid.Add(spanlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # Note that FilterMonthDynamic.compute_limits only supports spans
        # <= 12 months
        self.span = NarrowSpinCtrl(self.panel, min=1, max=12,
                                                        style=wx.SP_ARROW_KEYS)
        self.span.SetValue(self.values['span'])
        self.fgrid.Add(self.span)

        advlabel = wx.StaticText(self.panel, label='Advance interval:')
        self.fgrid.Add(advlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # Note that FilterMonthDynamic.compute_limits only supports intervals
        # <= 12 months
        self.advance = NarrowSpinCtrl(self.panel, min=1, max=12,
                                                        style=wx.SP_ARROW_KEYS)
        self.advance.SetValue(self.values['advance'])
        self.fgrid.Add(self.advance)

    def _init_config(self, config):
        # config cannot be None here, as it's been initialized in FilterEditor
        if config['mode'] == 'month':
            # Do not overwrite the values in self.config, as they may be used
            # also by other filters
            self.values = {
                'month': min(max(int(config['month']), 1), 12),
                # For the moment only span<= 12 is supported
                'span': min(max(int(config['span']), 1), 12),
                # For the moment only advance <= 12 is supported
                'advance': min(max(int(config['advance']), 1), 12),
            }
        else:
            today = _datetime.date.today()
            self.values = {
                'month': today.month,
                'span': 1,
                'advance': 1,
            }

    def get_config(self):
        # It's important to store only the significant values for the limits:
        # this helps preventing the user from entering wrong values in the
        # configuration file
        return OrderedDict([
            ('mode', 'month'),
            ('month', str(self.month.GetSelection() + 1)),
            ('span', str(self.span.GetValue())),
            ('advance', str(self.advance.GetValue())),
        ])


class FilterRelative(object):
    def __init__(self, config):
        # Make sure self.low is lower than self.high
        limits = [int(config['low']) * 60, int(config['high']) * 60]
        limits.sort()
        self.low, self.high = limits

    def compute_limits(self, now):
        # Base all calculations on exact minutes, in order to limit the
        # possible cases and simplify debugging; occurrences cannot happen on
        # non-exact minutes anyway
        anow = now // 60 * 60
        mint = anow + self.low
        maxt = anow + self.high
        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        next_completion = occsobj.get_next_completion_time()

        # Note that this does *not* use
        # organism_timer_api.search_next_occurrences which would signal
        # search_next_occurrences_event, thus making this very method recur
        # infinitely
        nextoccs = organism_timer_api.get_next_occurrences(base_time=maxt)

        # Note that next_occurrence could even be a time of an occurrence
        # that's already displayed in the list (e.g. if an occurrence has a
        # start time within the queried range but an end time later than the
        # maximum end)
        next_occurrence = nextoccs.get_next_occurrence_time()

        delays = []

        try:
            # Add 60 so that the tasklist will be refreshed only when the
            # completion minute ends; also this way the difference will never
            # be 0, which would make the tasklist refresh continuously until
            # the end of the completion minute
            # Note that this by itself would for example prevent the state
            # of an occurrence to be updated from future to ongoing
            # immediately (but it would happen with 60 seconds of delay),
            # however in that case the change of state is triggered by the
            # search_next_occurrences event at the correct time
            d1 = next_completion - mint + 60
        except TypeError:
            # next_completion could be None
            pass
        else:
            delays.append(d1)

        try:
            # Note that, unlike above, next_occurrence is always greater than
            # maxt, so this difference will never be 0
            d2 = next_occurrence - maxt
        except TypeError:
            # next_occurrence could be None
            pass
        else:
            delays.append(d2)

        try:
            # Note that the delay can still be further limited in
            # OccurrencesView._restart
            # Subtract `now % 60` so that the refresh will occur at an exact
            # minute
            return min(delays) - now % 60
        except ValueError:
            # delays could be empty
            return None


class FilterAbsolute(object):
    def __init__(self, config):
        # Make sure self.low is lower than self.high
        limits = [int(_time.mktime(_time.strptime(config['low'],
                                                           '%Y-%m-%dT%H:%M'))),
                  int(_time.mktime(_time.strptime(config['high'],
                                                           '%Y-%m-%dT%H:%M')))]
        limits.sort()
        self.low, self.high = limits

    def compute_limits(self, now):
        return (self.low, self.high)

    def compute_delay(self, occsobj, now, mint, maxt):
        return None


class FilterRegular(object):
    def __init__(self, config):
        self.base = int(_time.mktime(_time.strptime(config['base'],
                                                            '%Y-%m-%dT%H:%M')))
        self.span = max(int(config['span']), 1) * 60
        self.advance = max(int(config['advance']), 1) * 60

    """
    * reference view (refmin, refmax)
    | reftime (now)
    [] target view (mintime, maxtime)

    A) mintime = reftime - ((reftime - refmin) % advance)
    B) mintime = reftime - ((reftime - refmin) % advance) + advance
    C) mintime = reftime - ((reftime - refmin) % advance) - ((refspan // advance) * advance)
    D) mintime = reftime - ((reftime - refmin) % advance) - ((refspan // advance) * advance) + advance

    G) mintime = reftime - ((reftime - refmax) % advance) - refspan
    H) mintime = reftime - ((reftime - refmax) % advance) + advance - refspan
    I) (!NOT VERIFIED!) mintime = reftime - ((reftime - refmax) % advance) - refspan + ((refspan // advance) * advance)
    J) (!NOT VERIFIED!) mintime = reftime - ((reftime - refmax) % advance) - refspan + ((refspan // advance) * advance) + advance

    M) mintime = reftime + ((refmin - reftime) % advance) - advance
    N) mintime = reftime + ((refmin - reftime) % advance)
    O) mintime = reftime + ((refmin - reftime) % advance) - ((refspan // advance) * advance) - advance
    P) mintime = reftime + ((refmin - reftime) % advance) - ((refspan // advance) * advance)

    S) mintime = reftime + ((refmax - reftime) % advance) - refspan
    T) mintime = reftime + ((refmax - reftime) % advance) + advance - refspan
    U) (!NOT VERIFIED!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance)
    V) (!NOT VERIFIED!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance) + advance

    All cases from extensions.organism_basicrules.occur_regularly are valid,
    except for the following:

    --------(  *  )--------(     )--------[     |--------(     )--------(     )-----
    AGMS

    --------[     |--------(     )--------(     )--------(     )--------(  *  )-----
    AGMS

    --------(     )--------[  *  |--------(     )--------(     )--------(     )-----
    AGMS

                *                         |
    (     (     (   ) (   ) (   ) (   ) [ | ) (   ) (   ] (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6 | 4 7   5 8   6 9   7     8     9
    (               )                     |
          (     *         )               |
                (               )         |
                      (               )   |
                            (             | )
                                  (       |       )
                                        [ |             ]
                                          |   (               )
                                          |         (               )
                                          |               (               )
    AJMU

                        |                           *
    (     (     (   ) [ | ) (   ) (   ] (   ) (   ) (   ) (   )     )     )
    0     1     2   0 3 | 1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               )   |
          (             | )
                (       |       )
                      [ |             ]
                        |   (               )
                        |         (               )
                        |               (               )
                        |                     (     *         )
                        |                           (               )
                        |                                 (               )
    AJMU

                                        * |
    (     (     (   ) (   ) (   ) (   ) [ | ) (   ) (   ] (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6 | 4 7   5 8   6 9   7     8     9
    (               )                     |
          (               )               |
                (               )         |
                      (               )   |
                            (             | )
                                  (     * |       )
                                        [ |             ]
                                          |   (               )
                                          |         (               )
                                          |               (               )
    AJMU

                *                       |
    (     (     (   ) (   ) (   ) (   ) |   ) (   ) (   ] (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               )                   |
          (     *         )             |
                (               )       |
                      (               ) |
                            (           |   )
                                  (     |         )
                                        |               ]
                                        |     (               )
                                        |           (               )
                                        |                 (               )
    AJNU

                *                           |
    (     (     (   ) (   ) (   ) (   ) [   | (   ) (   ] (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               )                       |
          (     *         )                 |
                (               )           |
                      (               )     |
                            (               |
                                  (         |     )
                                        [   |           ]
                                            | (               )
                                            |       (               )
                                            |             (               )
    AIMU

                      |                             *
    (     (     (   ) |   ) (   ) (   ] (   ) (   ) (   ) (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               ) |
          (           |   )
                (     |         )
                      |               ]
                      |     (               )
                      |           (               )
                      |                 (               )
                      |                       (     *         )
                      |                             (               )
                      |                                   (               )
    AJNU

                          |                         *
    (     (     (   ) [   | (   ) (   ] (   ) (   ) (   ) (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               )     |
          (               |
                (         |     )
                      [   |           ]
                          | (               )
                          |       (               )
                          |             (               )
                          |                   (     *         )
                          |                         (               )
                          |                               (               )
    AIMU

                                        *
    (     (     (   ) (   ) (   ) (   ) |   ) (   ) (   ] (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               )                   |
          (               )             |
                (               )       |
                      (               ) |
                            (           |   )
                                  (     |         )
                                        |               ]
                                        |     (               )
                                        |           (               )
                                        |                 (               )
    AJNU

                            *               |
    (     (     (   ) (   ) (   ) (   ) [   | (   ) (   ] (   )     )     )
    0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
    (               )                       |
          (               )                 |
                (               )           |
                      (     *         )     |
                            (               |
                                  (         |     )
                                        [   |           ]
                                            | (               )
                                            |       (               )
                                            |             (               )
    AIMU
    """

    def compute_limits(self, now):
        # Use advance, *not* span, as the interval between two bases; this
        # allows for example to view only the 5 working days of the week and
        # still correctly advance to the next week, bypassing the weekend
        # In case of overlapping spans, I want the most advanced (as opposed
        # to what e.g. happens when calculating item occurrences)
        rem = (self.base + self.span - now) % self.advance

        if self.span == self.advance and rem == 0:
            # Use formula (T), see the examples above and in
            # extensions.organism_basicrules.occur_regularly
            maxt = now + rem + self.advance
            mint = maxt - self.span
        elif self.span <= self.advance:
            # Use formula (S), see the examples above and in
            # extensions.organism_basicrules.occur_regularly
            maxt = now + rem
            mint = maxt - self.span
        else:
            # Use formula (A), see the examples above and in
            # extensions.organism_basicrules.occur_regularly
            mint = now - (now - self.base) % self.advance
            maxt = mint + self.span

        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        # Note that the delay can still be further limited in
        # OccurrencesView._restart
        return max(min((mint + self.advance, maxt)) - now, 0)


class FilterMonthStatic(object):
    def __init__(self, config):
        self.month = min(max(int(config['month']), 1), 12)
        self.span = max(int(config['span']), 1)
        self.year = max(int(config['year']), 1970)

    def compute_limits(self, now):
        mindate = _datetime.date(self.year, self.month, 1)
        # In divmod it's necessary to use a 0-11 month number
        years, maxmonth = divmod(self.month - 1 + self.span, 12)
        maxdate = _datetime.date(self.year + years, maxmonth + 1, 1)
        mint = int(_time.mktime(mindate.timetuple()))
        maxt = int(_time.mktime(maxdate.timetuple())) - 60
        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        return None


class FilterMonthDynamic(object):
    def __init__(self, config):
        self.month = min(max(int(config['month']), 1), 12)
        # For the moment only span<= 12 is supported
        self.span = min(max(int(config['span']), 1), 12)
        # For the moment only advance <= 12 is supported
        self.advance = min(max(int(config['advance']), 1), 12)

    def compute_limits(self, now):
        # Since no reference year is configured, the current year is always
        # used; this means that this algorithm supports only spans and
        # intervals <= 12 months!!!
        nowdate = _datetime.date.fromtimestamp(now)

        # It's necessary to use a 0-11 month number for the computation
        # Add 23 in order to avoid doing calculations with negative months
        nowrmonth = nowdate.month + 23
        rmonth = self.month + 23

        # Use advance, *not* span, as the interval between two basedates; this
        # allows for example to view only the first 2 months in an interval of
        # 3 and still correctly advance to the fourth month, bypassing the
        # third
        # In case of overlapping spans, I want the most advanced
        rem = (rmonth + self.span - nowrmonth) % self.advance

        if self.span == self.advance and rem == 0:
            # Use formula (T), see the examples in FilterRegular and in
            # extensions.organism_basicrules.occur_regularly
            maxrmonth = nowrmonth + rem + self.advance
            minrmonth = maxrmonth - self.span
        elif self.span <= self.advance:
            # Use formula (S), see the examples in FilterRegular and in
            # extensions.organism_basicrules.occur_regularly
            maxrmonth = nowrmonth + rem
            minrmonth = maxrmonth - self.span
        else:
            # Use formula (A), see the examples in FilterRegular and in
            # extensions.organism_basicrules.occur_regularly
            minrmonth = nowrmonth - (nowrmonth - rmonth) % self.advance
            maxrmonth = minrmonth + self.span

        miny, minmonth = divmod(minrmonth, 12)
        maxy, maxmonth = divmod(maxrmonth, 12)
        maxryear = maxy - miny

        mindate = _datetime.date(nowdate.year, minmonth + 1, 1)
        maxdate = _datetime.date(nowdate.year + maxryear, maxmonth + 1, 1)

        mint = int(_time.mktime(mindate.timetuple()))
        maxt = int(_time.mktime(maxdate.timetuple())) - 60
        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        nowdate = _datetime.date.fromtimestamp(now)
        mindate = _datetime.date.fromtimestamp(mint)
        # In divmod it's necessary to use a 0-11 month number
        years, delaymonth = divmod(mindate.month - 1 + self.advance, 12)
        delaydate = _datetime.date(mindate.year + years, delaymonth + 1, 1)

        # Note that the delay can still be further limited in
        # OccurrencesView._restart
        return max((delaydate - nowdate).total_seconds(), 0)
