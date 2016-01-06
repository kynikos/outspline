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

import collections

import outspline.plugins.wxscheduler_api as wxscheduler_api

import occur_once
import occur_every_interval
import occur_every_day
import occur_every_week
import occur_selected_weekdays
import occur_selected_months
import occur_selected_months_inverse
import occur_selected_months_weekday
import occur_selected_months_weekday_inverse
import occur_every_month
import occur_every_month_inverse
import occur_every_month_weekday
import occur_every_month_weekday_inverse
import occur_every_synodic_month
import occur_yearly
import except_once
import except_every_interval


class Main(object):
    def __init__(self):
        self.interfaces_to_data = collections.OrderedDict((
            ('occur_once', ('Occur once', occur_once)),
            ('occur_every_interval', ('Occur at regular time intervals',
                                                        occur_every_interval)),
            ('occur_every_day', ('Occur every day', occur_every_day)),
            ('occur_every_week', ('Occur every week', occur_every_week)),
            ('occur_selected_weekdays', ('Occur on selected days of the week',
                                                    occur_selected_weekdays)),
            ('occur_selected_months',
                                ('Occur on the n-th day of selected months',
                                occur_selected_months)),
            ('occur_selected_months_inverse',
                ('Occur on the n-th-to-last day of selected months',
                                            occur_selected_months_inverse)),
            ('occur_selected_months_weekday',
                ('Occur on the n-th weekday of selected months',
                                            occur_selected_months_weekday)),
            ('occur_selected_months_weekday_inverse',
                ('Occur on the n-th-to-last weekday of selected months',
                                    occur_selected_months_weekday_inverse)),
            ('occur_every_month', ('Occur on the n-th day of every month',
                                                        occur_every_month)),
            ('occur_every_month_inverse',
                ('Occur on the n-th-to-last day of every month',
                                                occur_every_month_inverse)),
            ('occur_every_month_weekday',
                ('Occur on the n-th weekday of every month',
                                                occur_every_month_weekday)),
            ('occur_every_month_weekday_inverse',
                ('Occur on the n-th-to-last weekday of every month',
                                        occur_every_month_weekday_inverse)),
            ('occur_every_synodic_month', ('Occur every mean synodic month',
                                                occur_every_synodic_month)),
            ('occur_yearly', ('Occur every n years', occur_yearly)),
            ('except_once', ('Except once', except_once)),
            ('except_every_interval', ('Except at regular time intervals',
                                                    except_every_interval)),
        ))

        rules_to_data = {
            ('occur_once_local', 'occur_once_UTC'):
                (None, {None: 'occur_once'}),
            ('occur_regularly_local', 'occur_regularly_UTC'):
                (6, {'1d': 'occur_every_day',
                     '1w': 'occur_every_week',
                     'sy': 'occur_every_synodic_month',
                     None: 'occur_every_interval'}),
            ('occur_regularly_group_local', 'occur_regularly_group_UTC'):
                (6, {'sw': 'occur_selected_weekdays'}),
                     # No 'None' case here for the moment
            ('occur_monthly_number_direct_local',
                                            'occur_monthly_number_direct_UTC'):
                (7, {'1m': 'occur_every_month',
                     None: 'occur_selected_months'}),
            ('occur_monthly_number_inverse_local',
                                        'occur_monthly_number_inverse_UTC'):
                (7, {'1m': 'occur_every_month_inverse',
                     None: 'occur_selected_months_inverse'}),
            ('occur_monthly_weekday_direct_local',
                                        'occur_monthly_weekday_direct_UTC'):
                (8, {'1m': 'occur_every_month_weekday',
                     None: 'occur_selected_months_weekday'}),
            ('occur_monthly_weekday_inverse_local',
                                        'occur_monthly_weekday_inverse_UTC'):
                (8, {'1m': 'occur_every_month_weekday_inverse',
                     None: 'occur_selected_months_weekday_inverse'}),
            ('occur_yearly_local', 'occur_yearly_UTC'):
                (None, {None: 'occur_yearly'}),
            ('except_once_local', 'except_once_UTC'):
                (None, {None: 'except_once'}),
            ('except_regularly_local', 'except_regularly_UTC'):
                (None, {None: 'except_every_interval'}),
        }

        self.rules_to_interfaces = {rule_names[0]:
                                        ('local', rules_to_data[rule_names][0],
                                        rules_to_data[rule_names][1])
                                        for rule_names in rules_to_data}
        self.rules_to_interfaces.update({rule_names[1]:
                                        ('UTC', rules_to_data[rule_names][0],
                                        rules_to_data[rule_names][1])
                                        for rule_names in rules_to_data})

        self.interfaces_to_rules = {}

        for rule_name in self.rules_to_interfaces:
            rule_standard, rule_conf_index, rule_interfaces = \
                                            self.rules_to_interfaces[rule_name]

            for rule_interface_tag in rule_interfaces:
                interface_name = rule_interfaces[rule_interface_tag]

                try:
                    self.interfaces_to_rules[interface_name]
                except KeyError:
                    self.interfaces_to_rules[interface_name] = (
                                    rule_conf_index, rule_interface_tag, {})

                self.interfaces_to_rules[interface_name][2][rule_name] = \
                                                                rule_standard

        wxscheduler_api.bind_to_init_rules_list(self._handle_init_rules)
        wxscheduler_api.bind_to_create_rule(self._handle_create_rule)
        wxscheduler_api.bind_to_edit_rule(self._handle_edit_rule)
        wxscheduler_api.bind_to_choose_rule(self._handle_choose_rule)
        wxscheduler_api.bind_to_apply_rule(self._handle_apply_rule)
        wxscheduler_api.bind_to_insert_rule(self._handle_insert_rule)

    def _handle_init_rules(self, kwargs):
        for interface in self.interfaces_to_data:
            wxscheduler_api.display_rule(kwargs['filename'], kwargs['id_'],
                            interface, self.interfaces_to_data[interface][0])

    def _handle_create_rule(self, kwargs):
        parent = kwargs['parent']
        filename = kwargs['filename']
        id_ = kwargs['id_']

        # occur_once is default
        rule_object = occur_once.Rule(parent, filename, id_, 'local', None)
        interface_name = 'occur_once'

        wxscheduler_api.initialize_rule(filename, id_, rule_object)
        wxscheduler_api.select_rule(filename, id_, interface_name)

    def _handle_edit_rule(self, kwargs):
        parent = kwargs['parent']
        filename = kwargs['filename']
        id_ = kwargs['id_']
        ruled = kwargs['ruled']

        rule_name = ruled['rule']
        rule_parameters = ruled['#']

        try:
            rule_standard, rule_conf_index, rule_interfaces = \
                                            self.rules_to_interfaces[rule_name]
        except KeyError:
            # The rule is not handled by this plugin
            pass
        else:
            try:
                rule_interface_tag = rule_parameters[rule_conf_index][0]
            except TypeError:
                rule_interface_tag = None

            try:
                rule_interface_name = rule_interfaces[rule_interface_tag]
            except KeyError:
                # The rule is not handled by this plugin
                pass
            else:
                rule_interface_module = self.interfaces_to_data[
                                                        rule_interface_name][1]
                rule_object = rule_interface_module.Rule(parent, filename, id_,
                                                rule_standard, rule_parameters)

                wxscheduler_api.initialize_rule(filename, id_, rule_object)
                wxscheduler_api.select_rule(filename, id_, rule_interface_name)

    def _handle_choose_rule(self, kwargs):
        parent = kwargs['parent']
        filename = kwargs['filename']
        id_ = kwargs['id_']
        ruled = kwargs['ruled']
        choice = kwargs['choice']

        try:
            interface_module = self.interfaces_to_data[choice][1]
        except KeyError:
            # The interface is not handled by this plugin
            pass
        else:
            standard = 'local'
            parameters = None

            try:
                rule_name = ruled['rule']
                rule_parameters = ruled['#']
            except KeyError:
                # A new rule is being created, or the edited rule doesn't use
                # 'rule' and '#'
                pass
            else:
                rule_conf_index, rule_conf_interface_tag, rule_conf_names = \
                                            self.interfaces_to_rules[choice]

                try:
                    rule_conf_standard = rule_conf_names[rule_name]
                except KeyError:
                    # The chosen interface doesn't handle the edited rule
                    pass
                else:
                    try:
                        rule_interface_tag = rule_parameters[rule_conf_index][
                                                                            0]
                    except TypeError:
                        # The edited rule doesn't have a configuration for the
                        # interface
                        standard = rule_conf_standard
                        parameters = rule_parameters
                    else:
                        if rule_interface_tag == rule_conf_interface_tag:
                            standard = rule_conf_standard
                            parameters = rule_parameters

            rule_object = interface_module.Rule(parent, filename, id_,
                                                        standard, parameters)
            wxscheduler_api.initialize_rule(filename, id_, rule_object)

    def _handle_apply_rule(self, kwargs):
        filename = kwargs['filename']
        id_ = kwargs['id_']
        interface_name = kwargs['rule']
        object_ = kwargs['object_']

        object_.apply_rule(filename, id_)

    def _handle_insert_rule(self, kwargs):
        filename = kwargs['filename']
        id_ = kwargs['id_']
        rule = kwargs['rule']

        rule_name = rule['rule']
        rule_parameters = rule['#']

        try:
            rule_standard, rule_conf_index, rule_interfaces = \
                                            self.rules_to_interfaces[rule_name]
        except KeyError:
            # The rule is not handled by this plugin
            pass
        else:
            try:
                rule_interface_tag = rule_parameters[rule_conf_index][0]
            except TypeError:
                rule_interface_tag = None

            try:
                rule_interface_name = rule_interfaces[rule_interface_tag]
            except KeyError:
                # The rule is not handled by this plugin
                pass
            else:
                rule_interface_module = self.interfaces_to_data[
                                                        rule_interface_name][1]
                rule_interface_module.Rule.insert_rule(filename, id_, rule,
                                                            rule_parameters)

def main():
    Main()
