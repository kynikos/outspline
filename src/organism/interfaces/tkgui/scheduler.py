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
import tkinter as _tk
from tkinter import ttk as _ttk
from tkinter import N, E, S, W
import databases
import queries
import editor
import constants
import items

panels = {}


class Scheduler():
    frame = None
    variables = None
    originals = None
    widgets = None
    item = None
    filename = None
    id_ = None
    
    def __init__(self, item):
        # Validare i valori inseriti *********************************************
        #    usare le funzioni apposite di Tk
        #        ad esempio Spinbox ha validateCommand
        # Disabilitare alarm quando start non è selezionato **********************
        
        self.variables = {}
        self.originals = {}
        self.widgets = {}
        
        self.frame = _ttk.Frame(editor.tabs[item].frame)
        
        frame = self.frame
        frame.grid(column=1, row=0, sticky=(N, E, S, W))
        
        self.item = item
        self.id_ = items.items[item].get_id()
        self.filename = items.items[item].get_filename()
        
    def _post_init(self):
        filename = self.filename
        id_ = self.id_
        variables = self.variables
        widgets = self.widgets
        
        qconn = databases.dbs[filename].connection.get()
        cursor = qconn.cursor()
        cursor.execute(queries.items_select_id_scheduler, (id_, ))
        row = cursor.fetchone()
        databases.dbs[filename].connection.give(qconn)
        
        ### START DATE ###
        variables['start_chbox'] = _tk.IntVar()
        variables['start_year'] = _tk.IntVar()
        variables['start_month'] = _tk.IntVar()
        variables['start_day'] = _tk.IntVar()
        variables['start_hour'] = _tk.IntVar()
        variables['start_minute'] = _tk.IntVar()
        
        # Ripristina il codice per settare il tempo alla prossima ora nel caso ***
        #     in cui il promemoria non sia mai stato attivato?
        secs = _time.localtime(row['I_start_time'])
        variables['start_chbox'].set(row['I_start_bool'])
        variables['start_year'].set(_time.strftime('%Y', secs))
        variables['start_month'].set(_time.strftime('%m', secs))
        variables['start_day'].set(_time.strftime('%d', secs))
        variables['start_hour'].set(_time.strftime('%H', secs))
        variables['start_minute'].set(_time.strftime('%M', secs))
        
        widgets['start_label'] = _ttk.Label(self.frame, text='Start:')
        widgets['start_chbox'] = _ttk.Checkbutton(self.frame,
                                             variable=variables['start_chbox'])
        widgets['start_year'] = _tk.Spinbox(self.frame, from_=2000,
                                                  to=2100, width=4, wrap=False,
                                          textvariable=variables['start_year'])
        widgets['start_month'] = _tk.Spinbox(self.frame, from_=1, to=12,
                                                            width=2, wrap=True,
                                         textvariable=variables['start_month'])
        widgets['start_day'] = _tk.Spinbox(self.frame, from_=1, to=31,
                                                            width=2, wrap=True,
                                           textvariable=variables['start_day'])
        widgets['start_hour'] = _tk.Spinbox(self.frame, from_=0, to=23,
                                                            width=2, wrap=True,
                                          textvariable=variables['start_hour'])
        widgets['start_minute'] = _tk.Spinbox(self.frame, from_=0, to=59,
                     increment=constants._MINUTE_INCREMENT, width=2, wrap=True,
                                        textvariable=variables['start_minute'])
        
        widgets['start_label'].grid(column=0, row=0, sticky=(N, E))
        widgets['start_chbox'].grid(column=1, row=0, sticky=N)
        widgets['start_year'].grid(column=2, row=0, sticky=N)
        widgets['start_month'].grid(column=3, row=0, sticky=N)
        widgets['start_day'].grid(column=4, row=0, sticky=N)
        widgets['start_hour'].grid(column=5, row=0, sticky=N)
        widgets['start_minute'].grid(column=6, row=0, sticky=N)
        
        ### ALARM ###
        variables['alarm_chbox'] = _tk.IntVar()
        
        variables['alarm_chbox'].set(row['I_alarm'])
        
        widgets['alarm_label'] = _ttk.Label(self.frame, text='Alarm:')
        widgets['alarm_chbox'] = _ttk.Checkbutton(self.frame,
                                             variable=variables['alarm_chbox'])
        
        widgets['alarm_label'].grid(column=0, row=1, sticky=(N, E))
        widgets['alarm_chbox'].grid(column=1, row=1, sticky=N)
        
        ### ORIGINAL VALUES ###
        # Always keep this after all variables[item] assignations
        self.refresh_originals()
    
    @classmethod
    def open(cls, item):
        global panels
        panels[item] = cls(item)
        panels[item]._post_init()
    
    def refresh_originals(self):
        for key in self.variables:
            self.originals[key] = self.variables[key].get()

    def get_start_time(self):
        t = _time.strptime(' '.join((str(self.variables['start_year'].get()),
                                      str(self.variables['start_month'].get()),
                                        str(self.variables['start_day'].get()),
                                       str(self.variables['start_hour'].get()),
                                   str(self.variables['start_minute'].get()))),
                                                              '%Y %m %d %H %M')
        return(int(_time.mktime(t)))

    @staticmethod
    def set_start_time():
        # Usare questa funzione solo nel caso in cui il promemoria non sia mai ***
        #     stato attivato?
        # Create child e create sibling non possono settare start_time a *********
        #     'NULL', altrimenti si verificano dei bug quando si tenta di
        #     leggere il valore e poi di riscriverlo con alcune query
        #   mettere '0'? Non sarebbe molto elegante, infatti un eventuale
        #     seppur improbabile promemoria al 1-1-1970 non verrebbe letto bene
        t = (int(_time.time()) // 3600 + 1) * 3600
        return(t)

    def is_modified(self):
        for key in self.variables:
            if self.variables[key].get() != self.originals[key]:
                return True
        else:
            return False

    def apply(self):
        start_bool = self.variables['start_chbox'].get()
        start_time = self.get_start_time()
        alarm = self.variables['alarm_chbox'].get()
        items.items[self.item].calculate_occurrences(start_bool, start_time,
                                                                         alarm)
        values = {'start_bool': start_bool,
                  'start_time': start_time,
                  'alarm': alarm}
        return(values)
