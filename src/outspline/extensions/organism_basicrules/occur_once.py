# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

_RULE_NAME = 'occur_once'


def make_rule(start, end, alarm, guiconfig):
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organism_api.update_item_rules
    if isinstance(start, int) and \
                   (end is None or (isinstance(end, int) and end > start)) and \
                                      (alarm is None or isinstance(alarm, int)):
        return {
            'rule': _RULE_NAME,
            '#': (
                start,
                end,
                alarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    occs.add_safe({'filename': filename,
                   'id_': id_,
                   'start': rule['#'][0],
                   'end': rule['#'][1],
                   'alarm': rule['#'][2]})

def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    # The rule is checked in make_rule, no need to use occs.add
    occs.add_safe(base_time, {'filename': filename,
                              'id_': id_,
                              'start': rule['#'][0],
                              'end': rule['#'][1],
                              'alarm': rule['#'][2]})
