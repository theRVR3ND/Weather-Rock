import os
import numpy as np
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
def queryStation(station, limit):
    return query("https://api.weather.gov/stations/%s/observations?station=%s&limit=%d" % (station, station, limit))

# parse time from NWS format
def parseTime(string):
    return datetime.strptime(string, '%Y-%m-%dT%H:%M:%S+00:00')

def composeTime(time):
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

# arg: time is datetime object
def roundTime(time):
    if time.minute < 30:
        return time.replace(minute=0)
    else:
        time += timedelta(hours=1)
        return time.replace(minute=0)

# calculate time-extrapolated data (for the nearest hour)
# args: tuple (value, datetime)
def extrapolateData(prev, curr):
    if prev[0] == None or curr[0] == None or prev[1] == curr[1]:
        return curr
    
    dY = curr[0] - prev[0]
    dt = (curr[1] - prev[1]).seconds // 60
    targTime = roundTime(curr[1]) # round curr time to nearest hour
    dm = (targTime - prev[1]).seconds // 60
    
    return (prev[0] + (dm * dY) / dt, targTime)

# retrieve data from stations (either saved or query)
# json heirarchy:
# station -> time -> parameters (values)
def pullData(stations, parameters):
    # check if data exists
    filepath = Path("data", "observations.json")
    j = {}
    if filepath.is_file():
        with open(filepath) as f:
            j = json.loads(f.read())

    modded = False # json modification flag
    for s in range(len(stations)):
        station = stations[s]        
        
        if not station in j:
            j[station] = {}

        limit = 24 # limit query to last 24 obervations (approx. last 24 hrs)
        obs = queryStation(station, limit) # observation data

        modded = False
        for i in range(len(obs["features"])):
            o = obs["features"][i]
            obsTime = o["id"].split("/")[-1] # observation timestamp
            if not obsTime in j[station]:
                modded = True

                # extrapolate data to nearest hour (for ease in formatting data later)
                if len(j[station]) > 1:
                    obsTime = composeTime(roundTime(parseTime(obsTime)))
                    j[station][obsTime] = {}
                    for p in parameters:
                        value = o["properties"][p]["value"]
                        extrap = extrapolateData(
                            (
                                obs["features"][i - 1]["properties"][p]["value"],
                                parseTime(obs["features"][i - 1]["id"].split("/")[-1])
                            ),
                            (value, parseTime(obsTime))
                        )
                        j[station][obsTime][p] = extrap[0]
                
                # no extrapolation of data
                else:
                    j[station][obsTime] = {}
                    for p in parameters:
                        j[station][obsTime][p] = o["properties"][p]["value"]
        
        if True:
            if 20 * s // len(stations) > 20 * (s - 1) // len(stations):
                print("[%s>%s]" % ("=" * (1 + 20 * s // (len(stations) - 1)), "-" * (19 - 20 * s // (len(stations) - 1))))
        else:
            print(station)

    if modded:
        #modded = False
        with open(filepath, 'w') as f:
            json.dump(j, f) # update json
            f.flush()
            f.close()
    
    #print("pullData end")
    return j

def loadData(stations, parameters):
    filepath = Path("data", "observations.json")
    if filepath.is_file():
        with open(filepath) as f:
            return json.loads(f.read())

# format data for tf input
# input shape is [batch, timesteps, feature] (from: https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM)
def formData(stations, parameters, batches, timesteps, jsonObj):
    data = np.zeros((batches, timesteps, len(stations) * len(parameters)))
    
    now = datetime.now()

    for i in range(batches):
        t = datetime(year=now.year, month=now.month, day=now.day) - timedelta(hours=-batches+timesteps+1)
        for j in range(timesteps):
            value = None
            for m in range(len(stations)):
                for n in range(len(parameters)):
                    if composeTime(t) in jsonObj[stations[m]]:
                        value = jsonObj[stations[m]][composeTime(t)][parameters[n]]
                    data[i][j][m * len(parameters) + n] = value
            t += timedelta(hours=1)
    
    return data, np.array([data[i][timesteps - 1::timesteps] for i in range(batches)])

if __name__ == "__main__":
    print("running datahandle.py")