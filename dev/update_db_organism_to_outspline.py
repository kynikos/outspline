#!/usr/bin/env python2

import sys
import sqlite3 as sqlite
import json
import time
import datetime

DATABASE = sys.argv[1]
QUERIES = (
    'UPDATE Properties SET P_max_history=60 WHERE P_id=1',
    'DROP TABLE CoMpatibility',
    'CREATE TABLE CoMpatibility (CM_id INTEGER PRIMARY KEY, '
                                'CM_type TEXT, '
                                'CM_addon TEXT, '
                                'CM_version INTEGER)',
    'INSERT INTO CoMpatibility (CM_id, CM_type, CM_addon, CM_version) '
                                             'VALUES (NULL, "Core", "core", 0)',
    'INSERT INTO CoMpatibility (CM_id, CM_type, CM_addon, CM_version) '
                                   'VALUES (NULL, "Extensions", "organism", 0)',
    'INSERT INTO CoMpatibility (CM_id, CM_type, CM_addon, CM_version) '
                             'VALUES (NULL, "Extensions", "organism_timer", 0)',
    'INSERT INTO CoMpatibility (CM_id, CM_type, CM_addon, CM_version) '
                        'VALUES (NULL, "Extensions", "organism_basicrules", 0)',
    'INSERT INTO CoMpatibility (CM_id, CM_type, CM_addon, CM_version) '
                            'VALUES (NULL, "Extensions", "organism_alarms", 0)',
    'DELETE FROM History',
    'CREATE TABLE TimerProperties (TP_id INTEGER PRIMARY KEY, '
                                                      'TP_last_search INTEGER)',
    'INSERT INTO TimerProperties (TP_id, TP_last_search) VALUES (NULL, ( '
                        'SELECT AP_last_search FROM AlarmsProperties LIMIT 1))',
    'DROP TABLE AlarmsProperties',
)


def string_to_rules(string):
    # Initialize rules in case string is False
    rules = []
    if string:
        rules = string.split('|')
        for i, v in enumerate(rules):
            strule = v.split(';')
            rules[i] = {}
            for sub in strule:
                spl = sub.split(':')
                # Get rid of the empty string coming from the final ; created
                # by rules_to_string()
                if spl[0]:
                    rules[i][spl[0]] = spl[1]

    # The last element is empty due to how the string is formatted by
    # rules_to_string()
    return rules[:-1]


def make_occur_once_rule(start, end, alarm, guiconfig):
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organism_api.update_item_rules
    if isinstance(start, int) and \
                   (end is None or (isinstance(end, int) and end > start)) and \
                                      (alarm is None or isinstance(alarm, int)):
        return {
            'rule': 'occur_once',
            '#': (
                start,
                end,
                alarm,
                guiconfig,
            )
        }
    else:
        raise Exception('Bad rule')


def make_except_once_rule(start, end, inclusive, guiconfig):
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organism_api.update_item_rules
    if isinstance(start, int) and isinstance(end, int) and end > start and \
                                                    isinstance(inclusive, bool):
        return {
            'rule': 'except_once',
            '#': (
                start,
                end,
                inclusive,
                guiconfig
            )
        }
    else:
        raise Exception('Bad rule')


def make_occur_every_day_rule(refstart, interval, rend, ralarm, guiconfig):
    # Make sure this rule can only produce occurrences compliant with the
    # requirements defined in organism_api.update_item_rules
    if isinstance(refstart, int) and refstart >= 0 and \
                                isinstance(interval, int) and interval > 0 and \
                    (rend is None or (isinstance(rend, int) and rend > 0)) and \
                                    (ralarm is None or isinstance(ralarm, int)):
        if ralarm is None:
            refmin = refstart
            refmax = refstart + max((rend, 0))
        else:
            refmin = refstart - max((ralarm, 0))
            refmax = refstart + max((rend, ralarm * -1, 0))

        refspan = refmax - refmin
        rstart = refstart - refmin

        return {
            'rule': 'occur_regularly_single',
            '#': (
                refmax,
                refspan,
                interval,
                rstart,
                rend,
                ralarm,
                guiconfig,
            )
        }
    else:
        raise Exception('Bad rule')

conn = sqlite.connect(DATABASE)
conn.row_factory = sqlite.Row
cur = conn.cursor()

for query in QUERIES:
    cur.execute(query)

cur.execute('SELECT * FROM Rules')
dbrules = cur.fetchall()

for dbrule in dbrules:
    id_ = dbrule['R_id']
    srules = dbrule['R_rules']
    rules = string_to_rules(srules)
    newrules = []

    for rule in rules:
        if rule['rule'] == 'occur_once':
            start = int(rule['start'])
            end = rule['end']
            ralarm = rule['ralarm']

            if end == 'None':
                end = None
            # end could have been already None (not a string)
            elif end != None:
                end = int(end)

            if ralarm == 'None':
                alarm = None
            elif ralarm == None:
                alarm = None
            elif ralarm != None:
                alarm = start - int(ralarm)

            endtype = 1 if end else 0
            alarmtype = 1 if alarm else 0

            newrules.append(make_occur_once_rule(start, end, alarm,
                                                          (endtype, alarmtype)))
        elif rule['rule'] == 'except_once':
            start = int(rule['start'])
            end = int(rule['end'])
            inclusive = rule['inclusive']

            if inclusive == 'True':
                inclusive = True
            elif inclusive == 'False':
                inclusive = False

            newrules.append(make_except_once_rule(start, end, inclusive, (1, )))
        elif rule['rule'] == 'occur_every_day':
            rstart = int(rule['rstart'])
            rendn = rule['rendn']
            rendu = rule['rendu']
            ralarm = rule['ralarm']

            if rendn == 'None':
                rendn = None
            # rendn could have been already None (not a string)
            elif rendn != None:
                rendn = int(rendn)

            if rendu == 'None':
                rendu = None

            if ralarm == 'None':
                ralarm = None
            # alarm could have been already None (not a string)
            elif ralarm != None:
                ralarm = int(ralarm)

            if rendn != None:
                mult = {'minutes': 60,
                        'hours': 3600,
                        'days': 86400,
                        'weeks': 604800,
                        'months': 2592000,
                        'years': 31536000}

                rend = rendn * mult[rendu]
            else:
                rend = None

            refstart = int(time.time()) // 86400 * 86400 + rstart + time.altzone

            endtype = 1 if rend is not None else 0
            alarmtype = 1 if ralarm is not None else 0

            newrules.append(make_occur_every_day_rule(refstart, 86400, rend,
                                            ralarm, ('1d', endtype, alarmtype)))
        else:
            raise Exception('Unexpected rule')

    newsrules = json.dumps(newrules, separators=(',',':'))
    cur.execute('UPDATE Rules SET R_rules=? WHERE R_id=?', (newsrules, id_))

conn.commit()
