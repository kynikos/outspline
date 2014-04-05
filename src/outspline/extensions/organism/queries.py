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

rules_create = ("CREATE TABLE Rules (R_id INTEGER PRIMARY KEY, "
                                    "R_rules TEXT)")

rules_select = 'SELECT * FROM Rules'

rules_select_id = 'SELECT R_rules FROM Rules WHERE R_id=? LIMIT 1'

rules_insert = 'INSERT INTO Rules (R_id, R_rules) VALUES (?, ?)'

rules_update_id = 'UPDATE Rules SET R_rules=? WHERE R_id={}'

rules_delete_id = 'DELETE FROM Rules WHERE R_id={}'

copyrules_create = ("CREATE TABLE CopyRules (CR_id INTEGER, "
                                            "CR_rules TEXT)")

copyrules_select = 'SELECT CR_id FROM CopyRules WHERE CR_rules!=? LIMIT 1'

copyrules_select_id = 'SELECT CR_rules FROM CopyRules WHERE CR_id=?'

copyrules_insert = 'INSERT INTO CopyRules (CR_id, CR_rules) VALUES (?, ?)'

copyrules_delete = 'DELETE FROM CopyRules'
