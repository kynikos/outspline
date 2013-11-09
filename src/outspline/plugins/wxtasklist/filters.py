# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

from outspline.static.wxclasses.choices import WidgetChoiceCtrl
from outspline.static.wxclasses.time import DateHourCtrl, TimeSpanCtrl
import outspline.coreaux_api as coreaux_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.interfaces.wxgui_api as wxgui_api

DEFAULT_FILTERS = {
    0: {
        'F0': OrderedDict([
            ('name', 'Next 24 hours'),
            ('mode', 'relative'),
            ('low', '-5'),
            ('high', '1440'),
            ('autoscroll', '1'),
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
            ('autoscroll', '1'),
        ]),
        'F2': OrderedDict([
            ('name', 'Current month'),
            ('mode', 'month'),
            ('month', '1'),
            ('span', '1'),
            ('advance', '1'),
            ('autoscroll', '1'),
        ]),
    },
}


class Filters():
    parent = None
    list_ = None
    panel = None
    fbox = None
    config = None
    choice = None
    filterids = None
    filtermap = None
    button_remove = None

    def __init__(self, parent, list_):
        self.parent = parent
        self.list_ = list_
        self.panel = wx.Panel(parent, style=wx.BORDER_NONE)
        self.fbox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.fbox)

        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

        self._init_choice()
        self._init_buttons()

        wxgui_api.bind_to_exit_application(self.handle_exit_application)

    def _init_choice(self):
        self.choice = wx.Choice(self.panel, size=(-1, 24), choices=())
        self.update_filters()

        selected_filter = self.config['selected_filter']

        try:
            self.config('Filters')(selected_filter)
        except KeyError:
            self.choice.SetSelection(0)
            self.list_.set_filter(self.choice.GetClientData(0))
        else:
            # Do not use self.choice.FindString because filter names are not
            # guaranteed to be unique
            index = self.filtermap[selected_filter]
            self.choice.SetSelection(index)
            self.list_.set_filter(self.choice.GetClientData(index))

        self.fbox.Add(self.choice, 1)

        self.panel.Bind(wx.EVT_CHOICE, self.choose_filter, self.choice)

    def _init_buttons(self):
        button_add = wx.Button(self.panel, label='Add', size=(60, 24))
        self.fbox.Add(button_add, flag=wx.LEFT, border=4)

        button_edit = wx.Button(self.panel, label='Edit', size=(60, 24))
        self.fbox.Add(button_edit, flag=wx.LEFT, border=4)

        self.button_remove = wx.Button(self.panel, label='Remove',
                                                                 size=(60, 24))
        self.fbox.Add(self.button_remove, flag=wx.LEFT, border=4)

        self.update_buttons()

        self.panel.Bind(wx.EVT_BUTTON, self.add_filter, button_add)
        self.panel.Bind(wx.EVT_BUTTON, self.edit_filter, button_edit)
        self.panel.Bind(wx.EVT_BUTTON, self.remove_filter, self.button_remove)

    def handle_exit_application(self, event):
        configfile = coreaux_api.get_user_config_file()
        # Reset the Filters section because some filters may have been removed
        self.config('Filters').export_reset(configfile)
        self.config.export_upgrade(configfile)

    def choose_filter(self, event):
        self.list_.set_filter(event.GetClientData())
        # The configuration is exported to the file only when exiting Outspline
        self.config['selected_filter'] = self.filterids[event.GetSelection()]
        self.list_.delay_restart()

    def add_filter(self, event):
        filter_ = FilterEditor(self.parent, self, None, None)
        self.parent.GetSizer().Replace(self.panel, filter_.panel)
        self.parent.GetSizer().Layout()

    def edit_filter(self, event):
        sel = self.choice.GetSelection()
        filterconf = self.choice.GetClientData(sel)
        filterid = self.filterids[sel]
        filter_ = FilterEditor(self.parent, self, filterid, filterconf)
        self.parent.GetSizer().Replace(self.panel, filter_.panel)
        self.parent.GetSizer().Layout()

    def remove_filter(self, event):
        # If there's only one filter left in the configuration, the remove
        # button is disabled; however update_filters can also handle the case
        # where there are no filters in the configuration, so no further tests
        # are needed here
        selection = self.choice.GetSelection()
        filters = self.config('Filters')
        filters(self.filterids[selection]).delete()
        self.choice.Delete(selection)
        self.update_buttons()
        self.update_filters()

        # Select the first filter for safe and consistent behavior
        self.choice.SetSelection(0)

        self.apply_selected_filter()

    def update_filters(self):
        filters = self.config('Filters')

        if len(filters.get_sections()) == 0:
            filters.reset(DEFAULT_FILTERS)

        self.filterids = {}
        self.filtermap = {}
        namemap = {}

        for filter_ in filters.get_sections():
            name = filters(filter_)['name']

            try:
                namemap[name]
            except KeyError:
                namemap[name] = []
            namemap[name].append(filter_)

        # Filters with the same name must be supported, and with the current
        # absence of a way to configure their order in the choice control, they
        # must be sorted alphabetically
        names = namemap.keys()
        names.sort()

        self.choice.Clear()

        for name in names:
            for filter_ in namemap[name]:
                index = self.choice.Append(name, clientData=filters(filter_
                                                  ).get_options(ordered=False))
                self.filterids[index] = filter_
                self.filtermap[filter_] = index

    def update_buttons(self):
        if self.choice.GetCount() < 2:
            self.button_remove.Enable(False)

    def update_filter_configuration(self, filter_, name, config):
        index = self.filtermap[filter_]
        self.choice.SetString(index, name)
        self.choice.SetClientData(index, config)

    def select_filter(self, filter_):
        self.choice.SetSelection(self.filtermap[filter_])

    def apply_selected_filter(self):
        self.list_.set_filter(self.choice.GetClientData(
                                                   self.choice.GetSelection()))
        self.list_.delay_restart()


class FilterEditor():
    parent = None
    editid = None
    config = None
    filters = None
    panel = None
    fbox = None
    name = None
    choice = None
    sfilter = None
    autoscroll = None
    aspaddingw = None
    aspadding = None

    def __init__(self, parent, filters, filterid, config):
        self.parent = parent
        self.editid = filterid
        self.filters = filters
        self.panel = wx.Panel(parent)
        self.fbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.fbox)

        self._init_config(config)
        self._init_header()
        self._init_filter_types()
        self._init_selected_filter()
        self._init_common_options()

    def _init_config(self, config):
        if config:
            self.config = config
        else:
            self.config = DEFAULT_FILTERS[0]['F0']
            self.config['name'] = 'New filter'

    def _init_header(self):
        sheader = wx.BoxSizer(wx.HORIZONTAL)
        self.fbox.Add(sheader, flag=wx.EXPAND)

        self.name = wx.TextCtrl(self.panel, value=self.config['name'],
                                                                 size=(-1, 24))
        sheader.Add(self.name, 1, flag=wx.BOTTOM, border=4)

        button_save = wx.Button(self.panel, label='Save', size=(60, 24))
        sheader.Add(button_save, flag=wx.LEFT | wx.BOTTOM, border=4)

        button_preview = wx.Button(self.panel, label='Preview', size=(60, 24))
        sheader.Add(button_preview, flag=wx.LEFT | wx.BOTTOM, border=4)

        button_cancel = wx.Button(self.panel, label='Cancel', size=(60, 24))
        sheader.Add(button_cancel, flag=wx.LEFT | wx.BOTTOM, border=4)

        self.panel.Bind(wx.EVT_BUTTON, self.save, button_save)
        self.panel.Bind(wx.EVT_BUTTON, self.preview, button_preview)
        self.panel.Bind(wx.EVT_BUTTON, self.cancel, button_cancel)

    def compose_configuration(self):
        config = OrderedDict()

        # wx.TextCtrl.GetValue returns a unicode, not a str
        config['name'] = str(self.name.GetValue())

        config.update(self.sfilter.get_config())

        if self.autoscroll.get_selection() == 1:
            config['autoscroll'] = str(self.aspaddingw.GetValue())
        else:
            config['autoscroll'] = 'off'

        return config

    def save(self, event):
        # Note that the configuration is exported to the file only when exiting
        # Outspline
        config = self.compose_configuration()

        filtersconfig = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                                     'Filters')

        if self.editid:
            filtersconfig(self.editid).reset(config)
            self.filters.update_filter_configuration(self.editid,
                                                        config['name'], config)
        else:
            newid = 0

            while True:
                newsection = ''.join(('F', str(newid)))

                try:
                    filtersconfig(newsection)
                except KeyError:
                    filtersconfig.make_subsection(newsection)
                    filtersconfig(newsection).reset(config)
                    self.filters.update_buttons()
                    self.filters.update_filters()
                    # select_filter must be done after update_filters
                    self.filters.select_filter(newsection)
                    break
                else:
                    newid += 1

        self.filters.apply_selected_filter()
        self.close()

    def preview(self, event):
        self.filters.list_.set_filter(self.compose_configuration())
        self.filters.list_.delay_restart()

    def cancel(self, event):
        self.close()
        self.filters.apply_selected_filter()

    def close(self):
        self.parent.GetSizer().Replace(self.panel, self.filters.panel)
        self.panel.Destroy()
        self.parent.GetSizer().Layout()

    def _init_filter_types(self):
        self.choice = wx.Choice(self.panel, size=(-1, 24), choices=())

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

        self.panel.Bind(wx.EVT_CHOICE, self.choose_filter_type, self.choice)

    def _init_selected_filter(self):
        self.sfilter = self.choice.GetClientData(self.choice.GetSelection()
                                                     )(self.panel, self.config)
        self.fbox.Add(self.sfilter.panel, flag=wx.EXPAND | wx.BOTTOM, border=4)

    def _init_common_options(self):
        try:
            self.aspadding = int(self.config['autoscroll'])
        except ValueError:
            self.aspadding = 1
            selas = 0
        else:
            selas = 1

        self.autoscroll = WidgetChoiceCtrl(self.panel,
                                                      (('No autoscroll', None),
              ('Autoscroll padding:', self._create_autoscroll_padding_widget)),
                                                                      selas, 4)
        self.autoscroll.force_update()
        self.fbox.Add(self.autoscroll.get_main_panel(), flag=wx.BOTTOM,
                                                                      border=4)

    def _create_autoscroll_padding_widget(self):
        self.aspaddingw = wx.SpinCtrl(self.autoscroll.get_main_panel(),
                          min=0, max=99, size=(40, 21), style=wx.SP_ARROW_KEYS)
        self.aspaddingw.SetValue(self.aspadding)

        return self.aspaddingw

    def choose_filter_type(self, event):
        fpanel = event.GetClientData()(self.panel, self.config)
        self.fbox.Replace(self.sfilter.panel, fpanel.panel)
        self.sfilter.panel.Destroy()
        self.sfilter = fpanel
        self.parent.Layout()


class FilterRelativeInterface():
    panel = None
    fgrid = None
    lowlimit = None
    highlimit = None
    values = None

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
        self.lowlimit.set_values(*TimeSpanCtrl._compute_widget_values(
                                                           self.values['low']))
        self.fgrid.Add(self.lowlimit.get_main_panel())

        highlabel = wx.StaticText(self.panel, label='High limit:')
        self.fgrid.Add(highlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # It must be possible to set up at least to 527039 minutes
        # (1 leap year - 1 minute)
        self.highlimit = TimeSpanCtrl(self.panel, -999999, 999999)
        self.highlimit.set_values(*TimeSpanCtrl._compute_widget_values(
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


class FilterAbsoluteInterface():
    panel = None
    fgrid = None
    lowlimit = None
    highlimit = None
    values = None

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


class FilterRegularInterface():
    panel = None
    fgrid = None
    base = None
    span = None
    advance = None
    values = None

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
        self.span.set_values(*TimeSpanCtrl._compute_widget_values(
                                                          self.values['span']))
        self.fgrid.Add(self.span.get_main_panel())

        advlabel = wx.StaticText(self.panel, label='Advance interval:')
        self.fgrid.Add(advlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # It must be possible to set up at least to 527039 minutes
        # (1 leap year - 1 minute)
        self.advance = TimeSpanCtrl(self.panel, 1, 999999)
        self.advance.set_values(*TimeSpanCtrl._compute_widget_values(
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


class FilterMonthStaticInterface():
    panel = None
    fgrid = None
    month = None
    span = None
    year = None
    values = None

    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=2, cols=3, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        today = _datetime.date.today()

        monthlabel = wx.StaticText(self.panel, label='Low month:')
        self.fgrid.Add(monthlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.month = wx.Choice(self.panel, size=(-1, 24), choices=('January',
                           'February', 'March', 'April', 'May', 'June', 'July',
                     'August', 'September', 'October', 'November', 'December'))
        self.month.SetSelection(self.values['month'] - 1)
        self.fgrid.Add(self.month)

        self.year = wx.SpinCtrl(self.panel, min=1970, max=9999,
                                         size=(60, 24), style=wx.SP_ARROW_KEYS)
        self.year.SetValue(self.values['year'])
        self.fgrid.Add(self.year)

        spanlabel = wx.StaticText(self.panel, label='Months span:')
        self.fgrid.Add(spanlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.span = wx.SpinCtrl(self.panel, min=1, max=999, size=(48, 21),
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


class FilterMonthDynamicInterface():
    panel = None
    fgrid = None
    month = None
    span = None
    advance = None
    values = None

    def __init__(self, parent, config):
        self.panel = wx.Panel(parent)

        self._init_config(config)

        self.fgrid = wx.FlexGridSizer(rows=3, cols=2, hgap=4, vgap=4)
        self.panel.SetSizer(self.fgrid)

        monthlabel = wx.StaticText(self.panel, label='Low month sample:')
        self.fgrid.Add(monthlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.month = wx.Choice(self.panel, size=(-1, 24), choices=('January',
                           'February', 'March', 'April', 'May', 'June', 'July',
                     'August', 'September', 'October', 'November', 'December'))
        today = _datetime.date.today()
        self.month.SetSelection(self.values['month'] - 1)
        self.fgrid.Add(self.month)

        spanlabel = wx.StaticText(self.panel, label='Months span:')
        self.fgrid.Add(spanlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # Note that FilterMonthDynamic.compute_limits only supports spans
        # <= 12 months
        self.span = wx.SpinCtrl(self.panel, min=1, max=12, size=(40, 21),
                                                        style=wx.SP_ARROW_KEYS)
        self.span.SetValue(self.values['span'])
        self.fgrid.Add(self.span)

        advlabel = wx.StaticText(self.panel, label='Advance interval:')
        self.fgrid.Add(advlabel, flag=wx.ALIGN_CENTER_VERTICAL)

        # Note that FilterMonthDynamic.compute_limits only supports intervals
        # <= 12 months
        self.advance = wx.SpinCtrl(self.panel, min=1, max=12, size=(40, 21),
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


class FilterRelative():
    low = None
    high = None

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
            # OccurrencesView.restart
            # Subtract `now % 60` so that the refresh will occur at an exact
            # minute
            return min(delays) - now % 60
        except ValueError:
            # delays could be empty
            return None


class FilterAbsolute():
    low = None
    high = None

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


class FilterRegular():
    base = None
    span = None
    advance = None

    def __init__(self, config):
        self.base = int(_time.mktime(_time.strptime(config['base'],
                                                            '%Y-%m-%dT%H:%M')))
        self.span = max(int(config['span']), 1) * 60
        self.advance = max(int(config['advance']), 1) * 60

    """
    * reference view (refmin, refmax)
    | reftime (now)
    [] target view (mintime, maxtime)

    --------(  *  )--------(     )--------(     )--------[  |  ]--------(     )-----
    mintime = reftime - ((reftime - refmin) % advance)
    mintime = reftime - ((reftime - refmax) % advance) + advance - refspan

    --------(  *  )--------(     )--------(     )-----|--[     ]--------(     )-----
    mintime = reftime - ((reftime - refmin) % advance) + advance
    mintime = reftime - ((reftime - refmax) % advance) + advance - refspan

    --------(     )--------(     )-----|--[     ]--------(     )--------(  *  )-----
    mintime = reftime + ((refmin - reftime) % advance)
    mintime = reftime + ((refmax - reftime) % advance) - refspan

    --------(     )--------[  |  ]--------(     )--------(     )--------(  *  )-----
    mintime = reftime + ((refmin - reftime) % advance) - advance
    mintime = reftime + ((refmax - reftime) % advance) - refspan

    --------(     )--------(     )--------[  |* ]--------(     )--------(     )-----
    mintime = refmin
    mintime = reftime - ((reftime - refmin) % advance)
    mintime = reftime + ((refmax - reftime) % advance) - refspan

    --------(  *  )--------(     )--------(     )--------|     ]--------(     )-----
    mintime = reftime
    mintime = reftime - ((reftime - refmin) % advance)
    mintime = reftime - ((reftime - refmax) % advance) + advance - refspan

    --------(  *  )--------(     )--------(     |--------[     ]--------(     )-----
    mintime = reftime - refspan + advance
    mintime = reftime - ((reftime - refmin) % advance) + advance
    mintime = reftime - ((reftime - refmax) % advance) + advance - refspan

    --------(     )--------(     )--------|     ]--------(     )--------(  *  )-----
    mintime = reftime
    mintime = reftime + ((refmin - reftime) % advance)
    mintime = reftime + ((refmax - reftime) % advance) - refspan

    --------(     |--------[     ]--------(     )--------(     )--------(  *  )-----
    mintime = reftime - refspan + advance
    mintime = reftime + ((refmin - reftime) % advance)
    mintime = reftime + ((refmax - reftime) % advance) - refspan + advance
    mintime = reftime - ((reftime - refmax) % advance) + advance - refspan

    --------(     )--------(     )--------|   * ]--------(     )--------(     )-----
    mintime = refmin = reftime
    mintime = reftime - ((reftime - refmin) % advance)
    mintime = reftime + ((refmax - reftime) % advance) - refspan


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
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime - ((reftime - refmax) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = reftime + ((refmin - reftime) % advance) - advance
    (not double checked!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = reftime
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime - ((reftime - refmax) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime - ((reftime - refmax) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = reftime
    mintime = reftime + ((refmin - reftime) % advance)
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance) + advance


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
    mintime = reftime + ((refmin - reftime) % advance) - advance
    (not double checked!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = refmin = reftime
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime + ((refmax - reftime) % advance) - refspan + ((refspan // advance) * advance) + advance

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
    mintime = reftime - ((reftime - refmin) % advance)
    (not double checked!) mintime = reftime - ((reftime - refmax) % advance) - refspan + ((refspan // advance) * advance) + advance
    """

    def compute_limits(self, now):
        # Use advance, *not* span, as the interval between two bases; this
        # allows for example to view only the 5 working days of the week and
        # still correctly advance to the next week, bypassing the weekend
        # See also the examples above
        # In case of overlapping spans, I want the most advanced (as opposed
        # to what e.g. happens when calculating item occurrences)
        if self.span >= self.advance:
            if now >= self.base:
                mint = now - (now - self.base) % self.advance
            else:
                rem = (self.base - now) % self.advance

                if rem > 0:
                    mint = now + rem - self.advance
                else:
                    mint = now
        else:
            if now > self.base:
                mint = now - (now - self.base - self.span) % self.advance + \
                                                       self.advance - self.span
            else:
                rem = (self.base + self.span - now) % self.advance

                if rem > 0:
                    mint = now + rem - self.span
                else:
                    mint = now + self.advance - self.span

        maxt = mint + self.span
        return (mint, maxt)

    def compute_delay(self, occsobj, now, mint, maxt):
        # Note that the delay can still be further limited in
        # OccurrencesView.restart
        return max(mint + self.advance - now, 0)


class FilterMonthStatic():
    month = None
    span = None
    year = None

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


class FilterMonthDynamic():
    month = None
    span = None
    advance = None

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
        # See also the examples above in FilterRegular
        # In case of overlapping spans, I want the most advanced
        if self.span >= self.advance:
            if nowrmonth >= rmonth:
                minrmonth = nowrmonth - (nowrmonth - rmonth) % self.advance
            else:
                rem = (rmonth - nowrmonth) % self.advance

                if rem > 0:
                    minrmonth = nowrmonth + rem - self.advance
                else:
                    minrmonth = nowrmonth
        else:
            if nowrmonth > rmonth:
                minrmonth = nowrmonth - (nowrmonth - rmonth - self.span) % \
                                        self.advance + self.advance - self.span
            else:
                rem = (rmonth + self.span - nowrmonth) % self.advance

                if rem > 0:
                    minrmonth = nowrmonth + rem - self.span
                else:
                    minrmonth = nowrmonth + self.advance - self.span

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
        # OccurrencesView.restart
        return max((delaydate - nowdate).total_seconds(), 0)
