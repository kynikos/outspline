# Organism - A simple and extensible outliner.
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

import organism.core_api as core_api

import copypaste
from copypaste import queries


def cut_items(filename, citems, description='Cut items'):
    group = core_api.get_next_history_group(filename)
    return copypaste.copy_items(filename, citems, cut=True, group=group,
                               description=description)


def copy_items(filename, citems):
    return copypaste.copy_items(filename, citems)
    

def paste_items_as_children(filename, baseid, description='Paste as children'):
    group = core_api.get_next_history_group(filename)
    return copypaste.paste_items(filename, baseid, 'children', group=group,
                                description=description)


def paste_items_as_siblings(filename, baseid, description='Paste as siblings'):
    group = core_api.get_next_history_group(filename)
    return copypaste.paste_items(filename, baseid, 'siblings', group=group,
                                description=description)


def has_copied_items(filename):
    return copypaste.has_copied_items(filename)


def select_copy_table():
    qmemory = core_api.get_memory_connection()
    cur = qmemory.cursor()
    cur.execute(queries.copy_select)
    core_api.give_memory_connection(qmemory)
    return cur


def bind_to_copy_items(handler, bind=True):
    return copypaste.copy_items_event.bind(handler, bind)


def bind_to_copy_item(handler, bind=True):
    return copypaste.item_copy_event.bind(handler, bind)


def bind_to_paste_item(handler, bind=True):
    return copypaste.item_paste_event.bind(handler, bind)
