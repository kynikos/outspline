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

import sys
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from outspline.coreaux_api import Event
import outspline.extensions.organism_api as organism_api
import outspline.interfaces.wxgui_api as wxgui_api

init_rules_list_event = Event()
insert_rule_event = Event()
create_rule_event = Event()
edit_rule_event = Event()
choose_rule_event = Event()
check_maker_event = Event()

items = {}


class Scheduler():
    filename = None
    id_ = None
    fpanel = None
    rpanel = None
    rbox = None
    rlist = None
    rulesl = None
    origrules = None
    rules = None
    rmaker = None
    rmaker_ref = None
    mbox = None
    mrules = None
    mmode = None
    mpanel = None
    choice = None
    choices = None

    def __init__(self, filename, id_):
        self.filename = filename
        self.id_ = id_

        self.fpanel = wxgui_api.add_plugin_to_editor(filename, id_,
                                                     'Schedule rules')

        self.rpanel = wx.Panel(self.fpanel)
        self.rbox = wx.BoxSizer(wx.VERTICAL)
        self.rpanel.SetSizer(self.rbox)

        wxgui_api.add_window_to_plugin(filename, id_, self.fpanel, self.rpanel)

    def post_init(self):
        self.choices = ()

        self._init_rules_list()
        self._init_rule_maker()

        self.refresh_mod_state()

        self.resize_rpanel()

        if not self.rules:
            wxgui_api.collapse_panel(self.filename, self.id_, self.fpanel)
            wxgui_api.resize_foldpanelbar(self.filename, self.id_)

        wxgui_api.bind_to_apply_editor(self.handle_apply)
        wxgui_api.bind_to_check_editor_modified_state(
                                             self.handle_check_editor_modified)
        wxgui_api.bind_to_close_editor(self.handle_close)

        init_rules_list_event.signal(filename=self.filename, id_=self.id_)

        self.choice.SetSelection(0)

    def handle_apply(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                        and self.is_modified():
            organism_api.update_item_rules(self.filename, self.id_,
                                            self.rules, kwargs['group'],
                                            kwargs['description'])
            self.refresh_mod_state()

    def handle_check_editor_modified(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_ \
                                                        and self.is_modified():
            wxgui_api.set_editor_modified(self.filename, self.id_)

    def handle_close(self, kwargs):
        if kwargs['filename'] == self.filename and kwargs['id_'] == self.id_:
            # It's necessary to explicitly unbind the handlers, otherwise this
            # object will never be garbage-collected due to circular
            # references, and the automatic unbinding won't work
            wxgui_api.bind_to_apply_editor(self.handle_apply, False)
            wxgui_api.bind_to_check_editor_modified_state(
                                      self.handle_check_editor_modified, False)
            wxgui_api.bind_to_close_editor(self.handle_close, False)

    def resize_rpanel(self):
        self.rpanel.Layout()
        self.rpanel.Fit()
        wxgui_api.collapse_panel(self.filename, self.id_, self.fpanel)
        wxgui_api.expand_panel(self.filename, self.id_, self.fpanel)
        wxgui_api.resize_foldpanelbar(self.filename, self.id_)

    def is_modified(self):
        return self.origrules != self.rules

    def refresh_mod_state(self):
        self.origrules = self.rules[:]

    def _init_rules_list(self):
        self.rlist = wx.Panel(self.rpanel)
        self.rbox.Add(self.rlist, proportion=1, flag=wx.EXPAND | wx.BOTTOM,
                                                                    border=4)

        pgrid = wx.GridBagSizer(4, 4)
        self.rlist.SetSizer(pgrid)
        pgrid.AddGrowableCol(0)

        # Note this class inherits ListView, which is a LitsCtrl interface
        # Do not allow multiple selections, so that it's possible to move rules
        # up and down
        self.rulesl = wx.ListView(self.rlist, style=wx.LC_REPORT |
                                  wx.LC_NO_HEADER | wx.LC_SINGLE_SEL |
                                  wx.SUNKEN_BORDER)
        self.rulesl.InsertColumn(0, 'Rules')
        pgrid.Add(self.rulesl, (0, 0), span=(3, 1), flag=wx.EXPAND)

        self.rules = []

        self.mmode = 'append'
        oprules = organism_api.get_item_rules(self.filename, self.id_)
        for rule in oprules:
            insert_rule_event.signal(filename=self.filename, id_=self.id_,
                                     rule=rule)

        self.button_up = wx.Button(self.rlist, label='Move up', size=(-1, 24),
                                   style=wx.BU_LEFT)
        pgrid.Add(self.button_up, (0, 1))

        self.button_remove = wx.Button(self.rlist, label='Remove',
                                       size=(-1, 24), style=wx.BU_LEFT)
        pgrid.Add(self.button_remove, (1, 1))

        self.button_down = wx.Button(self.rlist, label='Move down',
                                     size=(-1, 24), style=wx.BU_LEFT)
        pgrid.Add(self.button_down, (2, 1))

        self.button_add = wx.Button(self.rlist, label='Add...', size=(-1, 24),
                                    style=wx.BU_LEFT)
        pgrid.Add(self.button_add, (1, 2))

        self.button_edit = wx.Button(self.rlist, label='Edit...',
                                     size=(-1, 24), style=wx.BU_LEFT)
        pgrid.Add(self.button_edit, (2, 2))

        self.update_buttons()

        self.rlist.Bind(wx.EVT_BUTTON, self.add_rule, self.button_add)
        self.rlist.Bind(wx.EVT_BUTTON, self.edit_rule, self.button_edit)
        self.rlist.Bind(wx.EVT_BUTTON, self.remove_rule, self.button_remove)
        self.rlist.Bind(wx.EVT_BUTTON, self.move_rule_up, self.button_up)
        self.rlist.Bind(wx.EVT_BUTTON, self.move_rule_down, self.button_down)

        self.rulesl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.update_buttons)
        self.rulesl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.update_buttons)
        self.rulesl.Bind(wx.EVT_LIST_DELETE_ITEM, self.update_buttons)

    def update_buttons(self, event=None):
        if self.rulesl.GetSelectedItemCount():
            self.button_edit.Enable()
            self.button_remove.Enable()
            self.button_up.Enable()
            self.button_down.Enable()
        else:
            self.button_edit.Enable(False)
            self.button_remove.Enable(False)
            self.button_up.Enable(False)
            self.button_down.Enable(False)

    def add_rule(self, event):
        self.rlist.Show(False)

        self.mrules = {}
        self.mmode = 'append'

        create_rule_event.signal(filename=self.filename, id_=self.id_,
                                                             parent=self.rmaker)

        self.rmaker.Show()
        self.resize_rpanel()

    def edit_rule(self, event):
        index = self.rulesl.GetFirstSelected()
        if index != -1:
            self.rlist.Show(False)

            self.mrules = self.rules[index]
            self.mmode = index

            edit_rule_event.signal(filename=self.filename, id_=self.id_,
                                          parent=self.rmaker, ruled=self.mrules)

            self.rmaker.Show()
            self.resize_rpanel()

    def remove_rule(self, event):
        index = self.rulesl.GetFirstSelected()
        if index != -1:
            self.rulesl.DeleteItem(index)
            self.rulesl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            del self.rules[index]

    def move_rule_up(self, event):
        index = self.rulesl.GetFirstSelected()
        if index not in (-1, 0):
            self.rulesl.InsertStringItem(index - 1,
                                         self.rulesl.GetItemText(index))
            self.rulesl.DeleteItem(index + 1)
            self.rulesl.Select(index - 1)

            rule = self.rules.pop(index)
            self.rulesl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.rules.insert(index - 1, rule)

    def move_rule_down(self, event):
        index = self.rulesl.GetFirstSelected()
        if index not in (-1, self.rulesl.GetItemCount() - 1):
            self.rulesl.InsertStringItem(index + 2,
                                         self.rulesl.GetItemText(index))
            self.rulesl.DeleteItem(index)
            # Select *after* DeleteItem because DeleteItem deselects the
            # currently selected item (this doesn't happen in move_rule_up)
            self.rulesl.Select(index + 1)

            rule = self.rules.pop(index)
            self.rulesl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.rules.insert(index + 1, rule)

    def insert_rule(self, ruled, label):
        if self.mmode == 'append':
            self.rulesl.InsertStringItem(sys.maxint, label)

            # append relies on the use of sys.maxint in InsertStringItem
            self.rules.append(ruled)

        elif isinstance(self.mmode, int):
            self.rulesl.DeleteItem(self.mmode)
            self.rulesl.InsertStringItem(self.mmode, label)

            self.rules[self.mmode] = ruled

        self.rulesl.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def _init_rule_maker(self):
        self.rmaker = wx.Panel(self.rpanel)
        self.rbox.Add(self.rmaker, proportion=1, flag=wx.EXPAND | wx.BOTTOM,
                                                                    border=4)
        self.rmaker.Show(False)

        self.mbox = wx.BoxSizer(wx.VERTICAL)
        self.rmaker.SetSizer(self.mbox)

        mbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.mbox.Add(mbox2, flag=wx.EXPAND | wx.BOTTOM, border=4)

        self.choice = wx.Choice(self.rmaker, size=(-1, 24),
                                choices=self.choices)
        mbox2.Add(self.choice, 1, flag=wx.EXPAND)

        button_cancel = wx.Button(self.rmaker, label='Cancel', size=(60, 24))
        mbox2.Add(button_cancel, flag=wx.LEFT | wx.RIGHT, border=4)

        button_ok = wx.Button(self.rmaker, label='OK', size=(60, 24))
        mbox2.Add(button_ok)

        self.rmaker.Bind(wx.EVT_CHOICE, self.choose_rule, self.choice)
        self.rmaker.Bind(wx.EVT_BUTTON, self.cancel_maker, button_cancel)
        self.rmaker.Bind(wx.EVT_BUTTON, self.check_maker, button_ok)

    def display_rule(self, description, rule):
        self.choice.Append(description, clientData=rule)

    def select_rule(self, interface_name):
        for i in range(self.choice.GetCount()):
            if self.choice.GetClientData(i) == interface_name:
                self.choice.SetSelection(i)
                break

    def init_rule(self, rule):
        self.rmaker_ref = rule

    def choose_rule(self, event):
        choose_rule_event.signal(filename=self.filename, id_=self.id_,
                               parent=self.rmaker, choice=event.GetClientData(),
                                                              ruled=self.mrules)

    def change_rule(self, window):
        if self.mpanel:
            self.mbox.Remove(self.mpanel)
        self.mpanel = window
        self.mbox.Add(self.mpanel, 1, flag=wx.EXPAND)
        self.resize_rpanel()

    def cancel_maker(self, event):
        self.rmaker.Show(False)
        self.rlist.Show()
        self.resize_rpanel()

    def check_maker(self, event):
        check_maker_event.signal(filename=self.filename, id_=self.id_,
                                 rule=self.choice.GetClientData(
                                                    self.choice.GetSelection()),
                                 object_=self.rmaker_ref)

    def apply_maker(self, ruled, label):
        self.rmaker.Show(False)
        self.insert_rule(ruled, label)
        self.rlist.Show()
        self.resize_rpanel()

    @staticmethod
    def make_itemid(filename, id_):
        return '_'.join((filename, str(id_)))


def handle_open_editor(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']

    if filename in organism_api.get_supported_open_databases():
        global items
        items[Scheduler.make_itemid(filename, id_)] = Scheduler(filename, id_)
        items[Scheduler.make_itemid(filename, id_)].post_init()


def main():
    wxgui_api.bind_to_open_editor(handle_open_editor)
