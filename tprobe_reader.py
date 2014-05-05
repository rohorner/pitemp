__author__ = 'Rob Horner (robert@horners.org)'

"""
trpobe_reader.py:   A python app to query a raspberry pi temperature module and store the read values in
                    a persistent sqlite database.

Usage:  tprobe_reader <probe_ip_address>
TODO:   Current reads values from only one probe. Expand to read from a list of probe addresses
"""

import sqlite3
from pprint import pprint
import sys, os
from contextlib import closing
import json
import requests
import config
from datetime import datetime

TEMPERATURE_DB = 'temperatures.db'

def date_from_epoch(epoch):
    ''' Convert a unix epoch timestamp (1049958000) to human-readable format
        sqlite3 wants to see a timestamp as yyyy-MM-dd HH:mm:ss
    '''
    return datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')

def create_db(force=False):
    'Set-up a new characterized document database, eliminating an old one if it exists'
    if force:
        try:
            os.remove(TEMPERATURE_DB)
        except OSError:
            pass
    with closing(sqlite3.connect(TEMPERATURE_DB)) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE probes (id TEXT, name TEXT, lastread DATETIME)')
        c.execute('CREATE TABLE temperatures (id TEXT, timestamp DATETIME, temperature REAL)')
        c.execute('CREATE UNIQUE INDEX ProbeIndex ON probes (id)')
        for probe in config.PROBE_LIST:
            ''' Sample SQL command:
                insert into  probes ('id', 'name') values ('28-000004eb5222','probe_name');
            '''
            c.execute("INSERT INTO probes ('id', 'name') VALUES (?, ?)", (probe[0], probe[1]) )
        conn.commit()

def add_reading(id, timestamp, temperature):
    ''' Add a temperature reading to the history database '''
    with closing(sqlite3.connect(TEMPERATURE_DB)) as conn:
        c = conn.cursor()
        try:
            # Insert the current reading into the temperatures db
            c.execute('INSERT INTO temperatures VALUES (?, ?, ?)', (id, timestamp, temperature))
            # Update the probes table with the timestamp
            c.execute('UPDATE probes SET lastread = (?) WHERE id = (?)', (timestamp, id) )
        except sqlite3.IntegrityError:
            print 'sqlite3 raised IntegrityError'
        conn.commit()

def get_readings(probe_id=None, timespan=None):
    '''
    If the user didn't call us with a probe_id, then return all reading from all probes
    '''
    with closing(sqlite3.connect(TEMPERATURE_DB)) as conn:
        query_string = 'SELECT * FROM temperatures'
        if probe_id is not None:
            probe_filter = ' WHERE id = "'+probe_id + '"'
            query_string += probe_filter
        c = conn.cursor()
        try:
            results = c.execute(query_string).fetchall()
            return results
        except sqlite3.IntegrityError:
            print 'sqlite3 raised IntegrityError'

if __name__ == "__main__":

    #run_itty(host='', port=5000)


    if 0:
        create_db(force=True)

    if 1:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        headers = {
              'Accept': 'application/json',
              'content-type': 'application/json',
        }
        r = requests.get('http://rpi.horners.org:5000/get', headers=headers)
        print r.status_code
        result = r.json()
        resultList = [(id, timestamp, result[id]['curTemp']) for id in result]
        pprint(resultList)
        for reading in resultList:
            add_reading(reading[0], reading[1], reading[2])
