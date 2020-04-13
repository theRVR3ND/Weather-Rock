import os
import numpy as np
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import urllib.request

import json

def _write_to_file(fileName, contents):
    with open(fileName, "w") as file:
        for i in range(len(contents)):
            if(i == len(contents) - 1):
                file.write(contents[i])
            else:
                file.write(contents[i] + "\n")

# load station's location info into json file
def stations_info(stations):
    data = {}

    for s in stations:
        j = _query_api("https://api.weather.gov/stations/%s" % s)
        data[s] = j["geometry"]["coordinates"]
    
    with open('data/stationsInfo.json', 'w') as f:
        json.dump(data, f)
    
    return data

# scrape for list of stations
def list_stations(live_list=False):
    # retrieve live station list, not previously saved file
    if live_list:
        # get station list with api
        query = "https://api.weather.gov/stations"
        with urllib.request.urlopen(query) as url:
            fetch = json.loads(url.read().decode())
            stations = fetch["observationStations"]
            return stations

    else:
        # get previously saved station list
        with open("data/stationsList.txt", "r") as file:
            return file.read().split("\n")

# query weather service api
def _query_api(query):
    with urllib.request.urlopen(query) as url:
        return json.loads(url.read().decode())

# pull data from station
def _query_station(station, limit):
    return _query_api("https://api.weather.gov/stations/%s/observations?station=%s&limit=%d" % (station, station, limit))

# parse time from NWS format
def _parse_time(string):
    return datetime.strptime(string, '%Y-%m-%dT%H:%M:%S+00:00')

def _compose_time(time):
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

# arg: time is datetime object
def _round_time(time):
    if time.minute < 30:
        return time.replace(minute=0)
    else:
        time += timedelta(hours=1)
        return time.replace(minute=0)

# calculate time-extrapolated data (for the nearest hour)
# args: tuple (value, datetime)
def _extrapolate_data(prev, curr):
    if prev[0] == None or curr[0] == None or prev[1] == curr[1]:
        return curr
    
    dY = curr[0] - prev[0]
    dt = (curr[1] - prev[1]).seconds // 60
    targTime = _round_time(curr[1]) # round curr time to nearest hour
    dm = (targTime - prev[1]).seconds // 60
    
    return (prev[0] + (dm * dY) / dt, targTime)

# retrieve data from stations (either saved or query)
# json heirarchy:
# station -> time -> parameters (values)
def pull_data(stations, parameters, limit):
    # check if data exists
    filepath = Path("data", "observations.json")
    j = None
    if filepath.is_file():
        with open(filepath) as f:
            j = json.loads(f.read())
    else:
        j = {}
    
    modded = False # json modification flag
    for s in range(len(stations)):
        try:
            station = stations[s]        
            
            if not station in j:
                j[station] = {}

            obs = _query_station(station, limit) # observation data

            modded = False
            for i in range(len(obs["features"])):
                o = obs["features"][i]
                obs_time = o["id"].split("/")[-1] # observation timestamp
                if not obs_time in j[station]:
                    modded = True

                    # extrapolate data to nearest hour (for ease in formatting data later)
                    if len(j[station]) > 1:
                        obs_time = _compose_time(_round_time(_parse_time(obs_time)))
                        j[station][obs_time] = {}
                        for p in parameters:
                            value = o["properties"][p]["value"]
                            extrap = _extrapolate_data(
                                (
                                    obs["features"][i - 1]["properties"][p]["value"],
                                    _parse_time(obs["features"][i - 1]["id"].split("/")[-1])
                                ),
                                (value, _parse_time(obs_time))
                            )
                            j[station][obs_time][p] = extrap[0]
                    
                    # no extrapolation of data
                    else:
                        j[station][obs_time] = {}
                        for p in parameters:
                            value = o["properties"][p]["value"]
                            j[station][obs_time][p] = value
            
            if True:
                if 20 * s // len(stations) > 20 * (s - 1) // len(stations):
                    print("[%s>%s]" % ("=" * (1 + 20 * s // (len(stations) - 1)), "-" * (19 - 20 * s // (len(stations) - 1))))
            else:
                print(station)

        except:
            print("err")
            continue
    
    if modded:
        #modded = False
        with open(filepath, 'w') as f:
            json.dump(j, f) # update json
            f.flush()
            f.close()
    
    #print("pull_data end")
    return j

def load_data():
    filepath = Path("data", "observations.json")
    if filepath.is_file():
        with open(filepath) as f:
            return json.loads(f.read())

# normalize values in data (using same shaped array as form_data())
def _normalize(series): # series shape = (b atch, t ime, p aram)
    max = series.max(axis=1) # max of each parameter along time axis        shape = (b, p)
    min = series.min(axis=1) # min of each parameter along time axis        shape = (b, p)
    
    series = np.swapaxes(series, 1, 0) # shape = (t, b, p)

    # normalize: y = (x - min) / (max - min)
    ret = np.array([_ - min for _ in series])
    ret = np.array([_ / (max-min) for _ in series])
    # ret's shape = (t, b, p)

    return np.swapaxes(ret, 0, 1) # return ret w/ axes swapped so shape = (b, t, p)

# format data for tf input
# input shape is [batch, timesteps, feature] (from: https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM)
# output shape:
#   x = (batches, timesteps, values)
#   y = (batches, values)
def form_data(stations, parameters, batches, timesteps, json_obj):
    x = np.zeros((batches, timesteps, len(stations) * len(parameters)))
    y = np.zeros((batches, len(stations) * len(parameters)))

    now = datetime.now()

    for i in range(batches):
        t = datetime(year=now.year, month=now.month, day=now.day) - timedelta(hours=batches-i+timesteps+1)
        for j in range(timesteps):
            for m in range(len(stations)):
                for n in range(len(parameters)):
                    value = None
                    if _compose_time(t) in json_obj[stations[m]]:
                        value = json_obj[stations[m]][_compose_time(t)][parameters[n]]
                    else:
                        value = 0
                    
                    x[i][j][m * len(parameters) + n] = value if not value == None else 0
                    
                    if j == timesteps - 1:
                        tNext = _compose_time(t + timedelta(hours=1))
                        if tNext in json_obj[stations[m]]:
                            value = json_obj[stations[m]][tNext][parameters[n]]
                        else:
                            value = 0
                        y[i][m * len(parameters) + n] = value if not value == None else 0
            
            t += timedelta(hours=1)

    return _normalize(x), _normalize(y)

if __name__ == "__main__":
    print("running datahandle.py")
    parameters = ["temperature", "dewpoint", "windDirection", "windSpeed", "windGust", "barometricPressure", "seaLevelPressure", "visibility", "relativeHumidity"]
    pull_data(list_stations(), parameters, 24 * 2) # pull data for last 24 * 2 hours