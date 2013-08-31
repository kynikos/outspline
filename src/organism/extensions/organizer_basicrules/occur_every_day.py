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


def normalize_rule(reftime, rule):
    rstart = int(rule['rstart'])
    rendn = rule['rendn']
    rendu = rule['rendu']
    ralarm = rule['ralarm']
    
    if rendn == 'None':
        rendn = None
    # rendn could have been already None (not a string)
    elif rendn != None:
        rendn = int(rendn)
    
    if rendu == 'None':
        rendu = None
    
    if ralarm == 'None':
        ralarm = None
    # alarm could have been already None (not a string)
    elif ralarm != None:
        ralarm = int(ralarm)
            
    if rendn != None:
        mult = {'minutes': 60,
                'hours': 3600,
                'days': 86400,
                'weeks': 604800,
                'months': 2592000,
                'years': 31536000}
        
        rend = rendn * mult[rendu]
    else:
        rend = None
    
    firstday = reftime // 86400 * 86400 + _time.altzone
    rday = reftime % 86400
    
    if rstart < rday:
        start = firstday + 86400 + rstart
    else:
        start = firstday + rstart
    
    return (start, rend, ralarm)


def search_alarms(last_search, filename, id_, rule, alarms):
    rule = normalize_rule(last_search, rule)
    rend = rule[1]
    ralarm = rule[2]
    
    if rend != None:
        # This algorithm must get also occurrences whose end time is the next
        # alarm
        start = rule[0] - 86400 * (1 + rend // 86400)
    else:
        start = rule[0]
    
    while True:
        if rend != None:
            end = start + rend
        else:
            end = None
        
        if ralarm != None:
            alarm = start - ralarm
        else:
            alarm = None
        
        alarmd = {'filename': filename,
                  'id_': id_,
                  'start': start,
                  'end': end,
                  'alarm': alarm}
        
        next_alarm = alarms.get_next_alarm()
        
        if alarms.add(last_search, alarmd) or (next_alarm and
                                      (alarm is None and start > next_alarm) or
                                               (alarm and alarm > next_alarm)):
            break
        
        start += 86400


def get_occurrences(mint, maxt, filename, id_, rule, tempoccs):
    rule = normalize_rule(mint, rule)
    rend = rule[1]
    ralarm = rule[2]
    
    if rend != None:
        # This algorithm must get also occurrences whose end time falls within
        # the requested range
        start = rule[0] - 86400 * (1 + rend // 86400)
    else:
        start = rule[0]
    
    while True:
        if rend != None:
            end = start + rend
        else:
            end = None
        
        if ralarm != None:
            alarm = start - ralarm
        else:
            alarm = None
        
        if (alarm and alarm > maxt) or start > maxt:
            break
        
        tempoccs.add({'filename': filename,
                      'id_': id_,
                      'start': start,
                      'end': end,
                      'alarm': alarm})
        
        start += 86400
