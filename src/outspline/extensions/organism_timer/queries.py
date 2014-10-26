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

timerproperties_create = ('CREATE TABLE TimerProperties '
                          '(TP_id INTEGER PRIMARY KEY, '
                           'TP_last_search INTEGER)')

timerproperties_select_search = ('SELECT TP_last_search '
                                 'FROM TimerProperties LIMIT 1')

timerproperties_insert = ('INSERT INTO TimerProperties (TP_id, '
                          'TP_last_search) VALUES (NULL, ?)')

timerproperties_update = 'UPDATE TimerProperties SET TP_last_search=?'

timerproperties_drop = 'DROP TABLE TimerProperties'
