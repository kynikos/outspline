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
                      be excepted; if True, any occurrence whose period overlaps
                      the except period will be excepted.
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


def _compute_min_time(reftime, refmax, refspan, interval):
    # Always use refmax, _not_ refmin, in this algorithm, since it allows to
    # get the right occurrence more easily
    if reftime >= refmax:
        rem = (reftime - refmax) % interval
        return reftime - rem + interval - refspan
    else:
        # Don't use only refmin when refmin <= reftime < refmax, because in
        # case of refspan > interval (overlapping occurrences) it wouldn't
        # always be the correct value (see the examples in
        # occur_regularly_single.py)
        rem = (refmax - reftime) % interval
        return reftime + rem - refspan


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    interval = rule['#'][2]
    start = _compute_min_time(mint, rule['#'][0], rule['#'][1], interval)
    rend = rule['#'][3]
    inclusive = rule['#'][4]

    while True:
        end = start + rend

        if start > maxt:
            break

        if start <= maxt and end >= mint:
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
