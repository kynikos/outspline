# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import organism.core_api as core_api
import organism.extensions.organizer_api as organizer_api
import organism.extensions.organizer_alarms_api as organizer_alarms_api

import occur_once, occur_every_day, except_once


def handle_search_alarms(kwargs):
    last_search = kwargs['last_search']
    filename = kwargs['filename']
    id_ = kwargs['id_']
    rule = kwargs['rule']
    alarms = kwargs['alarms']
    
    if rule['rule'] == 'occur_once':
        occur_once.search_alarms(last_search, filename, id_, rule, alarms)
    elif rule['rule'] == 'occur_every_day':
        occur_every_day.search_alarms(last_search, filename, id_, rule, alarms)
    elif rule['rule'] == 'except_once':
        except_once.search_alarms(filename, id_, rule, alarms)


def handle_get_occurrences(kwargs):
    mint = kwargs['mint']
    maxt = kwargs['maxt']
    filename = kwargs['filename']
    id_ = kwargs['id_']
    rule = kwargs['rule']
    tempoccs = kwargs['tempoccs']
    
    if rule['rule'] == 'occur_once':
        occur_once.get_occurrences(filename, id_, rule, tempoccs)
    elif rule['rule'] == 'occur_every_day':
        occur_every_day.get_occurrences(mint, maxt, filename, id_, rule,
                                        tempoccs)
    elif rule['rule'] == 'except_once':
        except_once.get_occurrences(mint, maxt, filename, id_, rule, tempoccs)


def main():
    organizer_api.bind_to_get_occurrences(handle_get_occurrences)
    organizer_alarms_api.bind_to_search_alarms(handle_search_alarms)
