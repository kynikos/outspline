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

from outspline.coreaux_api import Event
import outspline.core_api as core_api

import queries
from exceptions import UnsafePasteWarning

origin_filename = None
copy_items_event = Event()
item_copy_event = Event()
item_paste_event = Event()
items_pasted_event = Event()
paste_check_event = Event()


def copy_items(filename, cids):
    qmemory = core_api.get_memory_connection()
    cursorm = qmemory.cursor()
    cursorm.execute(queries.copy_delete)
    core_api.give_memory_connection(qmemory)

    copy_items_event.signal()

    global origin_filename
    origin_filename = filename

    for id_ in cids:
        info = core_api.get_item_info(filename, id_)
        record = (id_, info['parent'], info['previous'], info['text'])

        qmemory = core_api.get_memory_connection()
        cursorm = qmemory.cursor()
        cursorm.execute(queries.copy_insert, record)
        core_api.give_memory_connection(qmemory)

        item_copy_event.signal(filename=filename, id_=id_)


def paste_items(filename, baseid, mode, group, description='Paste items'):
    qmemory = core_api.get_memory_connection()
    cursor = qmemory.cursor()
    cursor.execute(queries.copy_select_parent_roots)
    old_roots = cursor.fetchall()
    core_api.give_memory_connection(qmemory)

    old_to_new_ids = {}

    def recurse(baseid, previd):
        cursor.execute(queries.copy_select_parent, (baseid, previd))
        child = cursor.fetchone()

        if child:
            id_ = child['C_id']

            old_to_new_ids[id_] = core_api.append_item(
                                filename, old_to_new_ids[baseid], group=group,
                                text=child['C_text'], description=description)

            item_paste_event.signal(filename=filename, id_=old_to_new_ids[id_],
                                    oldid=id_, group=group,
                                    description=description)

            recurse(id_, 0)
            recurse(baseid, id_)

    if mode == 'siblings':
        old_roots.reverse()

    for root in old_roots:
        if mode == 'children':
            old_to_new_ids[root['C_id']] = core_api.append_item(
                                filename, baseid, group=group,
                                text=root['C_text'], description=description)
        elif mode == 'siblings':
            old_to_new_ids[root['C_id']] = core_api.insert_item_after(
                                filename, baseid, group=group,
                                text=root['C_text'], description=description)

        item_paste_event.signal(filename=filename,
                                            id_=old_to_new_ids[root['C_id']],
                                            oldid=root['C_id'], group=group,
                                            description=description)

        recurse(root['C_id'], 0)

    new_ids = old_to_new_ids.values()
    new_roots = [old_to_new_ids[root['C_id']] for root in old_roots]

    items_pasted_event.signal()

    return (new_roots, new_ids)


def can_paste_safely(filename):
    try:
        paste_check_event.signal(filename=filename,
                                                exception=UnsafePasteWarning)
    except UnsafePasteWarning:
        return False
    else:
        return True


def has_copied_items(filename):
    qmemory = core_api.get_memory_connection()
    cursor = qmemory.cursor()
    cursor.execute(queries.copy_select_check)
    core_api.give_memory_connection(qmemory)

    if cursor.fetchone():
        return True
    else:
        return False


def main():
    qmemory = core_api.get_memory_connection()
    cursor = qmemory.cursor()
    cursor.execute(queries.copy_create)
    core_api.give_memory_connection(qmemory)
