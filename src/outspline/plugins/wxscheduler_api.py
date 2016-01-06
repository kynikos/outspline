# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import outspline.interfaces.wxgui_api as wxgui_api

import wxscheduler


def display_rule(filename, id_, rule, description):
    return wxscheduler.base.get_scheduler(filename, id_
                                ).rule_editor.display_rule(rule, description)


def select_rule(filename, id_, interface_name):
    return wxscheduler.base.get_scheduler(filename, id_
                                    ).rule_editor.select_rule(interface_name)


def initialize_rule(filename, id_, rule):
    return wxscheduler.base.get_scheduler(filename, id_).rule_editor.init_rule(
                                                                        rule)


def change_rule(filename, id_, sizer):
    return wxscheduler.base.get_scheduler(filename, id_
                                            ).rule_editor.change_rule(sizer)


def insert_rule(filename, id_, ruled, label):
    return wxscheduler.base.get_scheduler(filename, id_).rule_list.insert_rule(
                                                                ruled, label)


def apply_rule(filename, id_, ruled, label):
    return wxscheduler.base.get_scheduler(filename, id_).rule_editor.apply_(
                                                                ruled, label)


def work_around_bug332(filename, id_):
    # Temporary workaround for bug #332
    return wxscheduler.base.get_scheduler(filename, id_).rule_editor.button_ok


def bind_to_init_rules_list(handler, bind=True):
    return wxscheduler.init_rules_list_event.bind(handler, bind)


def bind_to_create_rule(handler, bind=True):
    return wxscheduler.create_rule_event.bind(handler, bind)


def bind_to_edit_rule(handler, bind=True):
    return wxscheduler.edit_rule_event.bind(handler, bind)


def bind_to_choose_rule(handler, bind=True):
    return wxscheduler.choose_rule_event.bind(handler, bind)


def bind_to_apply_rule(handler, bind=True):
    return wxscheduler.check_editor_event.bind(handler, bind)


def bind_to_insert_rule(handler, bind=True):
    return wxscheduler.insert_rule_event.bind(handler, bind)


def simulate_expand_rules_panel(filename, id_):
    fpanel = wxscheduler.base.get_scheduler(filename, id_).fpanel
    wxgui_api.expand_panel(filename, id_, fpanel)

def simulate_remove_all_rules(filename, id_):
    sched = wxscheduler.base.get_scheduler(filename, id_)

    while sched.rule_list.listview.GetItemCount() > 0:
        sched.rule_list.listview.Select(0)
        sched.rule_list.remove_rule(None)
