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

import organism.plugins.wxscheduler_api as wxscheduler_api

import occur_once
import occur_every_day
import except_once


def handle_init_rules(kwargs):
    wxscheduler_api.initialize_rule(kwargs['filename'], kwargs['id_'],
                                    occur_once._RULE_DESC,
                                    occur_once._RULE_NAME)
    
    wxscheduler_api.initialize_rule(kwargs['filename'], kwargs['id_'],
                                    occur_every_day._RULE_DESC,
                                    occur_every_day._RULE_NAME)
    
    wxscheduler_api.initialize_rule(kwargs['filename'], kwargs['id_'],
                                    except_once._RULE_DESC,
                                    except_once._RULE_NAME)


def handle_choose_rule(kwargs):
    if kwargs['rule'] == occur_once._RULE_NAME:
        occur_once.choose_rule(kwargs)
    elif kwargs['rule'] == occur_every_day._RULE_NAME:
        occur_every_day.choose_rule(kwargs)
    elif kwargs['rule'] == except_once._RULE_NAME:
        except_once.choose_rule(kwargs)


def handle_apply_rule(kwargs):
    if kwargs['rule'] == occur_once._RULE_NAME:
        occur_once.apply_rule(kwargs)
    elif kwargs['rule'] == occur_every_day._RULE_NAME:
        occur_every_day.apply_rule(kwargs)
    elif kwargs['rule'] == except_once._RULE_NAME:
        except_once.apply_rule(kwargs)

 
def handle_insert_rule(kwargs):
    if kwargs['rule']['rule'] == occur_once._RULE_NAME:
        occur_once.insert_rule(kwargs)
    elif kwargs['rule']['rule'] == occur_every_day._RULE_NAME:
        occur_every_day.insert_rule(kwargs)
    elif kwargs['rule']['rule'] == except_once._RULE_NAME:
        except_once.insert_rule(kwargs)


def main():
    wxscheduler_api.bind_to_init_rules_list(handle_init_rules)
    wxscheduler_api.bind_to_choose_rule(handle_choose_rule)
    wxscheduler_api.bind_to_apply_rule(handle_apply_rule)
    wxscheduler_api.bind_to_insert_rule(handle_insert_rule)
