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

import wx

import organism.core_api as core_api
import organism.coreaux_api as coreaux_api

config = coreaux_api.get_interface_configuration('wxgui')

# Use a copy of the original constant, so that every time a database is opened
# it reads the current value, and not the one stored in the configuration
# Do not put this into the class, since it must be an instance-independent
# value
_show_history = config.get_bool('show_history')


class HistoryWindow(wx.ScrolledWindow):
    filename = None
    events = None
    box = None
    
    def __init__(self, parent, filename):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetScrollRate(20, 20)
        
        self.filename = filename
        self.events = {}
        
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.box)
        
        self.refresh()
    
    def refresh(self):
        self.box.Clear(True)
        
        descriptions = core_api.get_history_descriptions(self.filename)
        for row in descriptions:
            st = wx.StaticText(self, label=''.join(('[', str(row['H_status']),
                                                    '] ',
                                                    row['H_description'])))
            self.events[row['H_group']] = {'status': row['H_status'],
                                            'st': st}
            self.box.Add(st)
        
        self.Layout()
        self.box.FitInside(self)


def is_shown():
    return _show_history


def set_shown(flag=True):
    global _show_history
    _show_history = flag
