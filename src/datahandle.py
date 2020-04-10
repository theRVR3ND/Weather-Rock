import os
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import urllib.request

import json

def writeToFile(fileName, contents):
    with open(fileName, "w") as file:
        for i in range(len(contents)):
            if(i == len(contents) - 1):
                file.write(contents[i])
            else:
                file.write(contents[i] + "\n")

# load station's location info into json file
# format:
# stations (index){
#   id ("KXXX")
#   coord [xxx.xx, xxx.xx]
# }
def writeStationsInfo(stations):
    data = {}

    for i in range(len(stations)):
        info = stationsInfo(stations[i])
        lat = float(info["geometry"]["coordinates"][0])
        lon = float(info["geometry"]["coordinates"][1])

        data[i] = {}
        data[i]["id"] = stations[i]
        data[i]["coord"] = [lat, lon]
    
    with open('data/stationsInfo.json', 'w') as f:
        json.dump(data, f)

# scrape for list of stations
def listStations():
    # get previously saved station list
    with open("data/stationsList.txt", "r") as file:
        return file.read().split("\n")
    
    # get station list with api
    #query = "https://api.weather.gov/stations"
    #with urllib.request.urlopen(query) as url:
    #    fetch = json.loads(url.read().decode())
    #    stations = fetch["observationStations"]
    #    return stations

# query weather service api
def query(query):
    with urllib.request.urlopen(query) as url:
        return json.loads(url.read().decode())

def stationsInfo(station):
    return query("https://api.weather.gov/stations/%s" % station)

# pull data from station
def queryStation(station):
    return query("https://api.weather.gov/stations/%s/observations" % station)

# parse time from NWS format
def parseTime(string):
    return datetime.strptime(string, '%Y-%m-%dT%H:%M:%S+00:00')

# calculate time-extrapolated data (for the nearest hour)
# args: tuple (value, datetime)
def extrapolateData(prev, curr):
    if prev[0] == None or curr[0] == None or prev[1] == curr[1]:
        return curr
    
    dY = curr[0] - prev[0]
    dt = (curr[1] - prev[1]).seconds // 60
    targTime = curr[1] # round curr time to nearest hour
    if targTime.minute < 30:
        targTime = targTime.replace(minute=0)
    else:
        targTime += timedelta(hours=1)
        targTime = targTime.replace(minute=0)
    dm = (targTime - prev[1]).seconds // 60
    
    return (prev[0] + (dm * dY) / dt, targTime)

# retrieve data from station (either saved or query)
def pullData(station, parameters):
    print("pullData start")
    # check if data exists
    p = Path("data", "%s.json" % station)
    j = []
    if p.is_file():
        with open(p) as f:
            j = json.loads(f.read())
    
    now = datetime.utcnow()
    last_data = parseTime(j[-1]["time"]) if len(j) > 0 else datetime(1990, 1, 1)

    if now - last_data < timedelta(hours=1): # skip if data is current
        return j

    obs = queryStation(station) # observation data
    i = min(24, len(obs["features"])) # check last 24 hours of data (or however much is available)
    modded = False
    while (len(j) == 0 or now - last_data >= timedelta(hours=1)) and i > 0:
        i -= 1

        obvTime = parseTime(obs["features"][i]["id"].split("/")[-1]) # last observation time
        if last_data >= obvTime:
            continue

        modded = True
        dataTime = obvTime
        j.append({})
        for param in parameters:
            obvValue = obs["features"][i]["properties"][param]["value"]
            if len(j) > 1:
                extrapolated = extrapolateData(
                    (j[-2][param], parseTime(j[-2]["time"])),
                    (obvValue, obvTime))
                j[-1][param] = extrapolated[0]
                dataTime = extrapolated[1]
            else:
                j[-1][param] = obvValue
        j[-1]["time"] = dataTime.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        last_data = obvTime

    if modded:
        with open(p, 'w') as f:
            json.dump(j, f) # update json
            f.flush()
            f.close()
    
    print("pullData end")
    return j