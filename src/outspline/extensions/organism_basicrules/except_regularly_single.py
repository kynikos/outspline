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

import time as _time

from exceptions import BadRuleError

_RULE_NAME = 'except_regularly_single'


def make_rule(refstart, interval, rend, inclusive, guiconfig):
    """
    @param refstart: A sample except period Unix start time.
    @param interval: The interval in seconds between two consecutive except
                     period start times.
    @param rend: The positive difference in seconds between the sample start
                 time and the sample end time.
    @param inclusive: If False, only occurrences that start in the period will
                      be excepted; if True, any occurrence whose period
                      overlaps the except period will be excepted.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organism_api.update_item_rules
    if isinstance(refstart, int) and refstart >= 0 and \
                               isinstance(interval, int) and interval > 0 and \
            isinstance(rend, int) and rend > 0 and isinstance(inclusive, bool):
        refmax = refstart + rend
        refspan = refmax - refstart

        return {
            'rule': _RULE_NAME,
            '#': (
                refmax,
                refspan,
                interval,
                rend,
                inclusive,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()

"""
* reference occurrence
| reftime
[] target occurrence

A) mintime = reftime - ((reftime - refmin) % interval)
B) mintime = reftime - ((reftime - refmin) % interval) + interval
C) mintime = reftime - ((reftime - refmin) % interval) - ((refspan // interval) * interval)
D) mintime = reftime - ((reftime - refmin) % interval) - ((refspan // interval) * interval) + interval

G) mintime = reftime - ((reftime - refmax) % interval) - refspan
H) mintime = reftime - ((reftime - refmax) % interval) + interval - refspan
I) (!NOT VERIFIED!) mintime = reftime - ((reftime - refmax) % interval) - refspan + ((refspan // interval) * interval)
J) (!NOT VERIFIED!) mintime = reftime - ((reftime - refmax) % interval) - refspan + ((refspan // interval) * interval) + interval

M) mintime = reftime + ((refmin - reftime) % interval) - interval
N) mintime = reftime + ((refmin - reftime) % interval)
O) mintime = reftime + ((refmin - reftime) % interval) - ((refspan // interval) * interval) - interval
P) mintime = reftime + ((refmin - reftime) % interval) - ((refspan // interval) * interval)

S) mintime = reftime + ((refmax - reftime) % interval) - refspan
T) mintime = reftime + ((refmax - reftime) % interval) + interval - refspan
U) (!NOT VERIFIED!) mintime = reftime + ((refmax - reftime) % interval) - refspan + ((refspan // interval) * interval)
V) (!NOT VERIFIED!) mintime = reftime + ((refmax - reftime) % interval) - refspan + ((refspan // interval) * interval) + interval

All cases from occur_regularly_single are valid, except for the following:

--------(  *  )--------(     )--------[     |--------(     )--------(     )-----
AGMS

--------[     |--------(     )--------(     )--------(     )--------(  *  )-----
AGMS

--------(     )--------[  *  |--------(     )--------(     )--------(     )-----
AGMS

(-------)(---*---)(-------)(-------)(-------){-------}|-------](-------)(-------)
This case should use AHNT but can also use AHNS: the first calculated
occurrence is useless but safe

{-------}|-------](-------)(-------)(-------)(-------)(---*---)(-------)(-------)
This case should use AHNT but can also use AHNS: the first calculated
occurrence is useless but safe

(-------)(-------)(-------){-------}|---*---](-------)(-------)(-------)(-------)
This case should use AHNT but can also use AHNS: the first calculated
occurrence is useless but safe

            *                           |
(     (     (   ) (   ) [   ) (   ) (   | (   ) (   ) (   )     )     )
0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
(               )                       |
      (     *         )                 |
            (               )           |
                  (               )     |
                        [               |
                              (         |     )
                                    (   |           )
                                        | (               )
                                        |       (               )
                                        |             (               )
CGOS

                      |                         *
(     [     (   ) (   | (   ) (   ) (   ) (   ) (   ) (   )     )     )
0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
(               )     |
      [               |
            (         |     )
                  (   |           )
                      | (               )
                      |       (               )
                      |             (               )
                      |                   (     *         )
                      |                         (               )
                      |                               (               )
CGOS

                        *               |
(     (     (   ) (   ) [   ) (   ) (   | (   ) (   ) (   )     )     )
0     1     2   0 3   1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
(               )                       |
      (               )                 |
            (               )           |
                  (     *         )     |
                        [               |
                              (         |     )
                                    (   |           )
                                        | (               )
                                        |       (               )
                                        |             (               )
CGOS
"""


def _compute_min_time(reftime, refmax, refspan, interval):
    # Use formula (S), see the examples above and in occur_regularly_single
    return reftime + (refmax - reftime) % interval - refspan


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    interval = rule['#'][2]
    start = _compute_min_time(mint, rule['#'][0], rule['#'][1], interval)
    rend = rule['#'][3]
    inclusive = rule['#'][4]

    limits = occs.get_time_span()
    minstart = limits[0]
    maxend = limits[1]

    while True:
        end = start + rend

        if start > maxend:
            break
        elif end >= minstart:
            # The rule is checked in make_rule, no need to use occs.except_
            occs.except_safe(filename, id_, start, end, inclusive)

        start += interval


def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    interval = rule['#'][2]
    start = _compute_min_time(base_time, rule['#'][0], rule['#'][1], interval)
    rend = rule['#'][3]
    inclusive = rule['#'][4]

    limits = occs.get_time_span()
    minstart = limits[0]
    maxend = limits[1]

    while True:
        end = start + rend

        next_occ = occs.get_next_occurrence_time()

        if not next_occ or start > next_occ:
            break

        if start <= maxend and end >= minstart:
            # The rule is checked in make_rule, no need to use occs.except_
            occs.except_safe(filename, id_, start, end, inclusive)

        start += interval
