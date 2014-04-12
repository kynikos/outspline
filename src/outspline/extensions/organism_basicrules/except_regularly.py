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

_RULE_NAMES = {'local': 'except_regularly_local',
               'UTC': 'except_regularly_UTC'}


def make_rule(refstart, interval, rend, inclusive, standard, guiconfig):
    """
    @param refstart: A sample except period Unix start time.
    @param interval: The interval in seconds between two consecutive except
                     period start times.
    @param rend: The positive difference in seconds between the sample start
                 time and the sample end time.
    @param inclusive: If False, only occurrences that start in the period will
                      be excepted; if True, any occurrence whose period
                      overlaps the except period will be excepted.
    @param standard: The time standard to be used, either 'local' or 'UTC'.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    #   requirements defined in organism_api.update_item_rules
    # There's no need to check standard because it's imposed by the API
    if isinstance(refstart, int) and refstart >= 0 and \
            isinstance(interval, int) and interval > 0 and \
            isinstance(rend, int) and rend > 0 and isinstance(inclusive, bool):
        refmax = refstart + rend
        refspan = refmax - refstart

        return {
            'rule': _RULE_NAMES[standard],
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

All cases from occur_regularly are valid, except for the following:

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
    # Use formula (S), see the examples above and in occur_regularly
    return reftime + (refmax - reftime) % interval - refspan


def get_occurrences_range_local(mint, maxt, utcoffset, filename, id_, rule,
                                                                        occs):
    limits = occs.get_item_time_span(filename, id_)

    if limits:
        minstart, maxend = limits

        interval = rule['#'][2]
        rend = rule['#'][3]
        inclusive = rule['#'][4]

        # start can't be based on mint, in fact an except rule can affect an
        # occurrence even if its start and end times are out of the time range
        start = _compute_min_time(minstart, rule['#'][0], rule['#'][1],
                                                                      interval)
        while True:
            # Every timestamp can have a different UTC offset, depending
            # whether it's in a DST period or not
            offset = utcoffset.compute(start)

            sstart = start + offset
            send = sstart + rend

            # Do compare sstart with maxend, *not* start
            if sstart > maxend:
                break
            # Do compare send with minstart, *not* end
            elif send >= minstart:
                # The rule is checked in make_rule, no need to use occs.except_
                occs.except_safe(filename, id_, sstart, send, inclusive)

            start += interval


def get_occurrences_range_UTC(mint, maxt, utcoffset, filename, id_, rule,
                                                                        occs):
    limits = occs.get_item_time_span(filename, id_)

    if limits:
        minstart, maxend = limits

        interval = rule['#'][2]
        rend = rule['#'][3]
        inclusive = rule['#'][4]

        # start can't be based on mint, in fact an except rule can affect an
        # occurrence even if its start and end times are out of the time range
        start = _compute_min_time(minstart, rule['#'][0], rule['#'][1],
                                                                      interval)
        while True:
            end = start + rend

            if start > maxend:
                break
            elif end >= minstart:
                # The rule is checked in make_rule, no need to use occs.except_
                occs.except_safe(filename, id_, start, end, inclusive)

            start += interval


def get_next_item_occurrences_local(base_time, utcoffset, filename, id_, rule,
                                                                        occs):
    limits = occs.get_item_time_span(filename, id_)

    if limits:
        minstart, maxend = limits

        interval = rule['#'][2]
        rend = rule['#'][3]
        inclusive = rule['#'][4]

        # start can't be based on base_time, in fact an except rule can affect
        # an occurrence even if its start and end times are out of the time
        # range
        start = _compute_min_time(minstart, rule['#'][0], rule['#'][1],
                                                                      interval)

        while True:
            # Every timestamp can have a different UTC offset, depending
            # whether it's in a DST period or not
            offset = utcoffset.compute(start)

            sstart = start + offset
            send = sstart + rend

            next_occ = occs.get_next_occurrence_time()

            # Do compare sstart with next_occ, *not* start
            if not next_occ or sstart > next_occ:
                break

            # Do compare sstart with maxend and send with minstart, *not* start
            # and end
            if sstart <= maxend and send >= minstart:
                # The rule is checked in make_rule, no need to use occs.except_
                occs.except_safe(filename, id_, sstart, send, inclusive)

            start += interval


def get_next_item_occurrences_UTC(base_time, utcoffset, filename, id_, rule,
                                                                        occs):
    limits = occs.get_item_time_span(filename, id_)

    if limits:
        minstart, maxend = limits

        interval = rule['#'][2]
        rend = rule['#'][3]
        inclusive = rule['#'][4]

        # start can't be based on base_time, in fact an except rule can affect
        # an occurrence even if its start and end times are out of the time
        # range
        start = _compute_min_time(minstart, rule['#'][0], rule['#'][1],
                                                                      interval)

        while True:
            end = start + rend

            next_occ = occs.get_next_occurrence_time()

            if not next_occ or start > next_occ:
                break

            if start <= maxend and end >= minstart:
                # The rule is checked in make_rule, no need to use occs.except_
                occs.except_safe(filename, id_, start, end, inclusive)

            start += interval
