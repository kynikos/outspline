# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

from organism_basicrules import (occur_once, occur_regularly,
                    occur_regularly_group, occur_monthly_number_direct,
                    occur_monthly_number_inverse, occur_monthly_weekday_direct,
                    occur_monthly_weekday_inverse, occur_yearly,
                    except_once, except_regularly)
from organism_basicrules.exceptions import BadRuleError


def make_occur_once_rule_local(start, end, alarm, guiconfig):
    return occur_once.make_rule(start, end, alarm, 'local', guiconfig)


def make_occur_once_rule_UTC(start, end, alarm, guiconfig):
    return occur_once.make_rule(start, end, alarm, 'UTC', guiconfig)


def make_occur_regularly_rule_local(refstart, interval, rend, ralarm,
                                                                    guiconfig):
    return occur_regularly.make_rule(refstart, interval, rend, ralarm,
                                                        'local', guiconfig)


def make_occur_regularly_rule_UTC(refstart, interval, rend, ralarm,
                                                                    guiconfig):
    return occur_regularly.make_rule(refstart, interval, rend, ralarm,
                                                        'UTC', guiconfig)


def make_occur_regularly_group_rule_local(refstart, interval, rstarts, rend,
                                                            ralarm, guiconfig):
    return occur_regularly_group.make_rule(refstart, interval, rstarts, rend,
                                                    ralarm, 'local', guiconfig)


def make_occur_regularly_group_rule_UTC(refstart, interval, rstarts, rend,
                                                            ralarm, guiconfig):
    return occur_regularly_group.make_rule(refstart, interval, rstarts, rend,
                                                    ralarm, 'UTC', guiconfig)


def make_occur_monthly_number_direct_rule_local(months, day, hour, minute,
                                                    rend, ralarm, guiconfig):
    return occur_monthly_number_direct.make_rule(months, day, hour, minute,
                                            rend, ralarm, 'local', guiconfig)


def make_occur_monthly_number_direct_rule_UTC(months, day, hour, minute, rend,
                                                            ralarm, guiconfig):
    return occur_monthly_number_direct.make_rule(months, day, hour, minute,
                                                rend, ralarm, 'UTC', guiconfig)


def make_occur_monthly_number_inverse_rule_local(months, day, hour, minute,
                                                    rend, ralarm, guiconfig):
    return occur_monthly_number_inverse.make_rule(months, day, hour, minute,
                                            rend, ralarm, 'local', guiconfig)


def make_occur_monthly_number_inverse_rule_UTC(months, day, hour, minute, rend,
                                                            ralarm, guiconfig):
    return occur_monthly_number_inverse.make_rule(months, day, hour, minute,
                                                rend, ralarm, 'UTC', guiconfig)


def make_occur_monthly_weekday_direct_rule_local(months, weekday, number,
                                        hour, minute, rend, ralarm, guiconfig):
    return occur_monthly_weekday_direct.make_rule(months, weekday, number,
                                hour, minute, rend, ralarm, 'local', guiconfig)


def make_occur_monthly_weekday_direct_rule_UTC(months, weekday, number, hour,
                                            minute, rend, ralarm, guiconfig):
    return occur_monthly_weekday_direct.make_rule(months, weekday, number,
                                hour, minute, rend, ralarm, 'UTC', guiconfig)


def make_occur_monthly_weekday_inverse_rule_local(months, weekday, number,
                                        hour, minute, rend, ralarm, guiconfig):
    return occur_monthly_weekday_inverse.make_rule(months, weekday, number,
                                hour, minute, rend, ralarm, 'local', guiconfig)


def make_occur_monthly_weekday_inverse_rule_UTC(months, weekday, number,
                                        hour, minute, rend, ralarm, guiconfig):
    return occur_monthly_weekday_inverse.make_rule(months, weekday, number,
                                hour, minute, rend, ralarm, 'UTC', guiconfig)


def make_occur_yearly_rule_local(interval, refyear, month, day, hour,
                                            minute, rend, ralarm, guiconfig):
    return occur_yearly.make_rule(interval, refyear, month, day, hour,
                                    minute, rend, ralarm, 'local', guiconfig)


def make_occur_yearly_rule_UTC(interval, refyear, month, day, hour,
                                            minute, rend, ralarm, guiconfig):
    return occur_yearly.make_rule(interval, refyear, month, day, hour,
                                        minute, rend, ralarm, 'UTC', guiconfig)


def make_except_once_rule_local(start, end, inclusive, guiconfig):
    return except_once.make_rule(start, end, inclusive, 'local', guiconfig)


def make_except_once_rule_UTC(start, end, inclusive, guiconfig):
    return except_once.make_rule(start, end, inclusive, 'UTC', guiconfig)


def make_except_regularly_rule_local(refstart, interval, rend,
                                                        inclusive, guiconfig):
    return except_regularly.make_rule(refstart, interval, rend,
                                                inclusive, 'local', guiconfig)


def make_except_regularly_rule_UTC(refstart, interval, rend, inclusive,
                                                                    guiconfig):
    return except_regularly.make_rule(refstart, interval, rend,
                                                inclusive, 'UTC', guiconfig)
