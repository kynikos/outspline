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

import random
import os

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api
from outspline.coreaux_api import log
import outspline.interfaces.wxgui_api as wxgui_api
organism_api = coreaux_api.import_optional_extension_api('organism')
links_api = coreaux_api.import_optional_extension_api('links')
wxcopypaste_api = coreaux_api.import_optional_plugin_api('wxcopypaste')
wxscheduler_api = coreaux_api.import_optional_plugin_api('wxscheduler')
wxscheduler_basicrules_api = coreaux_api.import_optional_plugin_api(
                                                    'wxscheduler_basicrules')
wxalarms_api = coreaux_api.import_optional_plugin_api('wxalarms')
wxlinks_api = coreaux_api.import_optional_plugin_api('wxlinks')


def _select_database():
    dbn = core_api.get_databases_count()
    dbid = wxgui_api.get_selected_database_tab_index()
    if dbid > -1:
        choices = [dbid] * 3 + range(dbn)
        wxgui_api.select_database_tab_index(random.choice(choices))
        return True
    else:
        return False


def _select_items(many):
    filename = wxgui_api.get_selected_database_filename()
    ids = core_api.get_items_ids(filename)

    if ids:
        w = 0 if many else 1
        modes = (
            (40, 80)[w] * ['select_one'] +
            (10, 0)[w] * ['reselect_many'] +
            (10, 0)[w] * ['select_some'] +
            (10, 0)[w] * ['select_all'] +
            (20, 0)[w] * ['unselect_some'] +
            (10, 20)[w] * ['unselect_all']
        )
        mode = random.choice(modes)

        if mode == 'unselect_some':
            selection = wxgui_api.get_tree_selections(filename)
            if selection:
                sids = [wxgui_api.get_tree_item_id(filename, i) for i in
                                                                    selection]
                remids = random.sample(ids, random.randint(1, len(ids)))
                wxgui_api.simulate_remove_items_from_selection(filename,
                                                                        remids)
        else:
            if mode in ('select_one', 'reselect_many', 'unselect_all'):
                wxgui_api.simulate_unselect_all_items(filename)

            addids = {
                'select_one': (random.choice(ids), ),
                'reselect_many': random.sample(ids, random.randint(
                                        2 if len(ids) > 1 else 1, len(ids))),
                'select_some': random.sample(ids, random.randint(1, len(ids))),
                'select_all': ids,
                'unselect_all': (),
            }

            wxgui_api.simulate_add_items_to_selection(filename, addids[mode])

    return wxgui_api.get_tree_selections(filename)


def _select_editor():
    edids = wxgui_api.get_open_editors_tab_indexes()
    edid = wxgui_api.get_selected_editor_tab_index()
    if edid in edids:
        choices = [edid] * 3 + edids
        wxgui_api.select_editor_tab_index(random.choice(choices))
        return True
    else:
        return False


def create_database():
    testfilesd = coreaux_api.get_plugin_configuration('wxdevelopment')(
                                                                'TestFiles')
    testfiles = [os.path.expanduser(testfilesd[key]) for key in testfilesd]
    random.shuffle(testfiles)

    while testfiles:
        filename = testfiles.pop()
        if not core_api.is_database_open(filename):
            try:
                os.remove(filename)
            except OSError:
                # filename doesn't exist yet
                pass

            log.debug('Simulate create database')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_create_database(filename)
            break
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def open_database():
    testfilesd = coreaux_api.get_plugin_configuration('wxdevelopment')(
                                                                'TestFiles')
    testfiles = [os.path.expanduser(testfilesd[key]) for key in testfilesd]
    random.shuffle(testfiles)

    while testfiles:
        filename = testfiles.pop()
        if not core_api.is_database_open(filename) and \
                                                    os.path.isfile(filename):
            log.debug('Simulate open database')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_open_database(filename)
            break
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def save_database():
    if _select_database():
        if random.randint(0, 9) < 9:
            log.debug('Simulate save database')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_save_database()
        else:
            log.debug('Simulate save all databases')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_save_all_databases()
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def close_database():
    if _select_database():
        save = random.randint(0, 5)
        if random.randint(0, 9) < 9:
            log.debug('Simulate' + (' save and ' if save > 0 else ' ') +
                                                            'close database')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            if save > 0:
                wxgui_api.simulate_save_database()
            wxgui_api.simulate_close_database(no_confirm=True)
        else:
            log.debug('Simulate' + (' save and ' if save > 0 else ' ') +
                                                        'close all databases')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            if save > 0:
                wxgui_api.simulate_save_all_databases()
            wxgui_api.simulate_close_all_databases(no_confirm=True)
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def undo_database_history():
    if _select_database():
        log.debug('Simulate undo history')
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        wxgui_api.simulate_undo_tree(no_confirm=True)
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def redo_database_history():
    if _select_database():
        log.debug('Simulate redo history')
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        wxgui_api.simulate_redo_tree(no_confirm=True)
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def create_item():
    if _select_database():
        _select_items(False)

        if random.randint(0, 1) == 0:
            log.debug('Simulate create sibling item')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_create_sibling()
        else:
            log.debug('Simulate create child item')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_create_child()
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def cut_items():
    if wxcopypaste_api and _select_database():
        if _select_items(True):
            log.debug('Simulate cut items')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxcopypaste_api.simulate_cut_items(no_confirm=True)
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def copy_items():
    if wxcopypaste_api and _select_database():
        if _select_items(True):
            log.debug('Simulate copy items')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxcopypaste_api.simulate_copy_items()
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def paste_items():
    if wxcopypaste_api and _select_database():
        _select_items(False)

        if random.randint(0, 1) == 0:
            log.debug('Simulate paste items as siblings')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxcopypaste_api.simulate_paste_items_as_siblings(no_confirm=True)
        else:
            log.debug('Simulate paste items as children')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxcopypaste_api.simulate_paste_items_as_children(no_confirm=True)
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def move_item():
    if _select_database():
        if _select_items(False):
            c = random.randint(0, 2)
            if c == 0:
                log.debug('Simulate move item up')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxgui_api.simulate_move_item_up()
            elif c == 1:
                log.debug('Simulate move item down')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxgui_api.simulate_move_item_down()
            else:
                log.debug('Simulate move item to parent')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxgui_api.simulate_move_item_to_parent()
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def edit_item():
    if _select_database():
        if _select_items(False):
            log.debug('Simulate edit item')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_edit_item()
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def delete_items():
    if _select_database():
        if _select_items(True):
            log.debug('Simulate delete items')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_delete_items(no_confirm=True)
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def edit_editor_text():
    if _select_editor():
        text = ''
        words = ('the quick brown fox jumps over the lazy dog ' * 6).split()
        seps = ' ' * 6 + '\n'
        for x in xrange(random.randint(10, 100)):
            words.append(str(random.randint(0, 100)))
            text = ''.join((text, random.choice(words),
                            random.choice(seps)))
        text = ''.join((text, random.choice(words))).capitalize()

        log.debug('Simulate replace editor text')
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        wxgui_api.simulate_replace_editor_text(text)
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def edit_editor_rules():
    if organism_api and wxscheduler_api and wxscheduler_basicrules_api and \
                                                            _select_editor():
        filename, id_ = wxgui_api.get_selected_editor_identification()

        # It should also be checked if the database supports
        #  organism_basicrules (bug #330)
        if filename in organism_api.get_supported_open_databases():
            wxscheduler_api.simulate_expand_rules_panel(filename, id_)
            wxscheduler_api.simulate_remove_all_rules(filename, id_)

            rules = []

            for n in xrange(random.randint(0, 8)):
                r = random.randint(0, 16)

                if r == 0:
                    rule = \
                          wxscheduler_basicrules_api.create_random_occur_once_rule()
                elif r == 1:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_interval_rule()
                elif r == 2:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_day_rule()
                elif r == 3:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_week_rule()
                elif r == 4:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_selected_weekdays_rule()
                elif r == 5:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_selected_months_rule()
                elif r == 6:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_selected_months_inverse_rule()
                elif r == 7:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_selected_months_weekday_rule()
                elif r == 8:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_selected_months_weekday_inverse_rule()
                elif r == 9:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_month_rule()
                elif r == 10:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_month_inverse_rule()
                elif r == 11:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_month_weekday_rule()
                elif r == 12:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_month_weekday_inverse_rule()
                elif r == 13:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_every_synodic_month_rule()
                elif r == 14:
                    rule = \
                        wxscheduler_basicrules_api.create_random_occur_yearly_rule()
                elif r == 15:
                    rule = \
                         wxscheduler_basicrules_api.create_random_except_once_rule()
                else:
                    rule = \
                        wxscheduler_basicrules_api.create_random_except_every_interval_rule()

                rules.append(rule)

            log.debug('Simulate replace item rules')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()

            for rule in rules:
                if rule['rule'] in ('occur_once_local', 'occur_once_UTC'):
                    wxscheduler_basicrules_api.simulate_create_occur_once_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_regularly_local',
                                                        'occur_regularly_UTC'):
                    if rule['#'][6][0] == '1d':
                        wxscheduler_basicrules_api.simulate_create_occur_every_day_rule(
                                                        filename, id_, rule)
                    elif rule['#'][6][0] == '1w':
                        wxscheduler_basicrules_api.simulate_create_occur_every_week_rule(
                                                        filename, id_, rule)
                    elif rule['#'][6][0] == 'sy':
                        wxscheduler_basicrules_api.simulate_create_occur_every_synodic_month_rule(
                                                        filename, id_, rule)
                    else:
                        wxscheduler_basicrules_api.simulate_create_occur_every_interval_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_regularly_group_local',
                                                'occur_regularly_group_UTC'):
                    if rule['#'][6][0] == 'sw':
                        wxscheduler_basicrules_api.simulate_create_occur_selected_weekdays_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_monthly_number_direct_local',
                                            'occur_monthly_number_direct_UTC'):
                    if rule['#'][7][0] == '1m':
                        wxscheduler_basicrules_api.simulate_create_occur_every_month_rule(
                                                        filename, id_, rule)
                    else:
                        wxscheduler_basicrules_api.simulate_create_occur_selected_months_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_monthly_number_inverse_local',
                                        'occur_monthly_number_inverse_UTC'):
                    if rule['#'][7][0] == '1m':
                        wxscheduler_basicrules_api.simulate_create_occur_every_month_inverse_rule(
                                                        filename, id_, rule)
                    else:
                        wxscheduler_basicrules_api.simulate_create_occur_selected_months_inverse_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_monthly_weekday_direct_local',
                                        'occur_monthly_weekday_direct_UTC'):
                    if rule['#'][8][0] == '1m':
                        wxscheduler_basicrules_api.simulate_create_occur_every_month_weekday_rule(
                                                        filename, id_, rule)
                    else:
                        wxscheduler_basicrules_api.simulate_create_occur_selected_months_weekday_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_monthly_weekday_inverse_local',
                                        'occur_monthly_weekday_inverse_UTC'):
                    if rule['#'][8][0] == '1m':
                        wxscheduler_basicrules_api.simulate_create_occur_every_month_weekday_inverse_rule(
                                                        filename, id_, rule)
                    else:
                        wxscheduler_basicrules_api.simulate_create_occur_selected_months_weekday_inverse_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('occur_yearly_local',
                                                        'occur_yearly_UTC'):
                    wxscheduler_basicrules_api.simulate_create_occur_yearly_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('except_once_local', 'except_once_UTC'):
                    wxscheduler_basicrules_api.simulate_create_except_once_rule(
                                                        filename, id_, rule)
                elif rule['rule'] in ('except_regularly_local',
                                                    'except_regularly_UTC'):
                    wxscheduler_basicrules_api.simulate_create_except_every_interval_rule(
                                                        filename, id_, rule)
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def link_item_to_selection():
    if links_api and wxlinks_api and _select_editor():
        filename, id_ = wxgui_api.get_selected_editor_identification()
        _select_items(False)

        if filename in links_api.get_supported_open_databases():
            log.debug('Simulate link item to selection')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxlinks_api.simulate_link_to_selection(filename, id_)
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def apply_editor():
    if _select_editor():
        if random.randint(0, 9) < 9:
            log.debug('Simulate apply editor')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_apply_editor()
        else:
            log.debug('Simulate apply all editors')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            wxgui_api.simulate_apply_all_editors()
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def close_editor():
    if _select_editor():
        apply_ = random.randint(0, 5)
        if random.randint(0, 9) < 9:
            log.debug('Simulate' + (' apply and ' if apply_ > 0 else ' ') +
                                                                'close editor')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            if apply_ > 0:
                wxgui_api.simulate_apply_editor()
            wxgui_api.simulate_close_editor(ask='quiet')
        else:
            log.debug('Simulate' + (' apply and ' if apply_ > 0 else ' ') +
                                                        'close all editors')
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            if apply_ > 0:
                wxgui_api.simulate_apply_all_editors()
            wxgui_api.simulate_close_all_editors(ask='quiet')
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def snooze_alarms():
    if wxalarms_api:
        alarms = wxalarms_api.get_active_alarms()
        if alarms:
            unit = random.choice(('minutes', 'hours', 'days', 'weeks'))
            if unit == 'minutes':
                number = random.randint(1, 360)
            elif unit == 'hours':
                number = random.randint(1, 24)
            elif unit == 'days':
                number = random.randint(1, 3)
            elif unit == 'weeks':
                number = random.randint(1, 2)

            wxalarms_api.simulate_set_snooze_time(number, unit)

            if random.randint(0, 11) > 0:
                alarm = random.choice(alarms)
                log.debug('Simulate snooze alarm')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxalarms_api.simulate_snooze_alarm(alarm['filename'],
                                                            alarm['alarmid'])
            else:
                log.debug('Simulate snooze all alarms')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxalarms_api.simulate_snooze_all_alarms()
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False


def dismiss_alarms():
    if wxalarms_api:
        alarms = wxalarms_api.get_active_alarms()
        if alarms:
            if random.randint(0, 11) > 0:
                alarm = random.choice(alarms)
                log.debug('Simulate dismiss alarm')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxalarms_api.simulate_dismiss_alarm(alarm['filename'],
                                                            alarm['alarmid'])
            else:
                log.debug('Simulate dismiss all alarms')
                # Databases are blocked in simulator._do_action
                core_api.release_databases()
                wxalarms_api.simulate_dismiss_all_alarms()
        else:
            # Databases are blocked in simulator._do_action
            core_api.release_databases()
            return False
    else:
        # Databases are blocked in simulator._do_action
        core_api.release_databases()
        return False

ACTIONS = (
    1 * [create_database] +
    1 * [open_database] +
    1 * [save_database] +
    1 * [close_database] +
    4 * [undo_database_history] +
    4 * [redo_database_history] +
    18 * [create_item] +
    4 * [cut_items] +
    4 * [copy_items] +
    4 * [paste_items] +
    4 * [move_item] +
    12 * [edit_item] +
    4 * [delete_items] +
    6 * [edit_editor_text] +
    6 * [edit_editor_rules] +
    6 * [link_item_to_selection] +
    12 * [apply_editor] +
    8 * [close_editor] +
    8 * [snooze_alarms] +
    8 * [dismiss_alarms]
)
