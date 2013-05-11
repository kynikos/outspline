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

import random
import time

import organism.coreaux_api as coreaux_api
from organism.coreaux_api import Event
import organism.core_api as core_api
organizer_api = coreaux_api.import_extension_api('organizer')

populate_tree_event = Event()


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


def populate_tree(filename):
    group = core_api.get_next_history_group(filename)
    description = 'Populate tree'

    treeitems = []
    i = 0
    while i < 10:
        dbitems = core_api.get_items_ids(filename)

        try:
            itemid = random.choice(dbitems)
        except IndexError:
            # No items in the database yet
            itemid = 0

        mode = random.choice(('child', 'sibling'))

        if mode == 'sibling' and itemid == 0:
            continue

        i += 1

        text = ''
        words = ('the quick brown fox jumps over the lazy dog ' * 6
                 ).split()
        seps = ' ' * 6 + '\n'
        for x in range(random.randint(10, 100)):
            words.append(str(random.randint(0, 100)))
            text = ''.join((text, random.choice(words),
                            random.choice(seps)))
        text = ''.join((text, random.choice(words))).capitalize()

        if mode == 'child':
            id_ = core_api.append_item(filename, itemid, group, text=text,
                                       description=description)
        elif mode == 'sibling':
            id_ = core_api.insert_item_after(filename, itemid, group,
                                             text=text,
                                             description=description)

        if organizer_api:
            rules = []

            for n in range(random.randint(0, 8)):
                start = int((random.gauss(time.time(), 15000)) // 60 * 60)
                end = random.choice((None, start + random.randint(1, 360) * 60))
                ralarm = random.choice((None, 0))
                rstart = random.randint(0, 1440) * 60
                # Ignore 'days', 'weeks', 'months', 'years'
                rendu = random.choice(('minutes', 'hours'))
                if rendu == 'minutes':
                    rendn = random.randint(1, 360)
                elif rendu == 'hours':
                    rendn = random.randint(1, 24)
                inclusive = random.choice((True, False))

                rule = random.choice((
                    {'rule': 'occur_once',
                     'start': start,
                     'end': end,
                     'ralarm': ralarm},
                    {'rule': 'occur_every_day',
                     'rstart': rstart,
                     'rendn': rendn,
                     'rendu': rendu,
                     'ralarm': ralarm},
                    {'rule': 'except_once',
                     'start': start,
                     'end': end,
                     'inclusive': inclusive}
                ))

                rules.append(rule)

            organizer_api.update_item_rules(filename, id_, rules, group,
                                            description=description)

        treeitems.append({'mode': mode,
                          'filename': filename,
                          'baseid': itemid,
                          'id_': id_,
                          'text': text})

    populate_tree_event.signal(treeitems=treeitems)
