from pathlib import Path
from datetime import datetime
from datetime import timedelta

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

# retrieve data from station (either saved or query)
def pullData(station, parameter):
    # check if data exists/is up to date
    p = Path("data", station, "%s.json" % parameter)
    j = []
    if p.is_file():
        with open(p) as f:
            j = json.loads(f.read())
    
    obs = queryStation(station)
    now = datetime.utcnow()
    last_data = parseTime(j[-1]["time"]) if len(j) > 0 else now
    i = len(obs["features"])
    while (len(j) == 0 or now - last_data >= timedelta(hours=1)) and i > 0:
        i = i - 1

        obvTime = parseTime(obs["features"][i]["id"].split("/")[-1])
        if last_data >= obvTime:
            continue

        j.append({})
        j[-1]["value"] = obs["features"][i]["properties"][parameter]["value"]
        j[-1]["time"] = obvTime.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        last_data = obvTime

    if i == 0:
        folder = Path("data", station)
        if not folder.exists():
            os.makedirs(folder)
        with open(p, 'w') as f:
            json.dump(j, f) # update json
            f.flush()
            f.close()
    
    return j