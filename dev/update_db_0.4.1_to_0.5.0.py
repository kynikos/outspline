#!/usr/bin/env python2

import sys
import sqlite3 as sqlite
import json

UTCOFFSET = int(sys.argv[1])
DATABASE = sys.argv[2]
conn = sqlite.connect(DATABASE)
conn.row_factory = sqlite.Row
cur = conn.cursor()

cur.execute('DROP TABLE History')
cur.execute("CREATE TABLE History (H_id INTEGER PRIMARY KEY, "
                                    "H_group INTEGER, "
                                    "H_status INTEGER, "
                                    "H_item INTEGER, "
                                    "H_type TEXT, "
                                    "H_description TEXT, "
                                    "H_redo TEXT, "
                                    "H_undo TEXT)")

cur.execute('SELECT * FROM Alarms')
alarms = cur.fetchall()
cur.execute('DROP TABLE Alarms')
cur.execute("CREATE TABLE Alarms (A_id INTEGER PRIMARY KEY, "
                                  "A_item INTEGER, "
                                  "A_start INTEGER, "
                                  "A_end INTEGER, "
                                  "A_alarm INTEGER, "
                                  "A_snooze INTEGER)")
for alarm in alarms:
    cur.execute('INSERT INTO Alarms (A_id, A_item, A_start, A_end, A_alarm, '
                        'A_snooze) VALUES (?, ?, ?, ?, ?, ?)',
                        (alarm['A_id'], alarm['A_item'], alarm['A_start'],
                        alarm['A_end'], alarm['A_alarm'], alarm['A_snooze']))

cur.execute("CREATE TABLE AlarmsOffLog (AOL_id INTEGER PRIMARY KEY, "
                                        "AOL_item INTEGER, "
                                        "AOL_tstamp INTEGER, "
                                        "AOL_reason INTEGER, "
                                        "AOL_text TEXT)")

cur.execute('SELECT * FROM Rules')
dbrules = cur.fetchall()

for dbrule in dbrules:
    id_ = dbrule['R_id']
    rules = json.loads(dbrule['R_rules'])
    newrules = []

    for rule in rules:
        if rule['rule'] == 'occur_once':
            #{"#":[1397379600,1397383200,1397379600,[1,1]],"rule":"occur_once"}
            #{"#":[1397408400,1397412000,1397408400,[1,1]],"rule":"occur_once_local"}
            rule['rule'] = "occur_once_local"
            rule['#'][0] += UTCOFFSET

            if rule['#'][1] is not None:
                rule['#'][1] += UTCOFFSET

            if rule['#'][2] is not None:
                rule['#'][2] += UTCOFFSET

            newrules.append(rule)

        elif rule['rule'] == 'occur_regularly_single':
            #{"#":[1397383200,3600,86400,0,3600,0,[null,1,1]],"rule":"occur_regularly_single"}
            #{"#":[1397408400,86400,0,82800,3600,0,[null,1,1]],"rule":"occur_regularly_local"}
            #{"#":[1397383200,3600,86400,0,3600,0,["1d",1,1]],"rule":"occur_regularly_single"}
            #{"#":[1397408400,86400,0,82800,3600,0,["1d",1,1]],"rule":"occur_regularly_local"}
            #{"#":[1397383200,3600,604800,0,3600,0,["1w",1,1]],"rule":"occur_regularly_single"}
            #{"#":[1397408400,604800,0,601200,3600,0,["1w",1,1]],"rule":"occur_regularly_local"}
            #{"#":[1397383200,3600,2551443,0,3600,0,["sy",1,1]],"rule":"occur_regularly_single"}
            #{"#":[1397408400,2551443,0,2547843,3600,0,["sy",1,1]],"rule":"occur_regularly_local"}
            refmax = rule['#'][0]
            refspan = rule['#'][1]
            interval = rule['#'][2]
            rstart = rule['#'][3]
            rend = rule['#'][4]
            ralarm = rule['#'][5]
            guiconfig = rule['#'][6]

            refstart = refmax - refspan + rstart + UTCOFFSET

            if ralarm is None:
                rmax = max((rend, 0))
            else:
                rmax = max((rend, ralarm * -1, 0))

            overlaps = rmax // interval
            bgap = interval - rmax % interval

            newrules.append({
                'rule': "occur_regularly_local",
                '#': (
                    refstart,
                    interval,
                    overlaps,
                    bgap,
                    rend,
                    ralarm,
                    guiconfig,
            )})

        elif rule['rule'] == 'occur_regularly_group':
            # All days, 18:00 (local), end +1 hour, alarm =
            #{"#":[1397988000,604800,[0,86400,172800,259200,345600,432000,518400],3600,3600,0,["sw",1,1]],"rule":"occur_regularly_group"}
            #{"#":[[1397494800,1397581200,1397667600,1397754000,1397840400,1397926800,1398013200],604800,0,601200,3600,0,["sw",1,1]],"rule":"occur_regularly_group_local"}

            # Not Tuesday, 18:00 (local), end +1 hour, alarm -1 hour
            #{"#":[1397991600,604800,[0,86400,172800,259200,345600,518400],3600,3600,3600,["sw",1,1]],"rule":"occur_regularly_group"}
            #{"#":[[1397498400,1397671200,1397757600,1397844000,1397930400,1398016800],604800,0,601200,3600,3600,["sw",1,1]],"rule":"occur_regularly_group_local"}
            refmax = rule['#'][0]
            interval = rule['#'][1]
            irmaxs = rule['#'][2]
            rmax = rule['#'][3]
            rend = rule['#'][4]
            ralarm = rule['#'][5]
            guiconfig = rule['#'][6]

            mrstart = max(irmaxs)
            refstart = refmax - mrstart - rmax

            rstarts = []

            for irmax in irmaxs:
                rstarts.append(mrstart - irmax)

            refstarts = []

            for rstart in rstarts:
                refstarts.append(refstart + rstart + UTCOFFSET)

            refstarts.sort()

            if ralarm is None:
                rmax = max((rend, 0))
            else:
                rmax = max((rend, ralarm * -1, 0))

            overlaps = rmax // interval
            bgap = interval - rmax % interval

            newrules.append({
                'rule': "occur_regularly_group_local",
                '#': (
                    refstarts,
                    interval,
                    overlaps,
                    bgap,
                    rend,
                    ralarm,
                    guiconfig,
            )})

        elif rule['rule'] == 'occur_monthly_number_direct':
            #{"#":[3600,[1,2,3,4,5,6,7,8,9,10,11,12],1098000,3600,0,[null,1,1]],"rule":"occur_monthly_number_direct"}
            #{"#":[0,[1,2,3,4,5,6,7,8,9,10,11,12],13,17,0,3600,0,[null,1,1]],"rule":"occur_monthly_number_direct_local"}
            #{"#":[3600,[1,2,3,4,5,6,7,8,9,10,11,12],1098000,3600,0,["1m",1,1]],"rule":"occur_monthly_number_direct"}
            #{"#":[0,[1,2,3,4,5,6,7,8,9,10,11,12],13,17,0,3600,0,["1m",1,1]],"rule":"occur_monthly_number_direct_local"}
            rstart = rule['#'][2]
            rend = rule['#'][3]
            ralarm = rule['#'][4]

            rule['rule'] = "occur_monthly_number_direct_local"

            day, rem = divmod(rstart, 86400)
            hour, rem = divmod(rem, 3600)
            minute = rem // 60

            rule['#'][2:3] = (day + 1, hour, minute)

            diff = (27 - day) * 86400 - hour * 3600 - minute * 60
            diffs = max(diff, 0)

            if ralarm:
                srend = max(rend, ralarm * -1, 0)
            else:
                srend = max(rend, 0)

            rule['#'][0] = max(srend - diffs, 0)

            newrules.append(rule)

        elif rule['rule'] == 'occur_monthly_number_inverse':
            #{"#":[3600,[1,2,3,4,5,6,7,8,9,10,11,12],1494000,3600,0,[null,1,1]],"rule":"occur_monthly_number_inverse"}
            #{"#":[0,[1,2,3,4,5,6,7,8,9,10,11,12],18,17,0,3600,0,[null,1,1]],"rule":"occur_monthly_number_inverse_local"}
            #{"#":[3600,[1,2,3,4,5,6,7,8,9,10,11,12],1494000,3600,0,["1m",1,1]],"rule":"occur_monthly_number_inverse"}
            #{"#":[0,[1,2,3,4,5,6,7,8,9,10,11,12],18,17,0,3600,0,["1m",1,1]],"rule":"occur_monthly_number_inverse_local"}
            rstart = rule['#'][2]
            rend = rule['#'][3]
            ralarm = rule['#'][4]

            rule['rule'] = "occur_monthly_number_inverse_local"

            rday, rem = divmod(rule['#'][2], 86400)
            iday = rday + 1 if rem > 0 else rday
            rrem = (86400 - rem) % 86400
            hour, rem = divmod(rrem, 3600)
            minute = rem // 60

            rule['#'][2:3] = (iday, hour, minute)

            diff = (iday - 1) * 86400 - hour * 3600 - minute * 60
            diffs = max(diff, 0)

            if ralarm:
                srend = max(rend, ralarm * -1, 0)
            else:
                srend = max(rend, 0)

            rule['#'][0] = max(srend - diffs, 0)

            newrules.append(rule)

        elif rule['rule'] == 'occur_monthly_weekday_direct':
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,1,3600,61200,3600,0,[null,1,1]],"rule":"occur_monthly_weekday_direct"}
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,1,3600,17,0,3600,0,[null,1,1]],"rule":"occur_monthly_weekday_direct_local"}
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,1,3600,61200,3600,0,["1m",1,1]],"rule":"occur_monthly_weekday_direct"}
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,1,3600,17,0,3600,0,["1m",1,1]],"rule":"occur_monthly_weekday_direct_local"}
            rstart = rule['#'][4]
            rend = rule['#'][5]
            ralarm = rule['#'][6]

            rule['rule'] = "occur_monthly_weekday_direct_local"

            hour, rem = divmod(rstart, 3600)
            minute = rem // 60

            rule['#'][4:5] = (hour, minute)

            if ralarm:
                maxoverlap = max(rend, ralarm * -1, 0)
            else:
                maxoverlap = max(rend, 0)

            rule['#'][3] = maxoverlap

            newrules.append(rule)

        elif rule['rule'] == 'occur_monthly_weekday_inverse':
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,2,3600,61200,3600,0,[null,1,1]],"rule":"occur_monthly_weekday_inverse"}
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,2,3600,17,0,3600,0,[null,1,1]],"rule":"occur_monthly_weekday_inverse_local"}
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,2,3600,61200,3600,0,["1m",1,1]],"rule":"occur_monthly_weekday_inverse"}
            #{"#":[[1,2,3,4,5,6,7,8,9,10,11,12],6,2,3600,17,0,3600,0,["1m",1,1]],"rule":"occur_monthly_weekday_inverse_local"}
            rstart = rule['#'][4]
            rend = rule['#'][5]
            ralarm = rule['#'][6]

            rule['rule'] = "occur_monthly_weekday_inverse_local"

            hour, rem = divmod(rstart, 3600)
            minute = rem // 60

            rule['#'][4:5] = (hour, minute)

            if ralarm:
                maxoverlap = max(rend, ralarm * -1, 0)
            else:
                maxoverlap = max(rend, 0)

            rule['#'][3] = maxoverlap

            newrules.append(rule)

        elif rule['rule'] == 'occur_yearly_single':
            #{"#":[0,1,2014,4,13,61200,3600,0,[1,1]],"rule":"occur_yearly_single"}
            #{"#":[0,1,2014,4,13,17,0,3600,0,[1,1]],"rule":"occur_yearly_local"}
            rule['rule'] = "occur_yearly_local"
            hour, rem = divmod(rule['#'][5], 3600)
            minute = rem // 60
            rule['#'][5:6] = (hour, minute)
            newrules.append(rule)

        elif rule['rule'] == 'except_once':
            #{"#":[1397379600,1397383200,false,[0]],"rule":"except_once"}
            #{"#":[1397408400,1397412000,false,[0]],"rule":"except_once_local"}
            rule['rule'] = "except_once_local"
            rule['#'][0] += UTCOFFSET
            rule['#'][1] += UTCOFFSET
            newrules.append(rule)

        elif rule['rule'] == 'except_regularly_single':
            #{"#":[1397383200,3600,86400,3600,false,[0]],"rule":"except_regularly_single"}
            #{"#":[1397408400,86400,0,82800,3600,false,[0]],"rule":"except_regularly_local"}
            refmax = rule['#'][0]
            refspan = rule['#'][1]
            interval = rule['#'][2]
            rend = rule['#'][3]
            inclusive = rule['#'][4]
            guiconfig = rule['#'][5]

            refstart = refmax - refspan + UTCOFFSET
            overlaps = rend // interval
            bgap = interval - rend % interval

            newrules.append({
                'rule': "except_regularly_local",
                '#': (
                    refstart,
                    interval,
                    overlaps,
                    bgap,
                    rend,
                    inclusive,
                    guiconfig,
            )})
        else:
            raise Exception('Unexpected rule')

    newsrules = json.dumps(newrules, separators=(',',':'))
    cur.execute('UPDATE Rules SET R_rules=? WHERE R_id=?', (newsrules, id_))

conn.commit()
