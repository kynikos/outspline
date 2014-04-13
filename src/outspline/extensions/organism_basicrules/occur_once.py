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

_RULE_NAMES = {'local': 'occur_once_local',
               'UTC': 'occur_once_UTC'}


def make_rule(start, end, alarm, standard, guiconfig):
    # Make sure this rule can only produce occurrences compliant with the
    #   requirements defined in organism_api.update_item_rules
    # There's no need to check standard because it's imposed by the API
    if isinstance(start, int) and \
                (end is None or (isinstance(end, int) and end > start)) and \
                (alarm is None or isinstance(alarm, int)):
        return {
            'rule': _RULE_NAMES[standard],
            '#': (
                start,
                end,
                alarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range_local(mint, utcmint, maxt, utcoffset, filename, id_,
                                                                rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    start = rule['#'][0]
    end = rule['#'][1]
    alarm = rule['#'][2]

    offset = utcoffset.compute(start)

    sstart = start + offset

    try:
        send = end + offset
    except TypeError:
        send = end

    try:
        salarm = alarm + offset
    except TypeError:
        salarm = alarm

    occs.add_safe({'filename': filename,
                   'id_': id_,
                   'start': sstart,
                   'end': send,
                   'alarm': salarm})


def get_occurrences_range_UTC(mint, utcmint, maxt, utcoffset, filename, id_,
                                                                rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    occs.add_safe({'filename': filename,
                   'id_': id_,
                   'start': rule['#'][0],
                   'end': rule['#'][1],
                   'alarm': rule['#'][2]})

def get_next_item_occurrences_local(base_time, utcbase, utcoffset, filename,
                                                            id_, rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    start = rule['#'][0]
    end = rule['#'][1]
    alarm = rule['#'][2]

    offset = utcoffset.compute(start)

    sstart = start + offset

    try:
        send = end + offset
    except TypeError:
        send = end

    try:
        salarm = alarm + offset
    except TypeError:
        salarm = alarm

    occs.add_safe(base_time, {'filename': filename,
                              'id_': id_,
                              'start': sstart,
                              'end': send,
                              'alarm': salarm})

def get_next_item_occurrences_UTC(base_time, utcbase, utcoffset, filename,
                                                            id_, rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    occs.add_safe(base_time, {'filename': filename,
                              'id_': id_,
                              'start': rule['#'][0],
                              'end': rule['#'][1],
                              'alarm': rule['#'][2]})
