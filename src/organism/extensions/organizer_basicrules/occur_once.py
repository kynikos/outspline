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

from exceptions import BadRuleError

_RULE_NAME = 'occur_once'


def _compute_alarm(start, ralarm):
    return None if (ralarm == None) else (start - ralarm)


def make_rule(start, end, ralarm):
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organizer_api.update_item_rules
    if start and (end is None or end > start):
        return {'rule': _RULE_NAME,
                'start': start,
                'end': end,
                'ralarm': ralarm,
                'alarm': _compute_alarm(start, ralarm)}
    else:
        raise BadRuleError()


def get_occurrences_range(filename, id_, rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    occs.add_safe({'filename': filename,
                   'id_': id_,
                   'start': rule['start'],
                   'end': rule['end'],
                   'alarm': rule['alarm']})

def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    occs.add_safe(base_time, {'filename': filename,
                              'id_': id_,
                              'start': rule['start'],
                              'end': rule['end'],
                              'alarm': rule['alarm']})
