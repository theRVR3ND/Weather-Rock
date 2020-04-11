##
# Weather prediction app using machine learning
# by Kelvin Peng - April 2020
#
# using National Weather Service API
# https://www.weather.gov/documentation/services-web-api#/
# && NEXRAD (from NOAA) API
# https://github.com/aarande/nexradaws/
##

import os
import collections
import numpy as np
from pathlib import Path
from datetime import datetime
from datetime import timedelta

import tensorflow as tf

import urllib.request
import json
import matplotlib.pyplot as plt

import nexradaws

import datahandle

parameters = ["temperature", "dewpoint", "windDirection", "windSpeed", "windGust", "barometricPressure", "seaLevelPressure", "visibility", "relativeHumidity"]

# preidct parameters
def predictValues(data):
    print("lalala")

def plotStations():
    # plot location of stations
    fig = plt.figure()
    a1 = fig.add_subplot(1, 1, 1)
    
    coords = [[] for _ in range(2)]

    with open("data/stationsInfo.json") as f:
        j = json.loads(f.read())
        for _ in j:
            coord = j[_]["coord"]
            coords[0].append(coord[0])
            coords[1].append(coord[1])
    
    a1.plot(coords[0], coords[1], ".", color="black")
    plt.show()

if __name__ == "__main__":
    #print("running")
    #print(datahandle.pullData(datahandle.listStations()[:10], parameters))
    stations = datahandle.listStations()[:100]
    print("1")
    #dataJSON = datahandle.pullData(stations, parameters)
    dataJSON = datahandle.loadData(stations, parameters)
    print("2")
    trainX, trainY = datahandle.formData(stations, parameters, 3, 7, dataJSON)
    print(str(trainX.shape) + " " + str(trainY.shape))
    print("3")
    testX, testY = datahandle.formData(stations, parameters, 1, 3, dataJSON)
    print(str(testX.shape) + " " + str(testY.shape))
    print("4")

    model = tf.keras.models.Sequential([
        tf.keras.layers.Embedding(input_dim=len(stations), output_dim=len(stations)),
        tf.keras.layers.LSTM(128),
        tf.keras.layers.Dense(10)
    ])
    
    model.compile(optimizer='adam',
        loss='MeanSquaredError',
        metrics=['MeanAbsoluteError'])

    model.fit(trainX, trainY, epochs=5)
    model.evaluate(testX, testY)

    #print("done")
    #predictPressure()