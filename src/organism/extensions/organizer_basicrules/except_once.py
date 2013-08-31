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


def normalize_rule(rule):
    start = int(rule['start'])
    end = int(rule['end'])
    inclusive = rule['inclusive']
    
    if inclusive == 'True':
        inclusive = True
    elif inclusive == 'False':
        inclusive = False
    
    return (start, end, inclusive)


def search_alarms(filename, id_, rule, alarms):
    rule = normalize_rule(rule)
    start = rule[0]
    end = rule[1]
    inclusive = rule[2]
    
    limits = alarms.get_time_span()
    minstart = limits[0]
    maxend = limits[1]

    if start <= maxend and end >= minstart:
        alarms.except_(filename, id_, start, end, inclusive)


def get_occurrences(mint, maxt, filename, id_, rule, tempoccs):
    rule = normalize_rule(rule)
    start = rule[0]
    end = rule[1]
    inclusive = rule[2]
    
    if start <= maxt and end >= mint:
        tempoccs.except_(filename, id_, start, end, inclusive)
