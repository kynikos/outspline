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

import wxscheduler


def display_rule(filename, id_, description, rule):
    return wxscheduler.items[wxscheduler.Scheduler.make_itemid(filename, id_)
                             ].display_rule(description, rule)


def initialize_rule(filename, id_, rule):
    return wxscheduler.items[wxscheduler.Scheduler.make_itemid(filename, id_)
                             ].init_rule(rule)


def change_rule(filename, id_, sizer):
    return wxscheduler.items[wxscheduler.Scheduler.make_itemid(filename, id_)
                             ].change_rule(sizer)


def insert_rule(filename, id_, ruled, label):
    return wxscheduler.items[wxscheduler.Scheduler.make_itemid(filename, id_)
                             ].insert_rule(ruled, label)


def bind_to_init_rules_list(handler, bind=True):
    return wxscheduler.init_rules_list_event.bind(handler, bind)


def bind_to_choose_rule(handler, bind=True):
    return wxscheduler.choose_rule_event.bind(handler, bind)


def bind_to_apply_rule(handler, bind=True):
    return wxscheduler.apply_maker_event.bind(handler, bind)


def bind_to_insert_rule(handler, bind=True):
    return wxscheduler.insert_rule_event.bind(handler, bind)
