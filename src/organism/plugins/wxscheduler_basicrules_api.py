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

import organism.extensions.organizer_basicrules_api as organizer_basicrules_api

import wxscheduler_basicrules


def create_random_occur_once_rule():
    return wxscheduler_basicrules.occur_once.Rule.create_random_rule()


def create_random_occur_every_interval_rule():
    return wxscheduler_basicrules.occur_every_interval.Rule.create_random_rule()


def create_random_occur_every_day_rule():
    return wxscheduler_basicrules.occur_every_day.Rule.create_random_rule()


def create_random_occur_every_week_rule():
    return wxscheduler_basicrules.occur_every_week.Rule.create_random_rule()


def create_random_occur_selected_months_rule():
    return wxscheduler_basicrules.occur_selected_months.Rule.create_random_rule()


def create_random_occur_selected_months_inverse_rule():
    return wxscheduler_basicrules.occur_selected_months_inverse.Rule.create_random_rule()


def create_random_except_once_rule():
    return wxscheduler_basicrules.except_once.Rule.create_random_rule()


def simulate_create_occur_once_rule(filename, id_, rule):
    wxscheduler_basicrules.occur_once.Rule.insert_rule(filename, id_, rule,
                                                                      rule['#'])


def simulate_create_occur_every_interval_rule(filename, id_, rule):
    wxscheduler_basicrules.occur_every_interval.Rule.insert_rule(filename, id_,
                                                                rule, rule['#'])


def simulate_create_occur_every_day_rule(filename, id_, rule):
    wxscheduler_basicrules.occur_every_day.Rule.insert_rule(filename, id_, rule,
                                                                      rule['#'])


def simulate_create_occur_every_week_rule(filename, id_, rule):
    wxscheduler_basicrules.occur_every_week.Rule.insert_rule(filename, id_,
                                                                rule, rule['#'])


def simulate_create_occur_selected_months_rule(filename, id_, rule):
    wxscheduler_basicrules.occur_selected_months.Rule.insert_rule(filename, id_,
                                                                rule, rule['#'])


def simulate_create_occur_selected_months_inverse_rule(filename, id_, rule):
    wxscheduler_basicrules.occur_selected_months_inverse.Rule.insert_rule(
                                                 filename, id_, rule, rule['#'])


def simulate_create_except_once_rule(filename, id_, rule):
    wxscheduler_basicrules.except_once.Rule.insert_rule(filename, id_, rule,
                                                                      rule['#'])
