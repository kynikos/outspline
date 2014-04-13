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

import occur_regularly
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
        refstarts = []

        for rstart in rstarts:
            if isinstance(rstart, int) and rstart >= 0:
                refstarts.append(refstart + rstart)
            else:
                raise BadRuleError()

        # Also take a possible negative (late) alarm time into account, in fact
        #  the occurrence wouldn't be found if the search range included the
        #  alarm time but not the actual occurrence time span; remember that
        #  it's normal that the occurrence is not added to the results if the
        #  search range is between (and doesn't include) the alarm time and the
        #  actual occurrence time span
        if ralarm is None:
            rmax = max((rend, 0))
        else:
            rmax = max((rend, ralarm * -1, 0))

        overlaps = rmax // interval
        bgap = interval - rmax % interval

        return {
            'rule': _RULE_NAMES[standard],
            '#': (
                refstarts,
                interval,
                overlaps,
                bgap,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise BadRuleError()


def get_occurrences_range_local(mint, utcmint, maxt, utcoffset, filename, id_,
                                                                rule, occs):
    for refstart in rule['#'][0]:
        srule = rule.copy()
        srule['#'][0] = refstart
        occur_regularly.get_occurrences_range_local(mint, utcmint, maxt,
                                        utcoffset, filename, id_, srule, occs)


def get_occurrences_range_UTC(mint, utcmint, maxt, utcoffset, filename, id_,
                                                                rule, occs):
    for refstart in rule['#'][0]:
        srule = rule.copy()
        srule['#'][0] = refstart
        occur_regularly.get_occurrences_range_UTC(mint, utcmint, maxt,
                                        utcoffset, filename, id_, srule, occs)


def get_next_item_occurrences_local(base_time, utcbase, utcoffset, filename,
                                                            id_, rule, occs):
    for refstart in rule['#'][0]:
        srule = rule.copy()
        srule['#'][0] = refstart
        occur_regularly.get_next_item_occurrences_local(base_time, utcbase,
                                        utcoffset, filename, id_, srule, occs)


def get_next_item_occurrences_UTC(base_time, utcbase, utcoffset, filename,
                                                            id_, rule, occs):
    for refstart in rule['#'][0]:
        srule = rule.copy()
        srule['#'][0] = refstart
        occur_regularly.get_next_item_occurrences_UTC(base_time, utcbase,
                                        utcoffset, filename, id_, srule, occs)
