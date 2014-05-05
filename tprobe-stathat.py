#!/usr/bin/env python

import requests
import json
from datetime import datetime
import config # program variable config file. Should be located in the same directory as us
from stathat import StatHat
from time import sleep

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
        probeList.append(tempProbe(probe[0],probe[1]))

    currentReadings = []

    for probe in probeList:
        result = {}
        if probe.readTemp():
            result['stat'] = probe.name
            result['value'] = '%.1f' % probe.curTemp
            result['t'] = datetime.now()
            currentReadings.append(result)
        #print 'Probe: %s' % probe

    return currentReadings


if __name__ == '__main__':

    stats = StatHat(config.EZKEY)

    while True :
        measurements = getTemps()
        for probe in measurements:
            stats.value(probe['stat'], probe['value'])
        sleep(300)

