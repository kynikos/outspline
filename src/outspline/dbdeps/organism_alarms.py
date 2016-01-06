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

import outspline.coreaux_api as coreaux_api
from outspline.extensions.organism_alarms import queries


def add(cursor):
    LIMIT = coreaux_api.get_extension_configuration('organism_alarms'
                                        ).get_int('default_log_soft_limit')

    cursor.execute(queries.alarmsproperties_create)
    cursor.execute(queries.alarmsproperties_insert_init, (LIMIT, ))
    cursor.execute(queries.alarms_create)
    cursor.execute(queries.alarmsofflog_create)

def remove(cursor):
    cursor.execute(queries.alarmsproperties_drop)
    cursor.execute(queries.alarms_drop)
    cursor.execute(queries.alarmsofflog_drop)

def upgrade_0_to_1(cursor):
    # These queries must stay here because they must not be updated with the
    # normal queries
    cursor.execute('CREATE TABLE AlarmsProperties '
                              '(AP_id INTEGER PRIMARY KEY, '
                               'AP_log_limit INTEGER)')
    LIMIT = coreaux_api.get_extension_configuration('organism_alarms'
                                        ).get_int('default_log_soft_limit')
    cursor.execute('INSERT INTO AlarmsProperties (AP_id, AP_log_limit) '
                                                'VALUES (NULL, ?)', (LIMIT, ))
