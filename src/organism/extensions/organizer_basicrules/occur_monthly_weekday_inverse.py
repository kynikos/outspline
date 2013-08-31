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

from exceptions import BadRuleError

_RULE_NAME = 'occur_monthly_weekday_inverse'


def make_rule(months, weekday, number, rstart, rend, ralarm, guiconfig):
    """
    @param months: The months for which create occurrences: must be a tuple of
                   integers representing the selected months (1 - 12).
    @param weekday: An integer representing the chosen day of the week
                 (0: Monday - 6: Sunday).
    @param number: An integer representing the number of the chosen weekday
                  (> 0) from the end of a month. If a month doesn't have enough
                  weekdays, no occurrence is generated.
    @param rstart: The positive difference in seconds between the start of the
                   chosen day and the actual start of the occurrence.
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
    if isinstance(months, list) and len(months) > 0 and \
                             isinstance(weekday, int) and -1 < weekday < 7 and \
                                    isinstance(number, int) and number > 0 and \
                           isinstance(rstart, int) and -1 < rstart < 86400 and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):
        nmonths = []

        for n in range(1, 13):
            if n in months:
                nmonths.extend([n, ] * (n - len(nmonths)))
        # Note that it's ok that nmonths can be shorter than 12 items; do *not*
        # do the following:
        #else:
        #    nmonths.extend([nmonths[0], ] * (12 - len(nmonths)))

        nnumber = number - 1

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
                nmonths,
                weekday,
                nnumber,
                span,
                rstart,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    months = rule['#'][0]
    weekday = rule['#'][1]
    number = rule['#'][2]
    # Go back by span in order to keep into account any occurrence that still
    # has to end
    mintime = mint - rule['#'][3]
    rstart = rule['#'][4]
    rend = rule['#'][5]
    ralarm = rule['#'][6]

    date = _datetime.date.fromtimestamp(mintime)

    try:
        month = months[date.month - 1]
    except IndexError:
        month = months[0]
        year = date.year + 1
    else:
        year = date.year

    while True:
        first_month_weekday, last_month_day_number = calendar.monthrange(year,
                                                                          month)
        last_month_weekday = (first_month_weekday + last_month_day_number % 7 +
                                                                          6) % 7
        selected_day_number = last_month_day_number - (last_month_weekday -
                                                   weekday + 7) % 7 - number * 7

        try:
            sdate = _datetime.datetime(year, month, selected_day_number)
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

        try:
            month = months[month]
        except IndexError:
            month = months[0]
            year += 1


def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    months = rule['#'][0]
    weekday = rule['#'][1]
    number = rule['#'][2]
    # Go back by span in order to keep into account any occurrence that still
    # has to end
    mintime = base_time - rule['#'][3]
    rstart = rule['#'][4]
    rend = rule['#'][5]
    ralarm = rule['#'][6]

    date = _datetime.date.fromtimestamp(mintime)

    try:
        month = months[date.month - 1]
    except IndexError:
        month = months[0]
        year = date.year + 1
    else:
        year = date.year

    while True:
        first_month_weekday, last_month_day_number = calendar.monthrange(year,
                                                                          month)
        last_month_weekday = (first_month_weekday + last_month_day_number % 7 +
                                                                          6) % 7
        selected_day_number = last_month_day_number - (last_month_weekday -
                                                   weekday + 7) % 7 - number * 7

        try:
            sdate = _datetime.datetime(year, month, selected_day_number)
        except ValueError:
            # Prevent infinite loops

            next_ = occs.get_next_occurrence_time()

            if next_:
                maxdate = _datetime.date.fromtimestamp(next_)
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

        try:
            month = months[month]
        except IndexError:
            month = months[0]
            year += 1
