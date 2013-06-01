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


def _compute_alarm(start, ralarm):
    return None if (ralarm == None) else (start - ralarm)


def get_occurrences_range(filename, id_, rule, occs):
    start = rule['start']
    end = rule['end']
    ralarm = rule['ralarm']

    alarm = _compute_alarm(start, ralarm)

    # The rule is checked in wxscheduler_basicrules.occur_once, no need to use
    # occs.add
    occs.add_safe({'filename': filename,
                   'id_': id_,
                   'start': start,
                   'end': end,
                   'alarm': alarm})

def get_next_item_occurrences(base_time, filename, id_, rule, occs):
    start = rule['start']
    end = rule['end']
    ralarm = rule['ralarm']

    alarm = _compute_alarm(start, ralarm)

    # The rule is checked in wxscheduler_basicrules.occur_once, no need to use
    # occs.add
    occs.add_safe(base_time, {'filename': filename,
                         'id_': id_,
                         'start': start,
                         'end': end,
                         'alarm': alarm})
