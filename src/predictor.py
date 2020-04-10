##
# Weather prediction app using machine learning
# by Kelvin Peng - April 2020
#
# using National Weather Service API
# https://www.weather.gov/documentation/services-web-api#/
# && NEXRAD (from NOAA) API
# https://github.com/aarande/nexradaws/
##

import collections
import numpy as np

import tensorflow as tf
#from tensorflow.keras import layers

import urllib.request
import json
import matplotlib.pyplot as plt

import nexradaws

def writeToFile(fileName, contents):
    with open(fileName, "w") as file:
        for i in range(len(contents)):
            if(i == len(contents) - 1):
                file.write(contents[i])
            else:
                file.write(contents[i] + "\n")

# scrape for list of stations
def listStations():
    # get previously saved station list
    with open("stationsList.txt", "r") as file:
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

def stationInfo(station):
    return query("https://api.weather.gov/stations/%s" % station)

# pull data from station
def pullData(station):
    return query("https://api.weather.gov/stations/%s/observations" % station)

# load station's location info into json file
# format:
# stations (index){
#   id ("KXXX")
#   coord [xxx.xx, xxx.xx]
# }
def jsonStationInfo(stations):
    data = {}

    for i in range(len(stations)):
        info = stationInfo(stations[i])
        lat = float(info["geometry"]["coordinates"][0])
        lon = float(info["geometry"]["coordinates"][1])

        data[i] = {}
        data[i]["id"] = stations[i]
        data[i]["coord"] = [lat, lon]
    
    with open('stationInfo.json', 'w') as f:
        json.dump(data, f)

if __name__ == "__main__":
    # plot location of stations
    fig = plt.figure()
    a1 = fig.add_subplot(1, 1, 1)
    
    coords = [[] for _ in range(2)]

    with open("stationInfo.json") as f:
        j = json.loads(f.read())
        for _ in j:
            coord = j[_]["coord"]
            #print("%s (%f, %f)" % (_, coord[0], coord[1]))
            coords[0].append(coord[0])
            coords[1].append(coord[1])
    
    a1.plot(coords[0], coords[1], ".", color="black")
    plt.show()

    #for _ in stations:
    #    data.append(pullData(_))
    
    # predict weather (???)
