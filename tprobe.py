#!/usr/bin/env python

from flask import Flask, make_response, request
from itty import get, post, run_itty, Response, NotFound
import os, json, pytz, time, argparse, functools
from contextlib import closing
from datetime import datetime
import config # program variable config file. Should be located in the same directory as us

app = Flask(__name__)

def jsonify(origfunc):
    @functools.wraps(origfunc)
    def wrapper(*args, **kwds):
        result = origfunc(*args, **kwds)
        text = json.dumps(result, indent=4)
        return Response(text, content_type='text/json', status=200)
    return wrapper

class tempProbe(object):
    def __init__(self, probeID, name):
        self.name = name
        self.rawTemp = ''
        self.curTemp = ''
        self.ID = probeID
        self.URI = '/sys/bus/w1/devices/%s/w1_slave' % self.ID
        self.measurementTime = ''

    def readTemp(self):
        with open(self.URI,'rb') as file:
            text = file.read()
            self.measurementTime = datetime.now()
            ''' The text output from the probe looks like this:
            4a 01 4b 46 7f ff 06 10 f7 : crc=f7 YES
            4a 01 4b 46 7f ff 06 10 f7 t=20625
            '''
            lines = text.split('\n')
            # Read the last word of the first line to see if the CRC check passed
            if lines[0].split()[-1] == 'YES':
                # Read the numbers after the '=' sign on the second line
                self.rawTemp = float(lines[1].split('=')[-1])
                # Convert to Fahrenheit
                self.curTemp = ((self.rawTemp / 1000.0) * 1.8) + 32.0
                return True
            else:
                self.curTemp = ''
                return False

    def __str__(self):
        return '%s: %.1f' % (self.name, self.curTemp)


    # Build a list of probe objects from the config file
@get("/get")
@jsonify
def getTemps(request):
    probeList = []
    for probe in config.PROBE_LIST:
        # print probe
        probeList.append(tempProbe(probe[0],probe[1]))

    # Go through the probe list, take a measurement, and store it in the dict
    currentReadings = {}
    for probe in probeList:
        if probe.readTemp():
            # print '%s: %s: %.1f' % (probe.measurementTime.strftime(config.TIME_FMT), probe.name, probe.curTemp)
            currentReadings[probe.name] = '%.1f' % probe.curTemp

    return currentReadings

@get("/welcome")
@jsonify
def howdy(request):
    return 'Hello!'


if __name__ == '__main__':
    app.run()

# run_itty(host='', port=8080)