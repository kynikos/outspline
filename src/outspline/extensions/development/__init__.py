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

import outspline.core_api as core_api


def print_memory_table(table):
    print('====== {} (:memory:) ======'.format(table))
    cur = core_api.select_memory_table(table)
    print('|'.join([field[0] for field in cur.description]))
    for i in cur:
        print(tuple(i))


def print_table(filename, table):
    print('====== {} ({}) ======'.format(table, filename))
    cur = core_api.select_table(filename, table)
    print('|'.join([field[0] for field in cur.description]))
    for i in cur:
        print(tuple(i))


def print_memory_db():
    for table in core_api.select_all_memory_table_names():
        print_memory_table(table[0])


def print_db(filename):
    print('Items in {}: {}'.format(filename, core_api.get_items_count(filename))
                                                                               )
    for table in core_api.select_all_table_names(filename):
        print_table(filename, table[0])


def print_all_db():
    print('Open databases: {}'.format(core_api.get_databases_count()))

    for filename in core_api.get_open_databases():
        print_db(filename)

    print_memory_db()
