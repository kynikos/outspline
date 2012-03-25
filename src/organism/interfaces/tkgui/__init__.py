# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

from constants import __author__, __status__, __version__, __date__
import rootwindow
import databases

# Vedere i moduli tix e scrolledtext!!! ******************************************
# Mettere le barre di scorrimento al tree, alla tasklist, all'area di ************
#   testo e alla finestra degli alarms


def main():
    databases.protection = databases.Protection()
    databases.memory = databases.MemoryDB()
    rootwindow.initialize()
    rootwindow.root.mainloop()

if __name__ == '__main__':
    main()
