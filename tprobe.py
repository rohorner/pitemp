#!/usr/bin/env python

from requests import *
from pprint import pprint
import json
from datetime import datetime
import config # program variable config file. Should be located in the same directory as us

class tempProbe(object):
    def __init__(self, probeID, name):
        self.name = name
        self.rawTemp = ''
        self.curTemp = float()
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
                # Read the raw temperature reading after the '=' sign on the second line
                self.rawTemp = float(lines[1].split('=')[-1])
                # Convert to Fahrenheit
                self.curTemp = ((self.rawTemp / 1000.0) * 1.8) + 32.0
                return True
            else:
                self.curTemp = ''
                return False

    def __str__(self):
        return '%s: %.1f' % (self.name, self.curTemp)

    def __repr__(self):
        self.readTemp()
        return '%s(%s(%s): %.1f)' % (self.__class__.__name__, self.name, self.ID,  self.curTemp)


    # Build a list of probe objects from the config file

def getTemps():
    probeList = []
    for probe in config.PROBE_LIST:
        # print probe
        probeList.append(tempProbe(probe[0],probe[1]))

    ''' Go through the probe list, take a measurement, and store it in the dict
        Must be in the form:
        {
            "data": [
                {"basement",  63.9},
                {"attic",  85.2},
                {"outdoor",  23.5}
            ]
        }
    '''
    currentReadings = {'data':[]}
    for probe in probeList:
        result = {}
        if probe.readTemp():
            print '%s: %s: %.1f' % (probe.measurementTime.strftime(config.TIME_FMT), probe.name, probe.curTemp)
            result[probe.name] = '%.1f' % probe.curTemp
            currentReadings['data'].append(result)

    return json.dumps(currentReadings)
    #return json.dumps(currentReadings, indent=2)


if __name__ == '__main__':

    data = getTemps()
    pprint(data)
    #headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    #r = requests.post(url, data=json.dumps(data), headers=headers)

