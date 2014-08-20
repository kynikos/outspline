# wxClasses
# Copyright (C) 2013-2014 Dario Giovannetti <dev@dariogiovannetti.net>
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


class WidgetChoiceCtrl(object):
    def __init__(self, parent, choices, initchoice, rborder,
                                                        layout_ancestors=1):
        self.panel = wx.Panel(parent)
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.box)

        self.choices = choices
        self.activectrl = None
        self.layout_ancestors = layout_ancestors

        self.choicectrl = wx.Choice(self.panel,
                                     choices=[choice[0] for choice in choices])
        self.set_selection(initchoice)
        self.box.Add(self.choicectrl, flag=wx.ALIGN_CENTER_VERTICAL |
                                                    wx.RIGHT, border=rborder)
        # Do not call self._update here, in fact classcall will very likely
        # have to use this very object, which at this stage hasn;'t been
        # instantiated yet; call self.force_update after the object is created,
        # instead

        self.panel.Bind(wx.EVT_CHOICE, self._handle_choice, self.choicectrl)

    def _handle_choice(self, event):
        self._update()

    def _update(self):
        # self.activectrl may not exist yet
        if self.activectrl:
            self.activectrl.Destroy()

        classcall = self.choices[self.choicectrl.GetSelection()][1]

        if classcall:
            self.activectrl = classcall()

        # self.activectrl is None if sel == 0
        if self.activectrl:
            self.box.Add(self.activectrl, flag=wx.ALIGN_CENTER_VERTICAL)

        window = self.panel

        for i in xrange(self.layout_ancestors):
            window = window.GetParent()

        window.Layout()

    def force_update(self):
        self._update()

    def set_choice_min_width(self, width):
        minh = self.choicectrl.GetMinHeight()
        self.choicectrl.SetMinSize((width, minh))

    def get_main_panel(self):
        return self.panel

    def get_selection(self):
        return self.choicectrl.GetSelection()

    def set_selection(self, choice):
        self.choicectrl.Select(choice)

    def get_choice_width(self):
        return self.choicectrl.GetSizeTuple()[0]


class MultipleChoiceCtrl(object):
    def __init__(self, parent, choices):
        self.panel = wx.Panel(parent)
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)

        self.cbctrls = []

        for i, c in enumerate(choices):
            self.cbctrls.append(wx.CheckBox(self.panel, label=c))
            box.Add(self.cbctrls[i], flag=wx.RIGHT, border=8)

    def get_main_panel(self):
        return self.panel

    def set_values(self, values):
        for v, ctrl in enumerate(self.cbctrls):
            ctrl.SetValue(v + 1 in values)

    def get_values(self):
        return [v + 1 for v, ctrl in enumerate(self.cbctrls) if ctrl.GetValue()
                                                                              ]
