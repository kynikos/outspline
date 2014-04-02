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

from exceptions import BadRuleError

_RULE_NAMES = {'local': 'except_once_local',
               'UTC': 'except_once_UTC'}


def make_rule(start, end, inclusive, standard, guiconfig):
    # Make sure this rule can only produce occurrences compliant with the
    #   requirements defined in organism_api.update_item_rules
    # There's no need to check standard because it's imposed by the API
    if isinstance(start, int) and isinstance(end, int) and end > start and \
                                                isinstance(inclusive, bool):
        return {
            'rule': _RULE_NAMES[standard],
            '#': (
                start,
                end,
                inclusive,
                guiconfig
            )
        }
    else:
        raise BadRuleError


def get_occurrences_range_local(mint, maxt, utcoffset, filename, id_, rule,
                                                                        occs):
    start = rule['#'][0]
    end = rule['#'][1]
    inclusive = rule['#'][2]

    offset = utcoffset.compute(start)

    sstart = start + offset

    try:
        send = end + offset
    except TypeError:
        send = end

    # The rule is checked in make_rule, no need to use occs.except_
    occs.except_safe(filename, id_, sstart, send, inclusive)


def get_occurrences_range_UTC(mint, maxt, utcoffset, filename, id_, rule,
                                                                        occs):
    start = rule['#'][0]
    end = rule['#'][1]
    inclusive = rule['#'][2]

    # The rule is checked in make_rule, no need to use occs.except_
    occs.except_safe(filename, id_, start, end, inclusive)


def get_next_item_occurrences_local(base_time, utcoffset, filename, id_, rule,
                                                                        occs):
    start = rule['#'][0]
    end = rule['#'][1]
    inclusive = rule['#'][2]

    offset = utcoffset.compute(start)

    sstart = start + offset

    try:
        send = end + offset
    except TypeError:
        send = end

    # The rule is checked in make_rule, no need to use occs.except_
    occs.except_safe(filename, id_, sstart, send, inclusive)


def get_next_item_occurrences_UTC(base_time, utcoffset, filename, id_, rule,
                                                                        occs):
    start = rule['#'][0]
    end = rule['#'][1]
    inclusive = rule['#'][2]

    # The rule is checked in make_rule, no need to use occs.except_
    occs.except_safe(filename, id_, start, end, inclusive)
