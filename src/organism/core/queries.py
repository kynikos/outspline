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

properties_create = ('CREATE TABLE Properties (P_id INTEGER PRIMARY KEY, '
                                              'P_max_history INTEGER)')

properties_select = 'SELECT * FROM Properties'

properties_select_history = ('SELECT P_max_history FROM Properties '
                             'WHERE P_max_history IS NOT NULL LIMIT 1')

properties_insert_init = ('INSERT INTO Properties (P_id, P_max_history) '
                          'VALUES (NULL, ?)')

properties_insert_copy = ('INSERT INTO Properties (P_id, P_max_history) '
                          'VALUES (?, ?)')

properties_delete = 'DELETE FROM Properties'

compatibility_create = ('CREATE TABLE CoMpatibility ('
                                                  'CM_id INTEGER PRIMARY KEY, '
                                                  'CM_type TEXT, '
                                                  'CM_addon TEXT, ' 
                                                  'CM_version TEXT)')

compatibility_select = 'SELECT * FROM CoMpatibility'

compatibility_insert = ('INSERT INTO CoMpatibility (CM_id, CM_type, CM_addon, '
                        'CM_version) VALUES (NULL, ?, ?, ?)')

compatibility_insert_copy = ('INSERT INTO CoMpatibility (CM_id, CM_type, '
                             'CM_addon, CM_version) VALUES (?, ?, ?, ?)')

compatibility_delete = 'DELETE FROM CoMpatibility'

items_create = ("CREATE TABLE Items (I_id INTEGER PRIMARY KEY, "
                                    "I_parent INTEGER, "
                                    "I_previous INTEGER, "
                                    "I_text TEXT)")

items_select = 'SELECT * FROM Items'

items_select_tree = 'SELECT I_id FROM Items'

items_select_id = ('SELECT I_parent, I_previous, I_text FROM Items '
                   'WHERE I_id=? LIMIT 1')

items_select_id_parent = 'SELECT I_parent FROM Items WHERE I_id=? LIMIT 1'

items_select_id_editor = 'SELECT I_text FROM Items WHERE I_id=? LIMIT 1'

items_select_id_previous = ('SELECT I_previous FROM Items WHERE I_id=? '
                            'LIMIT 1')

items_select_id_next = 'SELECT I_id FROM Items WHERE I_previous=? LIMIT 1'

items_select_id_children = ('SELECT I_id, I_previous FROM Items '
                            'WHERE I_parent=?')

items_select_id_haschildren = 'SELECT I_id FROM Items WHERE I_parent=? LIMIT 1'

items_select_parent = ('SELECT I_id, I_text FROM Items WHERE I_parent=? AND '
                       'I_previous=? LIMIT 1')

items_insert = ('INSERT INTO Items (I_id, I_parent, I_previous, I_text) '
                'VALUES ({}, {}, {}, ?)')

items_insert_copy = ('INSERT INTO Items (I_id, I_parent, I_previous, I_text) '
                     'VALUES (?, ?, ?, ?)')

items_update_id = 'UPDATE Items SET {} WHERE I_id={}'

items_delete_id = 'DELETE FROM Items WHERE I_id={}'

history_create = ("CREATE TABLE History (H_id INTEGER PRIMARY KEY, "
                                        "H_group INTEGER, "
                                        "H_status INTEGER, "
                                        "H_item INTEGER, "
                                        "H_type TEXT, "
                                        "H_description TEXT, "
                                        "H_redo TEXT, "
                                        "H_redo_text TEXT, "
                                        "H_undo TEXT, "
                                        "H_undo_text TEXT)")

history_select = ('SELECT * FROM History')

# Do not change the index of H_undo [3] and H_undo_text [4]
history_select_group_undo = ('SELECT H_id, H_item, H_type, H_undo, '
                             'H_undo_text FROM History '
                             'WHERE H_group=? ORDER BY H_id DESC')

# Do not change the index of H_redo [3] and H_redo_text [4]
history_select_group_redo = ('SELECT H_id, H_item, H_type, H_redo, '
                             'H_redo_text FROM History '
                             'WHERE H_group=? ORDER BY H_id ASC')

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

history_select_description = ('SELECT DISTINCT H_group, H_status, '
                              'H_description FROM History '
                              'ORDER BY H_group DESC')

history_select_select = ('SELECT H_id FROM History '
                         'WHERE H_status IN (1, 3, 5) AND H_group NOT IN '
                         '(SELECT DISTINCT H_group FROM History '
                         'WHERE H_status IN (1, 3, 5) '
                         'ORDER BY H_group DESC LIMIT ?)')

history_insert = ('INSERT INTO History (H_id, H_group, H_status, '
                  'H_item, H_type, H_description, H_redo, H_redo_text, '
                  'H_undo, H_undo_text) '
                  'VALUES (NULL, ?, 1, ?, ?, ?, ?, ?, ?, ?)')

history_insert_copy = ('INSERT INTO History (H_id, H_group, H_status, H_item, '
                       'H_type, H_description, H_redo, H_redo_text, H_undo, '
                       'H_undo_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')

history_update_status_new = ('UPDATE History SET H_status=5 '
                             'WHERE H_status IN (1, 3)')

history_update_status_old = ('UPDATE History SET H_status=2 '
                             'WHERE H_status IN (0, 4)')

history_update_id = 'UPDATE History SET H_status=? WHERE H_id=?'

history_update_group = ('UPDATE History '
                        'SET H_group = H_group - (SELECT MIN(H_group) '
                        'FROM History) + 1')

history_delete_status = 'DELETE FROM History WHERE H_status IN (0, 2, 4)'

history_delete_id = 'DELETE FROM History WHERE H_id=?'
