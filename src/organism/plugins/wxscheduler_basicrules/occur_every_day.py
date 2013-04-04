# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import organism.plugins.wxscheduler_api as wxscheduler_api

_RULE_NAME = 'occur_every_day'
_RULE_DESC = 'Occur every day at time for time'

mwidgets = None


def choose_rule(kwargs):
    parent = kwargs['parent']
    
    # Create rule interface
    
    global mwidgets
    mwidgets = {}
    
    mpanel = wx.Panel(parent)
    
    pgrid = wx.GridBagSizer(4, 4)
    mpanel.SetSizer(pgrid)
    
    slabel = wx.StaticText(mpanel, label='At:')
    pgrid.Add(slabel, (0, 1), flag=wx.ALIGN_CENTER_VERTICAL)
    
    mwidgets['start_hour'] = wx.SpinCtrl(mpanel, min=0, max=23,
                                       size=(40, 21),
                                       style=wx.SP_ARROW_KEYS | wx.SP_WRAP)
    pgrid.Add(mwidgets['start_hour'], (0, 2),
              flag=wx.ALIGN_CENTER_VERTICAL)
    
    slabel = wx.StaticText(mpanel, label=':')
    pgrid.Add(slabel, (0, 3), flag=wx.ALIGN_CENTER_VERTICAL)
    
    mwidgets['start_minute'] = wx.SpinCtrl(mpanel, min=0, max=59,
                                       size=(40, 21),
                                       style=wx.SP_ARROW_KEYS | wx.SP_WRAP)
    pgrid.Add(mwidgets['start_minute'], (0, 4),
              flag=wx.ALIGN_CENTER_VERTICAL)
    
    mwidgets['end_chbox'] = wx.CheckBox(mpanel)
    pgrid.Add(mwidgets['end_chbox'], (1, 0))
    
    slabel = wx.StaticText(mpanel, label='For:')
    pgrid.Add(slabel, (1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
    
    mwidgets['end_number'] = wx.SpinCtrl(mpanel, min=1, max=99, size=(40, 21),
                                         style=wx.SP_ARROW_KEYS)
    pgrid.Add(mwidgets['end_number'], (1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
    
    mwidgets['end_unit'] = wx.ComboBox(mpanel, value='minutes', size=(100, 21),
                                       choices=('minutes', 'hours', 'days',
                                                'weeks', 'months', 'years'),
                                       style=wx.CB_READONLY)
    pgrid.Add(mwidgets['end_unit'], (1, 3), span=(1, 2),
              flag=wx.ALIGN_CENTER_VERTICAL)
    
    mwidgets['alarm_chbox'] = wx.CheckBox(mpanel)
    pgrid.Add(mwidgets['alarm_chbox'], (2, 0))
    
    slabel = wx.StaticText(mpanel, label='Alarm')
    pgrid.Add(slabel, (2, 1), span=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
    
    # Initialize values in interface
    
    # dict.get() returns None if key is not in dictionary, and it happens
    # when the interface is being set up for a new rule
    rstart = kwargs['ruled'].get('rstart')
    rendn = kwargs['ruled'].get('rendn')
    rendu = kwargs['ruled'].get('rendu')
    ralarm = kwargs['ruled'].get('ralarm')
    
    if rstart == None:
        rstart = int(_time.strftime('%H', _time.localtime())) * 3600 + 3600
    
    mwidgets['start_hour'].SetValue(rstart // 3600)
    mwidgets['start_minute'].SetValue(rstart % 3600 // 60)
    
    if rendn == None:
        mwidgets['end_chbox'].SetValue(False)
        rendn = 1
        rendu = 'hours'
        
        mwidgets['end_number'].Disable()
        mwidgets['end_unit'].Disable()
    else:
        mwidgets['end_chbox'].SetValue(True)
    
    mwidgets['end_number'].SetValue(rendn)
    mwidgets['end_unit'].SetValue(rendu)
    
    if ralarm == None:
        mwidgets['alarm_chbox'].SetValue(False)
    else:
        mwidgets['alarm_chbox'].SetValue(True)
    
    wxscheduler_api.change_rule(kwargs['filename'], kwargs['id_'], mpanel)
    
    mpanel.Bind(wx.EVT_CHECKBOX, handle_end_checkbox, mwidgets['end_chbox'])


def handle_end_checkbox(event):
    if event.IsChecked():
        mwidgets['end_number'].Enable()
        mwidgets['end_unit'].Enable()
    else:
        mwidgets['end_number'].Disable()
        mwidgets['end_unit'].Disable()


def apply_rule(kwargs):
    shour = mwidgets['start_hour'].GetValue()
    sminute = mwidgets['start_minute'].GetValue()
    
    rstart = shour * 3600 + sminute * 60
    
    if mwidgets['end_chbox'].GetValue():
        rendn = mwidgets['end_number'].GetValue()
        rendu = mwidgets['end_unit'].GetValue()
    else:
        rendn = None
        rendu = None
    
    if mwidgets['alarm_chbox'].GetValue():
        ralarm = 0
    else:
        ralarm = None
    
    create_rule(filename=kwargs['filename'], id_=kwargs['id_'], rstart=rstart,
                rendn=rendn, rendu=rendu, ralarm=ralarm)

 
def insert_rule(kwargs):
    rstart = kwargs['rule']['rstart']
    rendn = kwargs['rule']['rendn']
    rendu = kwargs['rule']['rendu']
    ralarm = kwargs['rule']['ralarm']
    
    rstart = int(rstart)
    
    if rendn == 'None':
        rendn = None
    else:
        rendn = int(rendn)
    
    if rendu == 'None':
        rendu = None
    
    if ralarm == 'None':
        ralarm = None
    else:
        ralarm = int(ralarm)
    
    create_rule(filename=kwargs['filename'], id_=kwargs['id_'], rstart=rstart,
                rendn=rendn, rendu=rendu, ralarm=ralarm)
    

def create_rule(filename, id_, rstart, rendn, rendu, ralarm):
    rstart = int(rstart)
    label = 'Occur every day at {}:{}'.format(str(rstart // 3600).zfill(2),
                                             str(rstart % 3600 // 60).zfill(2))
    
    if rendn != None:
        label += ' for {} {}'.format(rendn, rendu)
    
    if ralarm != None:
        label += ', alarm enabled'
    
    ruled = {'rule': _RULE_NAME,
             'rstart': rstart,
             'rendn': rendn,
             'rendu': rendu,
             'ralarm': ralarm}
    
    wxscheduler_api.insert_rule(filename, id_, ruled, label)
