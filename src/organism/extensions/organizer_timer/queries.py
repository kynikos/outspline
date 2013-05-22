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

alarmsproperties_create = ('CREATE TABLE AlarmsProperties '
                           '(AP_id INTEGER PRIMARY KEY, '
                            'AP_last_search INTEGER)')

alarmsproperties_insert = ('INSERT INTO AlarmsProperties (AP_id, '
                           'AP_last_search) VALUES (NULL, ?)')

alarmsproperties_select_search = ('SELECT AP_last_search '
                                  'FROM AlarmsProperties LIMIT 1')

alarmsproperties_update = 'UPDATE AlarmsProperties SET AP_last_search=?'
