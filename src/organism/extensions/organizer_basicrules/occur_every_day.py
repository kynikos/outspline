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
        # the requested range (for get_occurrences) or is the next occurrence
        # (for search_next_item_occurrences)
        return startt - 86400 * (1 + rend // 86400)
    else:
        return startt


def _compute_end(start, rend):
    return start + rend if rend != None else None


def _compute_alarm(start, ralarm):
    return start - ralarm if ralarm != None else None


def get_occurrences(mint, maxt, filename, id_, rule, occs):
    rend = _compute_rend(rule['rendn'], rule['rendu'])
    start = _compute_start(mint, rule['rstart'], rend)
    ralarm = rule['ralarm']

    while True:
        end = _compute_end(start, rend)
        alarm = _compute_end(start, ralarm)

        if (alarm and alarm > maxt) or start > maxt:
            break

        occs.add({'filename': filename,
                  'id_': id_,
                  'start': start,
                  'end': end,
                  'alarm': alarm})

        start += 86400


def search_next_item_occurrences(last_search, filename, id_, rule, occs):
    rend = _compute_rend(rule['rendn'], rule['rendu'])
    start = _compute_start(last_search, rule['rstart'], rend)
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

        if occs.add(last_search, occd) or (next_occ and
                                         (alarm is None and start > next_occ) or
                                                  (alarm and alarm > next_occ)):
            break

        start += 86400
