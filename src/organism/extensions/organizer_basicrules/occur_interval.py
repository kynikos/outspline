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

_RULE_NAME = 'occur_interval'


def make_rule(refstart, interval, rend, ralarm, guiconfig):
    """
    @param refstart: A sample occurrence Unix start time.
    @param interval: The interval in seconds between two consecutive occurrence
                     start times.
    @param rend: The positive difference in seconds between the sample start
                 time and the sample end time.
    @param ralarm: The difference in seconds between the sample start time and
                   the sample alarm time; it is negative if the alarm is set
                   later than the start time.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organizer_api.update_item_rules
    if isinstance(refstart, int) and refstart >= 0 and \
                                isinstance(interval, int) and interval > 0 and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):
        if ralarm is None:
            refmin = refstart
            refmax = refstart + max((rend, 0))
        else:
            refmin = refstart - max((ralarm, 0))
            refmax = refstart + max((rend, ralarm * -1, 0))

        refspan = refmax - refmin
        rstart = refstart - refmin

        return {
            'rule': _RULE_NAME,
            '#': (
                refmax,
                refspan,
                interval,
                rstart,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()

"""
* reference occurrence
| reftime
[] target occurrence

--------(  *  )--------(     )--------(     )--------[  |  ]--------(     )-----
mintime = reftime - ((reftime - refmin) % interval)
mintime = reftime - ((reftime - refmax) % interval) + interval - refspan

--------(  *  )--------(     )--------(     )-----|--[     ]--------(     )-----
mintime = reftime - ((reftime - refmin) % interval) + interval
mintime = reftime - ((reftime - refmax) % interval) + interval - refspan

--------(     )--------(     )-----|--[     ]--------(     )--------(  *  )-----
mintime = reftime + ((refmin - reftime) % interval)
mintime = reftime + ((refmax - reftime) % interval) - refspan

--------(     )--------[  |  ]--------(     )--------(     )--------(  *  )-----
mintime = reftime + ((refmin - reftime) % interval) - interval
mintime = reftime + ((refmax - reftime) % interval) - refspan

--------(     )--------(     )--------[  |* ]--------(     )--------(     )-----
mintime = refmin
mintime = reftime - ((reftime - refmin) % interval)
mintime = reftime + ((refmax - reftime) % interval) - refspan

            *                         |
(     (     (   ) (   ) [   ) (   ) ( | ] (   ) (   ) (   )     )     )
0     1     2   0 3   1 4   2 5   3 6 | 4 7   5 8   6 9   7     8     9
(               )                     |
      (     *         )               |
            (               )         |
                  (               )   |
                        [             | ]
                              (       |       )
                                    ( |             )
                                      |   (               )
                                      |         (               )
                                      |               (               )
mintime = reftime - ((reftime - refmin) % interval) - ((refspan // interval) * interval)
mintime = reftime - ((reftime - refmax) % interval) + interval - refspan

                    |                           *
(     [     (   ) ( | ] (   ) (   ) (   ) (   ) (   ) (   )     )     )
0     1     2   0 3 | 1 4   2 5   3 6   4 7   5 8   6 9   7     8     9
(               )   |
      [             | ]
            (       |       )
                  ( |             )
                    |   (               )
                    |         (               )
                    |               (               )
                    |                     (     *         )
                    |                           (               )
                    |                                 (               )
mintime = reftime + ((refmin - reftime) % interval) - ((refspan // interval) * interval) - interval
mintime = reftime + ((refmax - reftime) % interval) - refspan

                                    * |
(     (     (   ) (   ) [   ) (   ) ( | ] (   ) (   ) (   )     )     )
0     1     2   0 3   1 4   2 5   3 6 | 4 7   5 8   6 9   7     8     9
(               )                     |
      (               )               |
            (               )         |
                  (               )   |
                        [             | ]
                              (     * |       )
                                    ( |             )
                                      |   (               )
                                      |         (               )
                                      |               (               )
mintime = reftime - ((reftime - refmin) % interval) - ((refspan // interval) * interval)
mintime = reftime + ((refmax - reftime) % interval) - refspan
"""


def _compute_min_time(reftime, refmax, refspan, interval):
    # Always use refmax, _not_ refmin, in this algorithm, since it allows to
    # get the right occurrence more easily
    if reftime > refmax:
        rem = (reftime - refmax) % interval
        return reftime - rem + interval - refspan
    else:
        # Don't use only refmin when refmin <= reftime <= refmax, because in
        # case of refspan > interval (overlapping occurrences) it wouldn't
        # always be the correct value (see the examples above)
        rem = (refmax - reftime) % interval
        return reftime + rem - refspan


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    interval = rule['#'][2]
    mintime = _compute_min_time(mint, rule['#'][0], rule['#'][1], interval)
    start = mintime + rule['#'][3]
    rend = rule['#'][4]
    ralarm = rule['#'][5]

    while True:
        try:
            end = start + rend
        except TypeError:
            end = None

        try:
            alarm = start - ralarm
        except TypeError:
            alarm = None

        if start > maxt and (alarm is None or alarm > maxt):
            break

        # The rule is checked in make_rule, no need to use occs.add
        occs.add_safe({'filename': filename,
                       'id_': id_,
                       'start': start,
                       'end': end,
                       'alarm': alarm})

        start += interval


def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    interval = rule['#'][2]
    mintime = _compute_min_time(base_time, rule['#'][0], rule['#'][1], interval)
    start = mintime + rule['#'][3]
    rend = rule['#'][4]
    ralarm = rule['#'][5]

    while True:
        try:
            end = start + rend
        except TypeError:
            end = None

        try:
            alarm = start - ralarm
        except TypeError:
            alarm = None

        occd = {'filename': filename,
                'id_': id_,
                'start': start,
                'end': end,
                'alarm': alarm}

        next_occ = occs.get_next_occurrence_time()

        # The rule is checked in make_rule, no need to use occs.add
        if occs.add_safe(base_time, occd) or (next_occ and start > next_occ and
                                           (alarm is None or alarm > next_occ)):
            break

        start += interval
