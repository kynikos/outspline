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

import development


def print_memory_table(table):
    return development.print_memory_table(table)


def print_table(filename, table):
    return development.print_table(filename, table)


def print_all_memory_tables():
    return development.print_memory_db()


def print_all_tables(filename):
    return development.print_db(filename)


def print_all_databases():
    return development.print_all_db()


def populate_tree(treedb):
    return development.populate_tree(treedb)


def bind_to_populate_tree(handler, bind=True):
    return development.populate_tree_event.bind(handler, bind)
