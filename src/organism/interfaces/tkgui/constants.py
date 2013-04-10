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

__author__ = "Dario Giovannetti <dev@dariogiovannetti.net>"
__status__ = "development"
__version__ = "1.0.0.a20110710"
__date__ = "2011-07-10"

_PROJECT_NAME = "Organism"
_FILE_EXT = "ogd"

_ROOT_GEOMETRY = '760x540'
_ROOT_MIN_SIZE = (600, 400)
_ALARMS_GEOMETRY = '400x128'
_ALARMS_MIN_SIZE = (400, 128)
_ALARMS_TITLE = _PROJECT_NAME + ' - Alarms'

_MINUTE_INCREMENT = 1   # Al momento c'e' un bug nello Spinbox per cui andando ***
                        # in su incrementa bene, ma andando indietro, una volta***
                        # arrivato allo 0, fa un passo indietro di 1 soltanto. ***
                        # Per esempio, se l'incremento e' 5 e sono a 0, se *******
                        # clicco in su va a 5, ma se da 0 clicco in giu' va a ****
                        # 59, non a 55 *******************************************
