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

_RULE_NAME = 'occur_every_interval'


def make_rule(refmin, refmax, interval, rstart, rend, ralarm, guiconfig):
    """
    @param refmin: The low end of the reference time span: it should be either
                   the start time or the alarm time, if set and earlier than the
                   start time. The reference time is one real occurrence for
                   this rule.
    @param refmax: The high end of the reference time span: it is the start time
                   itself or the end time, if set, or even the alarm time, if
                   set and greater than the start and end times.
    @param interval: The interval in seconds between two consecutive occurrence
                     start times.
    @param rstart: The positive difference in seconds between refmin and the
                   reference start time.
    @param rend: The positive difference in seconds between the reference start
                 time and the reference end time.
    @param ralarm: The difference in seconds between the reference start time
                   and the reference alarm time; it is negative if the alarm is
                   set later than the start time.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organizer_api.update_item_rules
    if isinstance(refmin, int) and isinstance(refmax, int) and \
                       refmax >= refmin >= 0 and isinstance(interval, int) and \
                  interval > 0 and isinstance(rstart, int) and rstart >= 0 and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):
        return {
            'rule': _RULE_NAME,
            '#': (
                refmin,
                refmax,
                # It's ok if refspan is 0
                refmax - refmin,
                interval,
                rstart,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def _compute_min_time(reftime, refmin, refmax, refspan, interval):
    if reftime > refmax:
        rem = (reftime - refmax) % interval
        return reftime - rem + interval - refspan
    elif reftime < refmin:
        rem = (refmin - reftime) % interval
        return reftime + rem - interval
    else:
        return refmin


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    interval = rule['#'][3]
    mintime = _compute_min_time(mint, rule['#'][0], rule['#'][1], rule['#'][2],
                                                                       interval)
    start = mintime + rule['#'][4]
    rend = rule['#'][5]
    ralarm = rule['#'][6]

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
    interval = rule['#'][3]
    mintime = _compute_min_time(base_time, rule['#'][0], rule['#'][1],
                                                         rule['#'][2], interval)
    start = mintime + rule['#'][4]
    rend = rule['#'][5]
    ralarm = rule['#'][6]

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
