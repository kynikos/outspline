# wxClasses
# Copyright (C) 2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of wxClasses.
#
# wxClasses is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wxClasses is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with wxClasses.  If not, see <http://www.gnu.org/licenses/>.

import wx


class WidgetChoiceCtrl():
    panel = None
    box = None
    choicectrl = None
    activectrl = None

    def __init__(self, parent, choices, initchoice, rborder):
        self.panel = wx.Panel(parent)
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.box)

        self.choices = choices

        self.choicectrl = wx.Choice(self.panel, size=(-1, 21),
                                     choices=[choice[0] for choice in choices])
        self.choicectrl.Select(initchoice)
        self.box.Add(self.choicectrl, flag=wx.ALIGN_CENTER_VERTICAL |
                                          wx.EXPAND | wx.RIGHT, border=rborder)
        # Do not call self._update here, in fact classcall will very likely have
        # to use this very object, which at this stage hasn;'t been instantiated
        # yet; call self.force_update after the object is created, instead

        self.panel.Bind(wx.EVT_CHOICE, self._update, self.choicectrl)

    def _update(self, event=None):
        # self.activectrl may not exist yet
        if self.activectrl:
            self.activectrl.Destroy()

        classcall = self.choices[self.choicectrl.GetSelection()][1]

        if classcall:
            self.activectrl = classcall()

        # self.activectrl is None if sel == 0
        if self.activectrl:
            self.box.Add(self.activectrl)

        # self.panel.Layout() isn't enough...
        self.panel.GetParent().Layout()

    def force_update(self):
        self._update()

    def set_choice_min_width(self, width):
        minh = self.choicectrl.GetMinHeight()
        self.choicectrl.SetMinSize((width, minh))

    def get_main_panel(self):
        return self.panel

    def get_selection(self):
        return self.choicectrl.GetSelection()

    def get_choice_width(self):
        return self.choicectrl.GetSizeTuple()[0]


class MultipleChoiceCtrl():
    panel = None
    cbctrls = None

    def __init__(self, parent, choices):
        self.panel = wx.Panel(parent)
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)

        self.cbctrls = []

        for i, c in enumerate(choices):
            self.cbctrls.append(wx.CheckBox(self.panel))
            box.Add(self.cbctrls[i], flag=wx.ALIGN_CENTER_VERTICAL)

            label = wx.StaticText(self.panel, label=c)
            box.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT |
                                                            wx.RIGHT, border=8)

    def get_main_panel(self):
        return self.panel

    def set_values(self, values):
        for v, ctrl in enumerate(self.cbctrls):
            ctrl.SetValue(v + 1 in values)

    def get_values(self):
        return [v + 1 for v, ctrl in enumerate(self.cbctrls) if ctrl.GetValue()
                                                                              ]
