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

import os as _os
import time as _time
import tkinter as _tk
from tkinter import N, E, S, W, X
from tkinter import ttk as _ttk
import constants
import databases
import queries
import timer
import editor
import items

alarmswindow = None


class AlarmsWindow():
    window = None
    frame = None
    bottom = None
    number = None
    unit = None
    alarms = None
    
    def __init__(self, parent):
        self.window = _tk.Toplevel(parent)
        self.alarms = {}
        
        self.hide()
        
        window = self.window
        window.title(constants._ALARMS_TITLE)
        window.geometry(constants._ALARMS_GEOMETRY)
        window.minsize(*constants._ALARMS_MIN_SIZE)
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)
        window.protocol("WM_DELETE_WINDOW", self.hide)
        
        self._init_frame(window)
        self._init_buttons(window)

    def _init_frame(self, parent):
        self.frame = _ttk.Frame(parent, padding=3)
        
        frame = self.frame
        frame.grid(column=0, row=0, sticky=(N, E, S, W))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _init_buttons(self, parent):
        self.bottom = _ttk.Frame(parent, padding=0)
        
        bottom = self.bottom
        bottom.grid(column=0, row=1, sticky=(N, E, S, W))
        bottom.columnconfigure(1, weight=1)
        
        snooze = _ttk.Frame(bottom, padding=(3, 3, 3, 0))
        snooze.grid(column=0, row=0, sticky=(S, W))
        
        label = _ttk.Label(snooze, text='Snooze configuration:')
        label.grid(column=0, row=0, sticky=(S, W))
        
        self.number = _tk.IntVar()
        self.number.set(5)
        numberw = _tk.Spinbox(snooze, from_=1, to=99, width=2,
                                                      textvariable=self.number)
        numberw.grid(column=1, row=0, sticky=(S, W))
        
        self.unit = _tk.StringVar()
        unitw = _ttk.Combobox(snooze, textvariable=self.unit, width=8,
                                                              state='readonly')
        unitw['values'] = ('minute(s)', 'hour(s)', 'day(s)', 'week(s)',
                                                         'month(s)', 'year(s)')
        unitw.current(0)
        unitw.grid(column=2, row=0, sticky=(S, W))
        
        buttons = _ttk.Frame(bottom, padding=3)
        buttons.grid(column=0, row=1, sticky=(S, W))
        
        button_s = _ttk.Button(buttons, text='Snooze all',
                                                       command=self.snooze_all)
        button_s.grid(column=0, row=0, sticky=(S, W))
        
        button_d = _ttk.Button(buttons, text='Dismiss all',
                                                      command=self.dismiss_all)
        button_d.grid(column=1, row=0, sticky=(S, W), padx=3)
        
        grip = _ttk.Sizegrip(bottom)
        grip.grid(column=1, row=1, sticky=(S, E))

    def show(self):
        self.window.deiconify()
        
    def hide(self):
        self.window.withdraw()
    
    def dismiss_all(self):
        databases.protection.block()
        group = databases.memory.get_next_history_group()
        for alarm in tuple(self.alarms.keys()):
            self.alarms[alarm].action(group=group, mode='dismiss')
        databases.protection.release()
    
    def snooze_all(self):
        databases.protection.block()
        group = databases.memory.get_next_history_group()
        for alarm in tuple(self.alarms.keys()):
            self.alarms[alarm].action(group=group, mode='snooze')
        databases.protection.release()
    
    def close_alarms(self, filename=None, id_=None):
        for alarm in tuple(self.alarms.keys()):
            afilename = self.alarms[alarm].get_filename()
            aid = self.alarms[alarm].get_id()
            if filename in (afilename, None) and id_ in (aid, None):
                self.alarms[alarm].close()

    def append(self, filename, id_, itemid, time, alarm):
        self.alarms[id_] = Alarm(self.frame, id_, filename, itemid, time,
                                                                         alarm)
        self.show()


class Alarm():
    frame = None
    id_ = None
    filename = None
    itemid = None
    time = None
    alarm = None
    
    def __init__(self, parent, id_, filename, itemid, time, alarm):
        self.frame = _ttk.Frame(parent, padding=3)
        self.id_ = id_
        self.filename = filename
        self.itemid = itemid
        self.time = time
        self.alarm = alarm
        
        frame = self.frame
        frame.pack(fill=X)
        frame.rowconfigure(1, pad=3)
        frame.columnconfigure(0, weight=1)
        frame['borderwidth'] = 1
        frame['relief'] = 'sunken'
        
        self._init_widgets(frame)
        
    def _init_widgets(self, parent):
        label = _ttk.Label(parent, text=_os.path.basename(self.filename))
        label.grid(column=0, row=0, sticky=(S, W))
        
        qconn = databases.dbs[self.filename].connection.get()
        cur = qconn.cursor()
        cur.execute(queries.items_select_id_editor, (self.itemid, ))
        text = cur.fetchone()['I_text']
        databases.dbs[self.filename].connection.give(qconn)
        text = text.partition('\n')[0]
        
        # Mostrare anche la data dell'evento (O_time) ****************************
        
        label = _ttk.Label(parent, text=text)
        label.grid(column=0, row=1, columnspan=2, sticky=(S, W))
        
        button_s = _ttk.Button(parent, text='Snooze', command=self.snooze)
        button_s.grid(column=1, row=0, sticky=(S, E), padx=3)
        
        button_d = _ttk.Button(parent, text='Dismiss', command=self.dismiss)
        button_d.grid(column=2, row=0, sticky=(S, E))
        
        button_e = _ttk.Button(parent, text='Open', command=self.open)
        button_e.grid(column=2, row=1, sticky=(S, E), padx=(3, 0))
    
    def snooze(self, group=None):
        databases.protection.block()
        self.action(group=group, mode='snooze')
        databases.protection.release()

    def dismiss(self, group=None):
        databases.protection.block()
        self.action(group=group, mode='dismiss')
        databases.protection.release()
    
    def action(self, group=None, mode=None):
        filename = self.filename
        alarm = self.alarm
        if mode == 'snooze':
            # Validare spinbox e combobox ****************************************
            mult = {'minute(s)': 60,
                    'hour(s)': 3600,
                    'day(s)': 86400,
                    'week(s)': 604800,
                    'month(s)': 2592000,
                    'year(s)': 31536000}
            # Se snoozo di n minuti l'allarme in generale non combacia più con ***
            #     i minuti esatti
            #   Controllare bene da tutte le parti che non facessi affidamento
            #     sulla separazione a minuti esatti anche per altri motivi
            newalarm = ((alarmswindow.number.get() *
                                                mult[alarmswindow.unit.get()] +
                                             int(_time.time())) // 60 + 1) * 60
        elif mode == 'dismiss':
            newalarm = 'NULL'
        if not group:
            group = databases.memory.get_next_history_group()
        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        query_redo = queries.occurrences_update_id_alarm.format(newalarm,  # @UndefinedVariable
                                                                      self.id_)
        query_undo = queries.occurrences_update_id_alarm.format(alarm,  # @UndefinedVariable
                                                                      self.id_)
        cursor.execute(query_redo)
        databases.dbs[filename].connection.give(qconn)
        qmemory = databases.memory.get()
        cursorh = qmemory.cursor()
        cursorh.execute(queries.history_insert, (group, filename, self.id_,
                                      'alarm', query_redo, '', query_undo, ''))
        databases.memory.give(qmemory)

        timer.refresh_timer()
        self.close()
    
    def close(self):
        self.frame.destroy()
        del alarmswindow.alarms[self.id_]
        
        if len(alarmswindow.alarms) == 0:
            alarmswindow.hide()
    
    def open(self):
        databases.protection.block()
        editor.Editor.open(items.Item.make_tree_id(self.filename, self.itemid))
        databases.protection.release()
    
    def get_filename(self):
        return(self.filename)
    
    def get_id(self):
        return(self.itemid)
