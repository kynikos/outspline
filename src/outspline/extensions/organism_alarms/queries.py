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

alarmsproperties_create = ('CREATE TABLE AlarmsProperties '
                          '(AP_id INTEGER PRIMARY KEY, '
                           'AP_log_limit INTEGER)')

alarmsproperties_select = 'SELECT * FROM AlarmsProperties'

alarmsproperties_select_history = ('SELECT AP_log_limit FROM AlarmsProperties '
                                    'WHERE AP_log_limit IS NOT NULL LIMIT 1')

alarmsproperties_insert_init = ('INSERT INTO AlarmsProperties '
                                    '(AP_id, AP_log_limit) VALUES (NULL, ?)')

alarmsproperties_insert_copy = ('INSERT INTO AlarmsProperties '
                                        '(AP_id, AP_log_limit) VALUES (?, ?)')

alarmsproperties_delete = 'DELETE FROM AlarmsProperties'

alarms_create = ("CREATE TABLE Alarms (A_id INTEGER PRIMARY KEY, "
                                      "A_item INTEGER, "
                                      "A_start INTEGER, "
                                      "A_end INTEGER, "
                                      "A_alarm INTEGER, "
                                      "A_snooze INTEGER)")

alarms_select = 'SELECT * FROM Alarms'

alarms_select_item = ('SELECT A_id, A_start, A_end, A_alarm, A_snooze '
                                                'FROM Alarms WHERE A_item=?')

alarms_select_count = ('SELECT COUNT(*) AS A_active_alarms FROM Alarms '
                                                    'WHERE A_snooze IS NULL')

alarms_insert = ('INSERT INTO Alarms (A_id, A_item, A_start, A_end, A_alarm, '
                                    'A_snooze) VALUES (NULL, ?, ?, ?, ?, ?)')

alarms_insert_copy = ('INSERT INTO Alarms (A_id, A_item, A_start, A_end, '
                                'A_alarm, A_snooze) VALUES (?, ?, ?, ?, ?, ?)')

alarms_update_id = 'UPDATE Alarms SET A_snooze=? WHERE A_id=?'

alarms_delete_id = 'DELETE FROM Alarms WHERE A_id=?'

alarms_delete_item = 'DELETE FROM Alarms WHERE A_item=?'

copyalarms_create = ("CREATE TABLE CopyAlarms (CA_id INTEGER, "
                                              "CA_item INTEGER, "
                                              "CA_start INTEGER, "
                                              "CA_end INTEGER, "
                                              "CA_alarm INTEGER, "
                                              "CA_snooze INTEGER)")

copyalarms_select = 'SELECT CA_id FROM CopyAlarms LIMIT 1'

copyalarms_select_id = ('SELECT CA_id, CA_start, CA_end, CA_alarm, CA_snooze '
                        'FROM CopyAlarms WHERE CA_item=?')

copyalarms_insert = ('INSERT INTO CopyAlarms (CA_id, CA_item, CA_start, '
                     'CA_end, CA_alarm, CA_snooze) VALUES (?, ?, ?, ?, ?, ?)')

copyalarms_delete = 'DELETE FROM CopyAlarms'

alarmsofflog_create = ("CREATE TABLE AlarmsOffLog ("
                                                "AOL_id INTEGER PRIMARY KEY, "
                                                "AOL_item INTEGER, "
                                                "AOL_tstamp INTEGER, "
                                                "AOL_reason INTEGER, "
                                                "AOL_text TEXT)")

alarmsofflog_select = 'SELECT * FROM AlarmsOffLog'

alarmsofflog_select_order = ('SELECT * FROM AlarmsOffLog '
                                                    'ORDER BY AOL_tstamp DESC')

alarmsofflog_insert = ('INSERT INTO AlarmsOffLog (AOL_id, AOL_item, '
                            'AOL_tstamp, AOL_reason, AOL_text) '
                            'VALUES (NULL, ?, strftime("%s", "now"), ?, ?)')

alarmsofflog_insert_copy = ('INSERT INTO AlarmsOffLog (AOL_id, AOL_item, '
                    'AOL_tstamp, AOL_reason, AOL_text) VALUES (?, ?, ?, ?, ?)')

# DELETE FROM AlarmsOffLog ORDER BY AOL_tstamp DESC LIMIT -1 OFFSET ?
alarmsofflog_delete_clean = ('DELETE FROM AlarmsOffLog '
                        'WHERE AOL_id NOT IN (SELECT AOL_id FROM AlarmsOffLog '
                        'ORDER BY AOL_tstamp DESC LIMIT ?)')
