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

import organism.plugins.wxscheduler_api as wxscheduler_api

import occur_once
import occur_every_interval
import occur_every_day
import except_once


def handle_init_rules(kwargs):
    wxscheduler_api.display_rule(kwargs['filename'], kwargs['id_'],
                                 occur_once._RULE_DESC, 'occur_once')

    wxscheduler_api.display_rule(kwargs['filename'], kwargs['id_'],
                        occur_every_interval._RULE_DESC, 'occur_every_interval')

    wxscheduler_api.display_rule(kwargs['filename'], kwargs['id_'],
                                 occur_every_day._RULE_DESC, 'occur_every_day')

    wxscheduler_api.display_rule(kwargs['filename'], kwargs['id_'],
                                 except_once._RULE_DESC, 'except_once')


def handle_choose_rule(kwargs):
    parent = kwargs['parent']
    filename = kwargs['filename']
    id_ = kwargs['id_']
    name = kwargs['rule']
    ruled = kwargs['ruled']

    # If editing an existing rule, if the chosen new rule type is different from
    # the current rule type, use the default values for initializing the gui
    if name == ruled.get('rule'):
        rulev = ruled.get('#')
    else:
        rulev = None

    if name == 'occur_once':
        ruleobj = occur_once.Rule(parent, filename, id_, rulev)
    elif name == 'occur_every_interval':
        ruleobj = occur_every_interval.Rule(parent, filename, id_, rulev)
    elif name == 'occur_every_day':
        ruleobj = occur_every_day.Rule(parent, filename, id_, rulev)
    elif name == 'except_once':
        ruleobj = except_once.Rule(parent, filename, id_, rulev)

    wxscheduler_api.initialize_rule(filename, id_, ruleobj)


def handle_apply_rule(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']
    name = kwargs['rule']
    object_ = kwargs['object_']

    # In general the various rules could use different functions for handling
    # this event
    if name == 'occur_once':
        object_.apply_rule(filename, id_)
    elif name == 'occur_every_interval':
        object_.apply_rule(filename, id_)
    elif name == 'occur_every_day':
        object_.apply_rule(filename, id_)
    elif name == 'except_once':
        object_.apply_rule(filename, id_)


def handle_insert_rule(kwargs):
    filename = kwargs['filename']
    id_ = kwargs['id_']
    rule = kwargs['rule']
    name = rule['rule']
    rulev = rule['#']

    if name == 'occur_once':
        occur_once.Rule.insert_rule(filename, id_, rule, rulev)
    elif name == 'occur_every_interval':
        occur_every_interval.Rule.insert_rule(filename, id_, rule, rulev)
    elif name == 'occur_every_day':
        occur_every_day.Rule.insert_rule(filename, id_, rule, rulev)
    elif name == 'except_once':
        except_once.Rule.insert_rule(filename, id_, rule, rulev)


def main():
    wxscheduler_api.bind_to_init_rules_list(handle_init_rules)
    wxscheduler_api.bind_to_choose_rule(handle_choose_rule)
    wxscheduler_api.bind_to_apply_rule(handle_apply_rule)
    wxscheduler_api.bind_to_insert_rule(handle_insert_rule)
