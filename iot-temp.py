#!/usr/bin/env python3

import time
import jwt
import paho.mqtt.client as mqtt
import json
from pprint import pprint
import datetime
import config # This program's config.py file. Must be located in the same directory


# Define some project-based variables to be used below. This should be the only
# block of variables that you need to edit in order to run this script

ssl_private_key_filepath = '/home/pi/demo_private.pem'
ssl_algorithm = 'RS256' # Either RS256 or ES256
root_cert_filepath = '/home/pi/roots.pem'
project_id = 'home-project-165818'
gcp_location = 'us-central1'
registry_id = 'tempsensors'
device_id = 'tprobe-001'

# end of user-variables

cur_time = datetime.datetime.utcnow()

def create_jwt():
  token = {
      'iat': cur_time,
      'exp': cur_time + datetime.timedelta(minutes=60),
      'aud': project_id
  }

  with open(ssl_private_key_filepath, 'r') as f:
    private_key = f.read()

  return jwt.encode(token, private_key, ssl_algorithm)

_CLIENT_ID = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(project_id, gcp_location, registry_id, device_id)
_MQTT_TOPIC = '/devices/{}/events'.format(device_id)

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
            self.measurementTime = datetime.datetime.now()
            ''' The text output from the probe looks like this:
                4a 01 4b 46 7f ff 06 10 f7 : crc=f7 YES
                4a 01 4b 46 7f ff 06 10 f7 t=20625
            '''
            lines = text.decode().split('\n')
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
        {
	"data": [
		"ts":  "2009-12-31 00:00:00+00",
		"measurements": [
			{
                	"name": "outdoor",
                	"temperatureF": 63.9
            		},
            		{
                	"name": "attic",
                	"temperatureF": 85.2
            		}
		]
	]
        }
    '''

    result = []
    entry = {}
    entry["ts"] = datetime.datetime.timestamp(datetime.datetime.now())
    entry["measurements"] = []
    for probe in probeList:
        if probe.readTemp():
            reading = {}
            reading["locationID"] = probe.name
            reading["temperatureF"] = float('%.1f' % probe.curTemp)
            entry["measurements"].append(reading)
    result.append(entry)

    # Return data as json
    pprint(result)
    return result


if __name__ == '__main__':

    tempdata = getTemps()
    #pprint(json.dumps(tempdata))

    client = mqtt.Client(client_id=_CLIENT_ID)
    # authorization is handled purely with JWT, no user/pass, so username can be whatever
    client.username_pw_set(
        username='unused',
        password=create_jwt())

    def error_str(rc):
        return '{}: {}'.format(rc, mqtt.error_string(rc))

    def on_connect(unusued_client, unused_userdata, unused_flags, rc):
        print('on_connect', error_str(rc))

    def on_publish(unused_client, unused_userdata, unused_mid):
        print('on_publish')

    client.on_connect = on_connect
    client.on_publish = on_publish

    client.tls_set(ca_certs=root_cert_filepath) # Replace this with 3rd party cert if that was used when creating registry
    client.connect('mqtt.googleapis.com', 8883)
    client.loop_start()


    client.publish(_MQTT_TOPIC, json.dumps(tempdata).encode("utf-8"), qos=1)


    time.sleep(1)

    client.loop_stop()
