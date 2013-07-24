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
import datetime as _datetime
import calendar
import bisect

from exceptions import BadRuleError

_RULE_NAME = 'occur_yearly'


def make_rule(occs, occsl, rend, ralarm, guiconfig):
    """
    @param occs: A dictionary whose keys are the selected months (1-12); each
                 value is a dictionary whose keys are the selected start days
                 (1-{28,30,31}); each value is a dictionary whose keys are
                 the selected start hours (0-23); each value is a tuple whose
                 items are the selected start minutes (0-59). Note that February
                 is considered of 28 days, use occsl for setting occurrences on
                 leap-year Februaries.
    @param occsl: A dictionary whose keys are the selected start days in a
                  leap-year February (1-29); each value is a dictionary whose
                  keys are the selected start hours (0-23); each value is a
                  tuple whose items are the selected start minutes (0-59).
    @param rend: The positive difference in seconds between the relative start
                 time and the relative end time.
    @param ralarm: The difference in seconds between the relative start time
                   and the relative alarm time; it is negative if the alarm is
                   set later than the start time.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Leap-year February is treated separately to make it possible for example
    # to define occurrences relative to the end of the month (since the length
    # of February si variable)

    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organizer_api.update_item_rules
    if isinstance(occs, dict) and isinstance(occsl, dict) and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):
        for m in occs:
            for d in occs[m]:
                for H in occs[m][d]:
                    for M in occs[m][d][H]:
                        try:
                            # 2001 was non leap
                            _datetime.datetime(2001, m, d, H, M)
                        except ValueError:
                            raise BadRuleError()

        for d in occsl:
            for H in occsl[d]:
                for M in occsl[d][H]:
                    try:
                        # 2000 was leap
                        _datetime.datetime(2000, 2, d, H, M)
                    except ValueError:
                        raise BadRuleError()

        occslt = occs.copy()

        if 2 in occs:
            occslt[2] = occsl

        # The algorithms assume that there's at least one occurrence every year
        if 0 in (len(occs), len(occslt)):
            raise BadRuleError()

        # Using the seconds from the start of the year would be troublesome
        # because of leap years

        occs1 = [int(''.join(('1', str(d).zfill(2), str(H).zfill(2),
                 str(M).zfill(2)))) for d in occs[1] for H in occs[1][d]
                                    for M in occs[1][d][H]] if 1 in occs else []

        occs2 = [int(''.join(('2', str(d).zfill(2), str(H).zfill(2),
                 str(M).zfill(2)))) for d in occs[2] for H in occs[2][d]
                                    for M in occs[2][d][H]] if 2 in occs else []

        occs2l = [int(''.join(('2', str(d).zfill(2), str(H).zfill(2),
                  str(M).zfill(2)))) for d in occsl for H in occsl[d]
                                     for M in occsl[d][H]]

        occs3 = [int(''.join((str(m).zfill(2), str(d).zfill(2),
                 str(H).zfill(2), str(M).zfill(2)))) for m in occs
                 for d in occs[m] for H in occs[m][d] for M in occs[m][d][H]
                 if m > 2]

        for o in (occs1, occs2, occs2l, occs3):
            o.sort()

        srend = max(rend, 0)

        if ralarm is None:
            span = srend
        elif ralarm >= 0:
            span = srend + ralarm
        else:
            span = max(srend, ralarm * -1)

        return {
            'rule': _RULE_NAME,
            '#': (
                span,
                occs1,
                occs2,
                occs2l,
                occs3,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    mintime = mint - rule['#'][0]
    occs1 = rule['#'][1]
    occs2 = rule['#'][2]
    occs2l = rule['#'][3]
    occs3 = rule['#'][4]
    rend = rule['#'][5]
    ralarm = rule['#'][6]

    sdate = _datetime.datetime.fromtimestamp(mintime)

    y = sdate.year

    if calendar.isleap(y):
        occsf = occs1 + occs2l + occs3
    else:
        occsf = occs1 + occs2 + occs3

    i = bisect.bisect_left(occsf, int(''.join((str(sdate.month),
                          str(sdate.day), str(sdate.hour), str(sdate.minute)))))

    while True:
        try:
            socc = occsf[i]
        except IndexError:
            y += 1

            if calendar.isleap(y):
                occsf = occs1 + occs2l + occs3
            else:
                occsf = occs1 + occs2 + occs3

            # 0 will always be a valid index because make_rule makes sure
            # there's at least an occurrence every year
            i = 0
            socc = occsf[0]

        m, mr = divmod(socc, 1000000)
        d, dr = divmod(mr, 10000)
        H, M = divmod(dr, 100)

        sdate = _datetime.datetime(y, m, d, H, M)
        start = int(_time.mktime(sdate.timetuple()))

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

        i += 1


def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    mintime = base_time - rule['#'][0]
    occs1 = rule['#'][1]
    occs2 = rule['#'][2]
    occs2l = rule['#'][3]
    occs3 = rule['#'][4]
    rend = rule['#'][5]
    ralarm = rule['#'][6]

    sdate = _datetime.datetime.fromtimestamp(mintime)

    y = sdate.year

    if calendar.isleap(y):
        occsf = occs1 + occs2l + occs3
    else:
        occsf = occs1 + occs2 + occs3

    i = bisect.bisect_left(occsf, int(''.join((str(sdate.month),
                          str(sdate.day), str(sdate.hour), str(sdate.minute)))))

    while True:
        try:
            socc = occsf[i]
        except IndexError:
            y += 1

            if calendar.isleap(y):
                occsf = occs1 + occs2l + occs3
            else:
                occsf = occs1 + occs2 + occs3

            # 0 will always be a valid index because make_rule makes sure
            # there's at least an occurrence every year
            i = 0
            socc = occsf[0]

        m, mr = divmod(socc, 1000000)
        d, dr = divmod(mr, 10000)
        H, M = divmod(dr, 100)

        sdate = _datetime.datetime(y, m, d, H, M)
        start = int(_time.mktime(sdate.timetuple()))

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

        i += 1
