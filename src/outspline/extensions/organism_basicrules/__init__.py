# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2014 Dario Giovannetti <dev@dariogiovannetti.net>
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

import outspline.extensions.organism_api as organism_api
import outspline.extensions.organism_timer_api as organism_timer_api

import occur_once
import occur_regularly_single
import occur_regularly_group
import occur_monthly_number_direct
import occur_monthly_number_inverse
import occur_monthly_weekday_direct
import occur_monthly_weekday_inverse
import occur_yearly_single
import occur_yearly_group
import except_once
import except_regularly_single


def install_next_occurrence_handlers():
    for rulename, handler in (
            (occur_once._RULE_NAMES['local'],
                occur_once.get_next_item_occurrences_local),
            (occur_once._RULE_NAMES['UTC'],
                occur_once.get_next_item_occurrences_UTC),
            (occur_regularly_single._RULE_NAMES['local'],
                occur_regularly_single.get_next_item_occurrences_local),
            (occur_regularly_single._RULE_NAMES['UTC'],
                occur_regularly_single.get_next_item_occurrences_UTC),
            (occur_regularly_group._RULE_NAMES['local'],
                occur_regularly_group.get_next_item_occurrences_local),
            (occur_regularly_group._RULE_NAMES['UTC'],
                occur_regularly_group.get_next_item_occurrences_UTC),
            (occur_monthly_number_direct._RULE_NAMES['local'],
                occur_monthly_number_direct.get_next_item_occurrences_local),
            (occur_monthly_number_direct._RULE_NAMES['UTC'],
                occur_monthly_number_direct.get_next_item_occurrences_UTC),
            (occur_monthly_number_inverse._RULE_NAMES['local'],
                occur_monthly_number_inverse.get_next_item_occurrences_local),
            (occur_monthly_number_inverse._RULE_NAMES['UTC'],
                occur_monthly_number_inverse.get_next_item_occurrences_UTC),
            (occur_monthly_weekday_direct._RULE_NAMES['local'],
                occur_monthly_weekday_direct.get_next_item_occurrences_local),
            (occur_monthly_weekday_direct._RULE_NAMES['UTC'],
                occur_monthly_weekday_direct.get_next_item_occurrences_UTC),
            (occur_monthly_weekday_inverse._RULE_NAMES['local'],
                occur_monthly_weekday_inverse.get_next_item_occurrences_local),
            (occur_monthly_weekday_inverse._RULE_NAMES['UTC'],
                occur_monthly_weekday_inverse.get_next_item_occurrences_UTC),
            (occur_yearly_single._RULE_NAMES['local'],
                occur_yearly_single.get_next_item_occurrences_local),
            (occur_yearly_single._RULE_NAMES['UTC'],
                occur_yearly_single.get_next_item_occurrences_UTC),
            (occur_yearly_group._RULE_NAMES['local'],
                occur_yearly_group.get_next_item_occurrences_local),
            (occur_yearly_group._RULE_NAMES['UTC'],
                occur_yearly_group.get_next_item_occurrences_UTC),
            (except_once._RULE_NAMES['local'],
                except_once.get_next_item_occurrences_local),
            (except_once._RULE_NAMES['UTC'],
                except_once.get_next_item_occurrences_UTC),
            (except_regularly_single._RULE_NAMES['local'],
                except_regularly_single.get_next_item_occurrences_local),
            (except_regularly_single._RULE_NAMES['UTC'],
                except_regularly_single.get_next_item_occurrences_UTC),
            ):
        organism_timer_api.install_rule_handler(rulename, handler)


def install_occurrence_range_handlers():
    for rulename, handler in (
                (occur_once._RULE_NAMES['local'],
                    occur_once.get_occurrences_range_local),
                (occur_once._RULE_NAMES['UTC'],
                    occur_once.get_occurrences_range_UTC),
                (occur_regularly_single._RULE_NAMES['local'],
                    occur_regularly_single.get_occurrences_range_local),
                (occur_regularly_single._RULE_NAMES['UTC'],
                    occur_regularly_single.get_occurrences_range_UTC),
                (occur_regularly_group._RULE_NAMES['local'],
                    occur_regularly_group.get_occurrences_range_local),
                (occur_regularly_group._RULE_NAMES['UTC'],
                    occur_regularly_group.get_occurrences_range_UTC),
                (occur_monthly_number_direct._RULE_NAMES['local'],
                    occur_monthly_number_direct.get_occurrences_range_local),
                (occur_monthly_number_direct._RULE_NAMES['UTC'],
                    occur_monthly_number_direct.get_occurrences_range_UTC),
                (occur_monthly_number_inverse._RULE_NAMES['local'],
                    occur_monthly_number_inverse.get_occurrences_range_local),
                (occur_monthly_number_inverse._RULE_NAMES['UTC'],
                    occur_monthly_number_inverse.get_occurrences_range_UTC),
                (occur_monthly_weekday_direct._RULE_NAMES['local'],
                    occur_monthly_weekday_direct.get_occurrences_range_local),
                (occur_monthly_weekday_direct._RULE_NAMES['UTC'],
                    occur_monthly_weekday_direct.get_occurrences_range_UTC),
                (occur_monthly_weekday_inverse._RULE_NAMES['local'],
                    occur_monthly_weekday_inverse.get_occurrences_range_local),
                (occur_monthly_weekday_inverse._RULE_NAMES['UTC'],
                    occur_monthly_weekday_inverse.get_occurrences_range_UTC),
                (occur_yearly_single._RULE_NAMES['local'],
                    occur_yearly_single.get_occurrences_range_local),
                (occur_yearly_single._RULE_NAMES['UTC'],
                    occur_yearly_single.get_occurrences_range_UTC),
                (occur_yearly_group._RULE_NAMES['local'],
                    occur_yearly_group.get_occurrences_range_local),
                (occur_yearly_group._RULE_NAMES['UTC'],
                    occur_yearly_group.get_occurrences_range_UTC),
                (except_once._RULE_NAMES['local'],
                    except_once.get_occurrences_range_local),
                (except_once._RULE_NAMES['UTC'],
                    except_once.get_occurrences_range_UTC),
                (except_regularly_single._RULE_NAMES['local'],
                    except_regularly_single.get_occurrences_range_local),
                (except_regularly_single._RULE_NAMES['UTC'],
                    except_regularly_single.get_occurrences_range_UTC),
            ):
        organism_api.install_rule_handler(rulename, handler)


def main():
    install_occurrence_range_handlers()
    install_next_occurrence_handlers()
