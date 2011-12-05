# Organism - Organism, a simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.com>
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
    end = rule['end']
    ralarm = rule['ralarm']
    
    if end == 'None':
        end = None
    # end could have been already None (not a string)
    elif end != None:
        end = int(end)
    
    if ralarm == 'None':
        alarm = None
    elif ralarm == None:
        alarm = None
    elif ralarm != None:
        alarm = start - int(ralarm)
    
    return (start, end, alarm)
    
def search_alarms(last_search, filename, id_, rule, alarms):
    rule = normalize_rule(rule)
    start = rule[0]
    end = rule[1]
    alarm = rule[2]
    
    alarms.add(last_search, {'filename': filename,
                             'id_': id_,
                             'start': start,
                             'end': end,
                             'alarm': alarm})


def get_occurrences(filename, id_, rule, tempoccs):
    rule = normalize_rule(rule)
    start = rule[0]
    end = rule[1]
    alarm = rule[2]
    
    tempoccs.add({'filename': filename,
                  'id_': id_,
                  'start': start,
                  'end': end,
                  'alarm': alarm})
