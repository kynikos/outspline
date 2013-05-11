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

import wxcopypaste


def bind_to_cut_items(handler, bind=True):
    return wxcopypaste.cut_items_event.bind(handler, bind)


def bind_to_paste_items(handler, bind=True):
    return wxcopypaste.paste_items_event.bind(handler, bind)


def simulate_cut_items():
    return wxcopypaste.cut_items(None)


def simulate_copy_items():
    return wxcopypaste.copy_items(None)


def simulate_paste_items_as_siblings():
    return wxcopypaste.paste_items_as_siblings(None)


def simulate_paste_items_as_children():
    return wxcopypaste.paste_items_as_children(None)
