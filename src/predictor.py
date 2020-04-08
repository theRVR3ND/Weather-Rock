##
# Weather prediction app using machine learning
# by Kelvin Peng - April 2020
#
# using National Weather Service API
# https://www.weather.gov/documentation/services-web-api#/
##

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

if __name__ == "__main__":
    # pull data of all stations
    stations = listStations()[1500:2000] # change later (when i have a more powerful machine :P)
    #data = [len(stations)]

    # plot location of stations
    fig = plt.figure()
    a1 = fig.add_subplot(1, 1, 1)
    for _ in stations:
        info = stationInfo(_)
        lat = float(info["geometry"]["coordinates"][0])
        lon = float(info["geometry"]["coordinates"][1])
        a1.plot(lat, lon, ".", color="black")
        #print("%f,%f" % (-lat, lon))
    plt.show()

    #for _ in stations:
    #    data.append(pullData(_))
    
    # predict weather (???)
