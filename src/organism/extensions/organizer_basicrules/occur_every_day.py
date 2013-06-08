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

import time as _time

from exceptions import BadRuleError

_RULE_NAME = 'occur_every_day'


def _compute_rend(rendn, rendu):
    if rendn != None:
        mult = {'minutes': 60,
                'hours': 3600,
                'days': 86400,
                'weeks': 604800,
                'months': 2592000,
                'years': 31536000}

        return rendn * mult[rendu]
    else:
        return None


def _compute_start(reftime, rstart, rend):
    firstday = reftime // 86400 * 86400 + _time.altzone
    rday = reftime % 86400

    if rstart < rday:
        startt = firstday + 86400 + rstart
    else:
        startt = firstday + rstart

    if rend != None:
        # This algorithm must also get occurrences whose end time falls within
        # the requested range (for get_occurrences_range) or is the next
        # occurrence (for get_next_item_occurrences)
        return startt - 86400 * (1 + rend // 86400)
    else:
        return startt


def _compute_end(start, rend):
    return start + rend if rend != None else None


def _compute_alarm(start, ralarm):
    return start - ralarm if ralarm != None else None


def make_rule(rstart, rendn, rendu, ralarm):
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organizer_api.update_item_rules
    if rstart:
        return {'rule': _RULE_NAME,
                'rstart': rstart,
                'rendn': rendn,
                'rendu': rendu,
                'ralarm': ralarm}
    else:
        raise BadRuleError()


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    rend = _compute_rend(rule['rendn'], rule['rendu'])
    start = _compute_start(mint, rule['rstart'], rend)
    ralarm = rule['ralarm']

    while True:
        end = _compute_end(start, rend)
        alarm = _compute_end(start, ralarm)

        if (alarm and alarm > maxt) or start > maxt:
            break

        # The rule is checked in make_rule, no need to use occs.add
        occs.add_safe({'filename': filename,
                       'id_': id_,
                       'start': start,
                       'end': end,
                       'alarm': alarm})

        start += 86400


def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    rend = _compute_rend(rule['rendn'], rule['rendu'])
    start = _compute_start(base_time, rule['rstart'], rend)
    ralarm = rule['ralarm']

    while True:
        end = _compute_end(start, rend)
        alarm = _compute_end(start, ralarm)

        occd = {'filename': filename,
                'id_': id_,
                'start': start,
                'end': end,
                'alarm': alarm}

        next_occ = occs.get_next_occurrence_time()

        # The rule is checked in make_rule, no need to use occs.add
        if occs.add_safe(base_time, occd) or (next_occ and
                                         (alarm is None and start > next_occ) or
                                                  (alarm and alarm > next_occ)):
            break

        start += 86400
