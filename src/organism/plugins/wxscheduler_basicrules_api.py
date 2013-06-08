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

import wxscheduler_basicrules


def simulate_create_except_once_rule(filename, id_, start, end, inclusive):
    kwargs = {
        'filename': filename,
        'id_': id_,
        'rule': {
            'start': start,
            'end': end,
            'inclusive': inclusive,
        }
    }
    wxscheduler_basicrules.except_once.Rule.insert_rule(kwargs)


def simulate_create_occur_every_day_rule(filename, id_, rstart, rendn, rendu,
                                                                        ralarm):
    kwargs = {
        'filename': filename,
        'id_': id_,
        'rule': {
            'rstart': rstart,
            'rendn': rendn,
            'rendu': rendu,
            'ralarm': ralarm,
        }
    }
    wxscheduler_basicrules.occur_every_day.Rule.insert_rule(kwargs)


def simulate_create_occur_once_rule(filename, id_, start, end, ralarm):
    kwargs = {
        'filename': filename,
        'id_': id_,
        'rule': {
            'start': start,
            'end': end,
            'ralarm': ralarm,
        }
    }
    wxscheduler_basicrules.occur_once.Rule.insert_rule(kwargs)
