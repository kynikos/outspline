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

import bisect

from exceptions import BadRuleError

_RULE_NAMES = {'local': 'occur_regularly_group_local',
               'UTC': 'occur_regularly_group_UTC'}


def make_rule(refstart, interval, rstarts, rend, ralarm, standard, guiconfig):
    """
    @param refstart: A sample Unix start time of the first occurrence in a
                     group.
    @param interval: The interval in seconds between the start times of the
                     first occurrences of two consecutive groups.
    @param rstarts: A tuple storing the positive differences in seconds between
                    the start time of the first occurrence and that of each
                    occurrence in a group. It must contain at least 0, which
                    corresponds to the first occurrence of the group.
    @param rend: The positive difference in seconds between an occurrence's
                 start and end times.
    @param ralarm: The difference in seconds between an occurrence's start and
                   alarm times; it is negative if the alarm is set later than
                   the start time.
    @param standard: The time standard to be used, either 'local' or 'UTC'.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    #   requirements defined in organism_api.update_item_rules
    # There's no need to check standard because it's imposed by the API
    if isinstance(refstart, int) and refstart >= 0 and \
                isinstance(interval, int) and interval > 0 and \
                isinstance(rstarts, list) and 0 in rstarts and \
                (rend is None or (isinstance(rend, int) and rend > 0)) and \
                (ralarm is None or isinstance(ralarm, int)):
        mrstart = max(rstarts)
        irmaxs = []

        for rstart in rstarts:
            if isinstance(rstart, int) and rstart >= 0:
                irmaxs.append(mrstart - rstart)
            else:
                raise BadRuleError()

        # irmaxs must be sorted in order to have bisect.bisect_right work
        # correctly
        irmaxs.sort()

        rmax = max((rend, ralarm * -1 if ralarm else 0, 0))
        refmax = refstart + mrstart + rmax

        return {
            'rule': _RULE_NAMES[standard],
            '#': (
                refmax,
                interval,
                irmaxs,
                rmax,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range_local(mint, utcmint, maxt, utcoffset, filename, id_,
                                                                rule, occs):
def _compute_relative_max_time(reftime, refmax, interval):
    # Use formula (S), see the examples in occur_regularly
    return (refmax - reftime) % interval


    interval = rule['#'][1]
    rmaxtime = _compute_relative_max_time(mint, rule['#'][0], interval)
    irmaxs = rule['#'][2]
    rmax = rule['#'][3]
    rend = rule['#'][4]
    ralarm = rule['#'][5]

    j = len(irmaxs) - 1
    i = bisect.bisect_right(irmaxs, rmaxtime) - 1
    irmax = irmaxs[i]
    basemax = mint + rmaxtime

    while True:
        start = basemax - irmax - rmax

        # Every timestamp can have a different UTC offset, depending whether
        # it's in a DST period or not
        offset = utcoffset.compute(start)

        sstart = start + offset

        try:
            send = sstart + rend
        except TypeError:
            send = None

        try:
            salarm = sstart - ralarm
        except TypeError:
            salarm = None

        # Do compare sstart and salarm with maxt, *not* start and alarm
        if sstart > maxt and (salarm is None or salarm > maxt):
            break

        # The rule is checked in make_rule, no need to use occs.add
        occs.add_safe({'filename': filename,
                       'id_': id_,
                       'start': sstart,
                       'end': send,
                       'alarm': salarm})

        if i > 0:
            i -= 1
            irmax = irmaxs[i]
        else:
            basemax += interval
            i = j
            irmax = irmaxs[j]


    interval = rule['#'][1]
    rmaxtime = _compute_relative_max_time(mint, rule['#'][0], interval)
    irmaxs = rule['#'][2]
    rmax = rule['#'][3]
    rend = rule['#'][4]
    ralarm = rule['#'][5]

    j = len(irmaxs) - 1
    i = bisect.bisect_right(irmaxs, rmaxtime) - 1
    irmax = irmaxs[i]
    basemax = mint + rmaxtime

    while True:
        start = basemax - irmax - rmax

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

        if i > 0:
            i -= 1
            irmax = irmaxs[i]
        else:
            basemax += interval
            i = j
            irmax = irmaxs[j]


def get_occurrences_range_UTC(mint, utcmint, maxt, utcoffset, filename, id_,
                                                                rule, occs):
    interval = rule['#'][1]
    rmaxtime = _compute_relative_max_time(base_time, rule['#'][0], interval)
    irmaxs = rule['#'][2]
    rmax = rule['#'][3]
    rend = rule['#'][4]
    ralarm = rule['#'][5]

    j = len(irmaxs) - 1
    i = bisect.bisect_right(irmaxs, rmaxtime) - 1
    irmax = irmaxs[i]
    basemax = base_time + rmaxtime

    while True:
        start = basemax - irmax - rmax

        # Every timestamp can have a different UTC offset, depending whether
        # it's in a DST period or not
        offset = utcoffset.compute(start)

        sstart = start + offset

        try:
            send = sstart + rend
        except TypeError:
            send = None

def get_next_item_occurrences_local(base_time, utcbase, utcoffset, filename,
                                                            id_, rule, occs):
        try:
            salarm = sstart - ralarm
        except TypeError:
            salarm = None

        occd = {'filename': filename,
                'id_': id_,
                'start': sstart,
                'end': send,
                'alarm': salarm}

        next_occ = occs.get_next_occurrence_time()

        # The rule is checked in make_rule, no need to use occs.add
        # Do compare sstart and salarm with next_occ, *not* start and alarm
        if occs.add_safe(base_time, occd) or \
                            (next_occ and sstart > next_occ and
                            (salarm is None or salarm > next_occ)):
            break

        if i > 0:
            i -= 1
            irmax = irmaxs[i]
        else:
            basemax += interval
            i = j
            irmax = irmaxs[j]


    interval = rule['#'][1]
    rmaxtime = _compute_relative_max_time(base_time, rule['#'][0], interval)
    irmaxs = rule['#'][2]
    rmax = rule['#'][3]
    rend = rule['#'][4]
    ralarm = rule['#'][5]

    j = len(irmaxs) - 1
    i = bisect.bisect_right(irmaxs, rmaxtime) - 1
    irmax = irmaxs[i]
    basemax = base_time + rmaxtime

    while True:
        start = basemax - irmax - rmax

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

        if i > 0:
            i -= 1
            irmax = irmaxs[i]
        else:
            basemax += interval
            i = j
            irmax = irmaxs[j]
def get_next_item_occurrences_UTC(base_time, utcbase, utcoffset, filename,
                                                            id_, rule, occs):
