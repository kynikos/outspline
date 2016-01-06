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

import json

import outspline.core.queries as core_queries
from outspline.extensions.organism import queries


def add(cursor):
    cursor.execute(queries.rules_create)
    rows = cursor.execute(core_queries.items_select_tree).fetchall()

    for row in rows:
        cursor.execute(queries.rules_insert, (row['I_id'], json.dumps([])))


def remove(cursor):
    cursor.execute(queries.rules_drop)


def upgrade_0_to_1(cursor):
    # Placeholder/example
    # These queries must stay here because they must not be updated with the
    # normal queries
    pass


def upgrade_1_to_2(cursor):
    # Placeholder/example
    # These queries must stay here because they must not be updated with the
    # normal queries
    pass
