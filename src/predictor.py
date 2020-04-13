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
    stations = datahandle.list_stations()[:100]
    parameters = ["temperature", "dewpoint", "windDirection", "windSpeed", "windGust", "barometricPressure", "seaLevelPressure", "visibility", "relativeHumidity"]  

    #dataJSON = datahandle.pull_data(stations, parameters, 24 * 2)
    dataJSON = datahandle.load_data()
    parameters = ["temperature"]

    BATCHES = 256
    TIMESTEPS = 24 * 4
    EPOCHS = 10
    EPOCHSTEPS = 10
    
    x, y = datahandle.form_data(stations, parameters, BATCHES, TIMESTEPS, dataJSON)
    #print("(%s, %s)" % (str(x.shape), str(y.shape)))
    trainX, testX, trainY, testY = x[:len(x)*2//3], x[len(x)*2//3:], y[:len(y)*2//3], y[len(y)*2//3:]
    #print("(%s, %s) (%s, %s)" % (str(trainX.shape), str(testX.shape), str(trainY.shape), str(testY.shape)))
    
    model = tf.keras.models.Sequential([
        tf.keras.layers.LSTM(16, input_shape=x.shape[1:]),
        tf.keras.layers.Dense(len(stations) * len(parameters))
    ])
    model.summary()
    
    model.compile(optimizer='adam', loss='mae')
    model.fit(trainX, trainY, epochs=EPOCHS, steps_per_epoch=EPOCHSTEPS)

    #model.summary()
    #model.evaluate(testX, testY)

    pred = model.predict(np.array([testX[-1]]))[0]
    
    #print("test")
    #print(testX)

    print(str(pred.shape))
    print("pred")
    print(pred)
    print("testY")
    print(testY[-1])
    #print(testY[-1].shape)
    #print(testY.shape)



    """
    print(x[ind, -50:, 0])
    print(y[ind][0])
    print(pred[0])
    """

    t = range(-50, 0)

    for _ in range(1):
        fig = plt.figure()
        ind = int(np.random.rand(1) * len(y))
        # plot actual and predicted values for a single station
        plt.plot(t, x[ind, -50:, 0], color="red")
        plt.plot(0, y[ind][0], ".",  color="orange")
        plt.plot(0, pred[0], "X",    color="green")
        plt.show()
