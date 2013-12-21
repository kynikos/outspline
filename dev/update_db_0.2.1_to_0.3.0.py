#!/usr/bin/env python2

import sys
import sqlite3 as sqlite
import json

DATABASE = sys.argv[1]

conn = sqlite.connect(DATABASE)
conn.row_factory = sqlite.Row
cur = conn.cursor()

cur.execute('SELECT * FROM Links')
dblinks = cur.fetchall()

for dblink in dblinks:
    id_ = dblink['L_id']
    target = dblink['L_target']

    cur.execute('SELECT I_text FROM Items WHERE I_id=? LIMIT 1', (id_, ))
    ltext = cur.fetchone()['I_text']

    cur.execute('SELECT I_text FROM Items WHERE I_id=? LIMIT 1', (target, ))
    ttext = cur.fetchone()['I_text']

    print('LINK TEXT', id_, ltext)
    print('TARGET TEXT', target, ttext)

    if ltext != ttext:
        raise Exception('Link text not synchronized: ', id_)

    cur.execute('SELECT R_rules FROM Rules WHERE R_id=? LIMIT 1', (id_, ))
    rules = json.loads(cur.fetchone()['R_rules'])

    print('LINK RULES', id_, rules)

    if rules != []:
        raise Exception('Link rules not empty: ', id_)

print('Successful')
