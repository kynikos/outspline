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

from organizer_basicrules import (occur_once, occur_regularly_single,
                             occur_regularly_group, occur_monthly_number_direct,
                     occur_monthly_number_inverse, occur_monthly_weekday_direct,
                 occur_monthly_weekday_inverse, occur_yearly_group, except_once)
from organizer_basicrules.exceptions import BadRuleError


def make_occur_once_rule(start, end, alarm, guiconfig):
    return occur_once.make_rule(start, end, alarm, guiconfig)


def make_occur_regularly_single_rule(refstart, interval, rend, ralarm,
                                                                     guiconfig):
    return occur_regularly_single.make_rule(refstart, interval, rend, ralarm,
                                                                      guiconfig)


def make_occur_regularly_group_rule(refstart, interval, rstarts, rend, ralarm,
                                                                     guiconfig):
    return occur_regularly_group.make_rule(refstart, interval, rstarts, rend,
                                                              ralarm, guiconfig)


def make_occur_monthly_number_direct_rule(months, rstart, rend, ralarm,
                                                                     guiconfig):
    return occur_monthly_number_direct.make_rule(months, rstart, rend, ralarm,
                                                                      guiconfig)


def make_occur_monthly_number_inverse_rule(months, rstart, rend, ralarm,
                                                                     guiconfig):
    return occur_monthly_number_inverse.make_rule(months, rstart, rend, ralarm,
                                                                      guiconfig)


def make_occur_monthly_weekday_direct_rule(months, weekday, number, rstart,
                                                       rend, ralarm, guiconfig):
    return occur_monthly_weekday_direct.make_rule(months, weekday, number,
                                                rstart, rend, ralarm, guiconfig)


def make_occur_monthly_weekday_inverse_rule(months, weekday, number, rstart,
                                                       rend, ralarm, guiconfig):
    return occur_monthly_weekday_inverse.make_rule(months, weekday, number,
                                                rstart, rend, ralarm, guiconfig)


def make_occur_yearly_group_rule(occs, occsl, rend, ralarm, guiconfig):
    return occur_yearly_group.make_rule(occs, occsl, rend, ralarm, guiconfig)


def make_except_once_rule(start, end, inclusive, guiconfig):
    return except_once.make_rule(start, end, inclusive, guiconfig)
