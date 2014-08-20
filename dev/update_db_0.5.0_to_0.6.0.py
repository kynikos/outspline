#!/usr/bin/env python2

import sys
import sqlite3

DATABASE = sys.argv[1]
conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT * FROM CoMpatibility')
deps = cur.fetchall()
cur.execute('DROP TABLE CoMpatibility')
cur.execute('CREATE TABLE CoMpatibility (CM_id INTEGER PRIMARY KEY, '
                                          'CM_extension TEXT, '
                                          'CM_version INTEGER)')
for dep in deps:
    addon = dep['CM_addon']
    ext = None if addon == 'core' else addon
    cur.execute('INSERT INTO CoMpatibility (CM_id, CM_extension, CM_version) '
                            'VALUES (?, ?, ?)',
                            (dep['CM_id'], ext, dep['CM_version']))

conn.commit()
