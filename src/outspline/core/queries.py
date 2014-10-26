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

master_select_tables = "SELECT name FROM sqlite_master WHERE type='table'"

master_select_table = "SELECT * FROM {}"

master_insert = "INSERT INTO {} ({}) VALUES ({})"

master_delete = "DELETE FROM {}"

properties_create = ('CREATE TABLE Properties (P_id INTEGER PRIMARY KEY, '
                                              'P_max_history INTEGER)')

properties_select_history = ('SELECT P_max_history FROM Properties '
                             'WHERE P_max_history IS NOT NULL LIMIT 1')

properties_insert_dummy = ('INSERT INTO Properties (P_id, P_max_history) '
                                                        'VALUES (NULL, NULL)')

properties_update = 'UPDATE Properties SET P_max_history=?'

properties_insert_init = ('INSERT INTO Properties (P_id, P_max_history) '
                          'VALUES (NULL, ?)')

properties_delete_dummy = 'DELETE FROM Properties WHERE P_max_history IS NULL'

compatibility_create = ('CREATE TABLE CoMpatibility ('
                                                  'CM_id INTEGER PRIMARY KEY, '
                                                  'CM_extension TEXT, '
                                                  'CM_version INTEGER)')

compatibility_select = 'SELECT * FROM CoMpatibility'

compatibility_insert = ('INSERT INTO CoMpatibility (CM_id, CM_extension, '
                        'CM_version) VALUES (NULL, ?, ?)')

compatibility_insert_ignored = ('INSERT INTO CoMpatibility (CM_id, '
                            'CM_extension, CM_version) VALUES (NULL, ?, NULL)')

compatibility_update_core = ('UPDATE CoMpatibility SET CM_version=? '
                                                'WHERE CM_extension IS NULL')

compatibility_update_extension = ('UPDATE CoMpatibility SET CM_version=? '
                                                'WHERE CM_extension=?')

compatibility_delete = 'DELETE FROM CoMpatibility WHERE CM_extension=?'

items_create = ("CREATE TABLE Items (I_id INTEGER PRIMARY KEY, "
                                    "I_parent INTEGER, "
                                    "I_previous INTEGER, "
                                    "I_text TEXT)")

items_select_tree = 'SELECT I_id FROM Items'

items_select_id = ('SELECT I_parent, I_previous, I_text FROM Items '
                   'WHERE I_id=? LIMIT 1')

items_select_id_parent = 'SELECT I_parent FROM Items WHERE I_id=? LIMIT 1'

items_select_id_editor = 'SELECT I_text FROM Items WHERE I_id=? LIMIT 1'

items_select_id_previous = ('SELECT I_previous FROM Items WHERE I_id=? '
                            'LIMIT 1')

items_select_id_next = 'SELECT I_id FROM Items WHERE I_previous=? LIMIT 1'

items_select_id_children = 'SELECT I_id FROM Items WHERE I_parent=?'

items_select_id_haschildren = 'SELECT I_id FROM Items WHERE I_parent=? LIMIT 1'

items_select_parent = ('SELECT I_id FROM Items WHERE I_parent=? AND '
                                                        'I_previous=? LIMIT 1')

items_select_parent_previous = ('SELECT I_parent, I_previous FROM Items '
                                                        'WHERE I_id=? LIMIT 1')

items_select_parent_text = ('SELECT I_id, I_text FROM Items '
                                'WHERE I_parent=? AND I_previous=? LIMIT 1')

items_select_search = 'SELECT I_id, I_text FROM Items'

items_insert = ('INSERT INTO Items (I_id, I_parent, I_previous, I_text) '
                'VALUES (?, ?, ?, ?)')

items_update_previous = 'UPDATE Items SET I_previous=? WHERE I_id=?'

items_update_parent = 'UPDATE Items SET I_parent=?, I_previous=? WHERE I_id=?'

items_update_text = 'UPDATE Items SET I_text=? WHERE I_id=?'

items_delete_id = 'DELETE FROM Items WHERE I_id=?'

history_create = ("CREATE TABLE History (H_id INTEGER PRIMARY KEY, "
                                        "H_group INTEGER, "
                                        "H_status INTEGER, "
                                        "H_item INTEGER, "
                                        "H_type TEXT, "
                                        "H_tstamp INTEGER, "
                                        "H_description TEXT, "
                                        "H_redo TEXT, "
                                        "H_undo TEXT)")

# Do not change the index of H_undo [3]
history_select_group_undo = ('SELECT H_id, H_item, H_type, H_undo '
                             'FROM History WHERE H_group=? ORDER BY H_id DESC')

# Do not change the index of H_redo [3]
history_select_group_redo = ('SELECT H_id, H_item, H_type, H_redo '
                             'FROM History WHERE H_group=? ORDER BY H_id ASC')

history_select_status = ('SELECT H_status FROM History '
                         'WHERE H_status IN (0, 1, 3, 4) LIMIT 1')

history_select_status_next = ('SELECT MAX(H_group) AS H_group '
                              'FROM History WHERE H_status IN (1, 3, 5)')

history_select_status_undo = ('SELECT H_group, H_status '
                              'FROM History WHERE H_status IN (1, 3, 5) '
                              'ORDER BY H_group DESC LIMIT 1')

history_select_status_redo = ('SELECT H_group, H_status '
                              'FROM History WHERE H_status IN (0, 2, 4) '
                              'ORDER BY H_group ASC LIMIT 1')

history_select_description = ('SELECT DISTINCT H_group, H_status, H_tstamp, '
                              'H_description FROM History '
                              'ORDER BY H_group DESC, H_tstamp DESC')

history_insert = ('INSERT INTO History (H_id, H_group, H_status, '
                  'H_item, H_type, H_tstamp, H_description, H_redo, H_undo) '
                  'VALUES (NULL, ?, 1, ?, ?, strftime("%s", "now"), ?, ?, ?)')

history_update_status_new = ('UPDATE History SET H_status=5 '
                             'WHERE H_status IN (1, 3)')

history_update_status_old = ('UPDATE History SET H_status=2 '
                             'WHERE H_status IN (0, 4)')

history_update_id = 'UPDATE History SET H_status=? WHERE H_id=?'

history_update_group = ('UPDATE History '
                        'SET H_group = H_group - (SELECT MIN(H_group) '
                        'FROM History) + 1')

history_delete_status = 'DELETE FROM History WHERE H_status IN (0, 2, 4)'

# Don't delete statuses 0, 2, 4 this way, because those actions are ahead of
# the current database status, and at most they should be deleted in ascending
# order; however, they'll be deleted anyway the next time an action is done, so
# they can just be left alone here
# Don't just use ORDER BY and OFFSET directly in the main DELETE query, because
# groups have to be kept intact
history_delete_select = ('''
DELETE FROM History WHERE H_group < (
    SELECT MIN(H_group) FROM (
        SELECT DISTINCT H_group FROM History WHERE H_status IN (1, 3, 5)
        ORDER BY H_group DESC LIMIT ?
    )
)''')

# There can't be entries with statuses 0, 2, 4 because this query is executed
# only when *inserting* a group in the history, and before that all 0, 2 and 4
# actions are deleted by history_delete_status
# Don't just use ORDER BY and OFFSET directly in the main DELETE query, because
# groups have to be kept intact
history_delete_union = ('''
DELETE FROM History WHERE H_group < (
    SELECT MIN(H_group) FROM (
        SELECT H_group FROM (
            SELECT DISTINCT H_group FROM History ORDER BY H_group DESC LIMIT ?
        )
        UNION
        SELECT H_group FROM (
            SELECT DISTINCT H_group FROM History
            WHERE H_tstamp >= strftime("%s", "now") - ? * 60
            ORDER BY H_group DESC LIMIT ?
        )
    )
)''')

history_delete_purge = 'DELETE FROM History'
