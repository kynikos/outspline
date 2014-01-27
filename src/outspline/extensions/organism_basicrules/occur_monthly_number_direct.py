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

import time as _time
import datetime as _datetime

from exceptions import BadRuleError

_RULE_NAME = 'occur_monthly_number_direct'


def make_rule(months, rstart, rend, ralarm, guiconfig):
    """
    @param months: The months for which create occurrences: must be a list of
                   integers representing the selected months (1 - 12).
    @param rstart: The positive difference in seconds between the start of the
                   month and the start of the occurrence. Note that BadRuleError
                   is raised if rstart is longer than the shortest month in
                   months; February is considered of 28 days, use another rule
                   if you want to include February 29th.
    @param rend: The positive difference in seconds between the relative start
                 time and the relative end time.
    @param ralarm: The difference in seconds between the relative start time
                   and the relative alarm time; it is negative if the alarm is
                   set later than the start time.
    @param guiconfig: A place to store any configuration needed only by the
                      interface.
    """
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organism_api.update_item_rules
    if isinstance(months, list) and len(months) > 0 and \
                                   isinstance(rstart, int) and rstart >= 0 and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):

        limits = (2678400, 2419200, 2678400, 2592000, 2678400, 2592000,
                  2678400, 2678400, 2592000, 2678400, 2592000, 2678400)

        for m in months:
            try:
                limit = limits[m - 1]
            except (TypeError, IndexError):
                raise BadRuleError()
            else:
                if rstart >= limit:
                    raise BadRuleError()

        nmonths = []

        for n in range(1, 13):
            if n in months:
                nmonths.extend([n, ] * (n - len(nmonths)))
        # Note that it's ok that nmonths can be shorter than 12 items; do *not*
        # do the following:
        #else:
        #    nmonths.extend([nmonths[0], ] * (12 - len(nmonths)))

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
                nmonths,
                rstart,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range(mint, maxt, filename, id_, rule, occs):
    # Go back by span in order to keep into account any occurrence that still
    # has to end
    mintime = mint - rule['#'][0]
    months = rule['#'][1]
    rstart = rule['#'][2]
    rend = rule['#'][3]
    ralarm = rule['#'][4]

    date = _datetime.date.fromtimestamp(mintime)

    try:
        month = months[date.month - 1]
    except IndexError:
        month = months[0]
        year = date.year + 1
    else:
        year = date.year

    while True:
        date = _datetime.date(year, month, 1)

        start = int(_time.mktime(date.timetuple())) + rstart

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
    # Go back by span in order to keep into account any occurrence that still
    # has to end
    mintime = base_time - rule['#'][0]
    months = rule['#'][1]
    rstart = rule['#'][2]
    rend = rule['#'][3]
    ralarm = rule['#'][4]

    date = _datetime.date.fromtimestamp(mintime)

    try:
        month = months[date.month - 1]
    except IndexError:
        month = months[0]
        year = date.year + 1
    else:
        year = date.year

    while True:
        date = _datetime.date(year, month, 1)

        start = int(_time.mktime(date.timetuple())) + rstart

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
