#!/usr/bin/env python3
import datetime as dt
import requests

# set the Timeline API POST endpoint as the target URL
postTimelineURL = "https://api.tomorrow.io/v4/timelines"

# get your key from app.tomorrow.io/development/keys
apikey = "o7gop75AFgDkBb4avlJizGYC4YqZyHBz"

# pick the location, as a latlong pair
location = "39.5692011,-104.9452509"

# list the fields
fields = "temperature"

# choose the unit system, either metric or imperial
units = "imperial"

# set the timesteps, like "current", "1h" and "1d"
timesteps = "current"

units = "imperial"


# request the historical timelines with all the body parameters as options
requestURL = f'{postTimelineURL}?location={location}&fields={fields}&timesteps={timesteps}&units={units}&apikey={apikey}'
response = requests.get(requestURL)
data = response.json()
#print(data)
currentTemp = data["data"]["timelines"][0]["intervals"][0]["values"]["temperature"]
print(currentTemp)
