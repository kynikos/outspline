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

from exceptions import BadRuleError

_RULE_NAME = 'occur_yearly_single'


def make_rule(interval, refyear, month, day, rstart, rend, ralarm, guiconfig):
    """
    @param interval: An integer > 0 representing the number of years between
                     two consecutive occurrences.
    @param refyear: An integer representing a sample year of occurrence.
    @param month: An integer representing the chosen month (1-12).
    @param day: An integer representing the chosen day (1-31). February 29th
                will generate an occurrence only in leap years.
    @param rstart: The difference in seconds between the start of the chosen day
                   and the start of the occurrence (0-86399).
    @param rend: The positive difference in seconds between the relative start
                 time and the relative end time.
    @param ralarm: The difference in seconds between the relative start time
                   and the relative alarm time; it is negative if the alarm is
                   set later than the start time.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organizer_api.update_item_rules
    if isinstance(interval, int) and interval > 0 and \
                                  isinstance(refyear, int) and refyear > 0 and \
                           isinstance(rstart, int) and -1 < rstart < 86400 and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):
        # Non-leap year
        year = 2001

        try:
            # Do not use a leap year here because one more day should be
            # subtracted for January and February to obtain the time until the
            # end of the year
            date1 = _datetime.date(year, month, day)
        except ValueError:
            # Leap year
            year = 2000

            try:
                date1 = _datetime.date(year, month, day)
            except ValueError:
                raise BadRuleError()

        date2 = _datetime.date(year + 1, 1, 1)

        diff = date2 - date1
        diffs = diff.total_seconds() - rstart

        if ralarm:
            srend = max(rend, ralarm * -1, 0)
        else:
            srend = max(rend, 0)

        maxoverlap = max(srend - diffs, 0)

        return {
            'rule': _RULE_NAME,
            '#': (
                maxoverlap,
                interval,
                refyear,
                month,
                day,
                rstart,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    mintime = mint - rule['#'][0]
    interval = rule['#'][1]
    refyear = rule['#'][2]
    month = rule['#'][3]
    day = rule['#'][4]
    rstart = rule['#'][5]
    rend = rule['#'][6]
    ralarm = rule['#'][7]

    ndate = _datetime.date.fromtimestamp(mintime)
    nyear = ndate.year

    year = nyear + abs(refyear - nyear) % interval

    while True:
        try:
            sdate = _datetime.date(year, month, day)
        except ValueError:
            # Prevent infinite loops
            maxdate = _datetime.date.fromtimestamp(maxt)
            testdate = _datetime.date(year, month, 1)

            if maxdate < testdate:
                break
        else:
            start = int(_time.mktime(sdate.timetuple())) + rstart

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

        year += interval


def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    mintime = base_time - rule['#'][0]
    interval = rule['#'][1]
    refyear = rule['#'][2]
    month = rule['#'][3]
    day = rule['#'][4]
    rstart = rule['#'][5]
    rend = rule['#'][6]
    ralarm = rule['#'][7]

    ndate = _datetime.date.fromtimestamp(mintime)
    nyear = ndate.year

    year = nyear + abs(refyear - nyear) % interval

    while True:
        try:
            sdate = _datetime.date(year, month, day)
        except ValueError:
            # Prevent infinite loops
            maxdate = _datetime.date.fromtimestamp(
                                                occs.get_next_occurrence_time())
            testdate = _datetime.date(year, month, 1)

            if maxdate < testdate:
                break
        else:
            start = int(_time.mktime(sdate.timetuple())) + rstart

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

        year += interval
