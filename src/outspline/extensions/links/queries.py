# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

links_create = ("CREATE TABLE Links (L_id INTEGER, "
                                       "L_target INTEGER)")

links_select = 'SELECT * FROM Links'

links_select_id = 'SELECT L_target FROM Links WHERE L_id=? LIMIT 1'

links_select_target = 'SELECT L_id FROM Links WHERE L_target=?'

links_select_target_broken = ('SELECT L_id FROM Links WHERE L_target=NULL '
                              'LIMIT 1')

links_insert = 'INSERT INTO Links (L_id, L_target) VALUES ({}, {})'

links_insert_copy = 'INSERT INTO Links (L_id, L_target) VALUES (?, ?)'

links_update_id = 'UPDATE Links SET L_target={} WHERE L_id={}'

links_delete_id = 'DELETE FROM Links WHERE L_id={}'

copylinks_create = ("CREATE TABLE CopyLinks (CL_id INTEGER, "
                                            "CL_target INTEGER)")

copylinks_select = 'SELECT CL_id FROM CopyLinks LIMIT 1'

copylinks_select_id = 'SELECT CL_target FROM CopyLinks WHERE CL_id=?'

copylinks_select_target = 'SELECT CL_id FROM CopyLinks WHERE CL_target=?'

copylinks_insert = 'INSERT INTO CopyLinks (CL_id, CL_target) VALUES (?, ?)'

copylinks_update_id = 'UPDATE CopyLinks SET CL_target=NULL WHERE CL_id=?'

copylinks_update_id_break = 'UPDATE CopyLinks SET CL_target=NULL'

copylinks_delete = 'DELETE FROM CopyLinks'
