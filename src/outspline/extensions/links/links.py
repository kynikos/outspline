# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2014 Dario Giovannetti <dev@dariogiovannetti.net>
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

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
copypaste_api = coreaux_api.import_optional_extension_api('copypaste')
organism_api = coreaux_api.import_optional_extension_api('organism')

import queries
import exceptions

cdbs = set()


def select_links(filename):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.links_select)
    core_api.give_connection(filename, qconn)

    return cursor.fetchall()


def upsert_link(filename, id_, target, group, description='Insert link',
                                                                event=True):
    # target could be None (creating a broken link) or could be a no-longer
    # existing item
    if core_api.is_item(filename, target):
        # Forbid circular links (including links to self), as it could generate
        # unexpected infinite recursions (e.g. with synchronize_links_text)
        if id_ in find_links_chain(filename, target):
            raise exceptions.CircularLinksError()
        else:
            # Sync text
            tgttext = core_api.get_item_text(filename, target)

            if event:
                core_api.update_item_text(filename, id_, tgttext, group=group,
                                                    description=description)
            else:
                core_api.update_item_text_no_event(filename, id_, tgttext,
                                        group=group, description=description)

            # Drop any rules
            if organism_api:
                organism_api.update_item_rules(filename, id_, [], group=group,
                                                       description=description)
    else:
        # Force target = None if the given target no longer exists
        target = None

        # Drop any rules
        if organism_api:
            organism_api.update_item_rules(filename, id_, [], group=group,
                                                       description=description)

    # Note that exceptions.CircularLinksError could be raised before getting
    # here
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()

    cursor.execute(queries.links_select_id, (id_, ))
    res = cursor.fetchone()

    # Do not allow creating more than one link per item
    if res:
        oldtarget = res['L_target']

        query_redo = queries.links_update_id.format(target
                                        if target is not None else 'NULL', id_)
        query_undo = queries.links_update_id.format(oldtarget
                                     if oldtarget is not None else 'NULL', id_)

        cursor.execute(query_redo)
    else:
        # Allow the creation of a broken link
        query_redo = queries.links_insert.format(id_, target
                                             if target is not None else 'NULL')
        query_undo = queries.links_delete_id.format(id_)

        cursor.execute(query_redo)

    core_api.give_connection(filename, qconn)

    core_api.insert_history(filename, group, id_, 'link_upsert', description,
                                            query_redo, None, query_undo, None)


def synchronize_links_text(filename, target, text, group, description):
    if filename in cdbs:
        for id_ in find_back_links(filename, target):
            core_api.update_item_text(filename, id_, text, group, description)


def delete_link(filename, id_, group, description='Delete link'):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()

    cursor.execute(queries.links_select_id, (id_, ))
    res = cursor.fetchone()

    if res:
        target = res['L_target']

        query_redo = queries.links_delete_id.format(id_)
        query_undo = queries.links_insert.format(id_, target
                                             if target is not None else 'NULL')

        cursor.execute(query_redo)

        core_api.give_connection(filename, qconn)

        core_api.insert_history(filename, group, id_, 'link_delete',
                   description, query_redo, None, query_undo, None)
    else:
        core_api.give_connection(filename, qconn)


def break_links(filename, id_, group, description='Break links'):
    # Break any links that point to the item
    # Don't just delete those links, as it would leave their associated
    # items in an unexpected state for the user (back to normal,
    # undistinguished items); also this further action should be handled
    # properly by the interface somehow
    # Don't try to delete the links and their associated items, because
    # silently deleting items that were not selected would be confusing;
    # furthermore, theoretically link items are allowed (at least in the
    # back-end) to have their own children, which should be deleted too
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.links_select_target, (id_, ))

    for row in cursor.fetchall():
        linkid = row['L_id']

        query_redo = queries.links_update_id.format('NULL', linkid)
        query_undo = queries.links_update_id.format(id_, linkid)

        cursor.execute(query_redo)

        core_api.give_connection(filename, qconn)

        core_api.insert_history(filename, group, id_, 'link_break',
                   description, query_redo, None, query_undo, None)

        qconn = core_api.get_connection(filename)
        cursor = qconn.cursor()

    core_api.give_connection(filename, qconn)


def break_copied_links(filename, id_):
    # Breaking links in the CopyLinks table will not be stored in the history,
    # so this is useful only if undoing/redoing changes will warn the user and
    # break all the copied links
    if copypaste_api.get_copy_origin_filename() == filename:
        mconn = core_api.get_memory_connection()
        curm = mconn.cursor()

        curm.execute(queries.copylinks_select_target, (id_, ))

        for row in curm.fetchall():
            curm.execute(queries.copylinks_update_id, (row['CL_id'], ))

        core_api.give_memory_connection(mconn)


def break_all_copied_links(filename):
    if copypaste_api.get_copy_origin_filename() == filename:
        mconn = core_api.get_memory_connection()
        curm = mconn.cursor()
        curm.execute(queries.copylinks_update_id_break)
        core_api.give_memory_connection(mconn)


def find_link_target(filename, id_):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.links_select_id, (id_, ))
    core_api.give_connection(filename, qconn)

    row = cursor.fetchone()

    # If it's a valid link return its target id; if it's a broken link
    # return None; if it's not a link return False
    try:
        return row['L_target']
    except TypeError:
        return False


def find_links_chain(filename, id_):
    chain = []

    while id_ is not False:
        chain.append(id_)
        id_ = find_link_target(filename, id_)

    return chain


def find_broken_links(filename):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.links_select_target, (None, ))
    core_api.give_connection(filename, qconn)

    return [row['L_id'] for row in cursor.fetchall()]


def find_first_broken_link(filename):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.links_select_target_broken)
    core_api.give_connection(filename, qconn)

    try:
        return row['L_id']
    except TypeError:
        return None


def find_back_links(filename, id_):
    qconn = core_api.get_connection(filename)
    cursor = qconn.cursor()
    cursor.execute(queries.links_select_target, (id_, ))
    core_api.give_connection(filename, qconn)

    return [row['L_id'] for row in cursor.fetchall()]


def copy_link(filename, id_):
    if filename in cdbs:
        target = find_link_target(filename, id_)

        if target is not False:
            mem = core_api.get_memory_connection()
            curm = mem.cursor()
            curm.execute(queries.copylinks_insert, (id_, target))
            core_api.give_memory_connection(mem)


def can_paste_safely(filename, exception):
    mem = core_api.get_memory_connection()
    curm = mem.cursor()
    curm.execute(queries.copylinks_select)
    core_api.give_memory_connection(mem)

    # Warn if CopyLinks table has links but filename doesn't support them
    if curm.fetchone() and filename not in cdbs:
        raise exception()


def paste_link(filename, id_, oldid, group, description):
    if filename in cdbs:
        mem = core_api.get_memory_connection()
        curm = mem.cursor()
        curm.execute(queries.copylinks_select_id, (oldid, ))
        core_api.give_memory_connection(mem)
        row = curm.fetchone()

        if row:
            # Item is a link
            if copypaste_api.get_copy_origin_filename() == filename:
                # Pasting on the same database is always safe, although the
                # link could have been broken by a deletion or a history change
                target = row['CL_target']
            else:
                # If pasting on a different database, the link must be broken,
                # in fact even if the target is pasted too there's not a simple
                # way of retrieving its new id
                target = None

            # Do not emit an update event when pasting links (affects only
            # pasting in the same database), otherwise the interface will react
            # trying to update the text of the item in the tree, but the item
            # hasn't been created yet in the tree, resulting in an exception
            # (KeyError)
            # Right because the item is inserted in the tree *after* updating
            # its text, it will be added already with the correct text, so
            # there's no need to handle an update event in that case
            upsert_link(filename, id_, target, group, description, event=False)
