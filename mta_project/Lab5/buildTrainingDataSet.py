'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 5
'''
## This program is used to clean out the data from the csv that you collected.
## It aims at removing duplicate entries and extracting any further insights 
## that the author(s) of the code may see fit

## Usage (for file as is currently): python buildTrainingDataSet.py <filename of file from part 1>

import sys

# Pandas is a python library used for data analysis
import pandas
from pandas import read_csv
from pytz import timezone
from datetime import datetime

TIMEZONE = timezone('America/New_York')


def main(fileHandle):
    # This creates a dataframe
    rawData = read_csv(fileHandle)

    # Remove duplicates
    data = rawData.drop_duplicates()

    # Take only the latest of multiple trips
    data = data.groupby('tripId').apply(lambda x: x.loc[x.timestamp.idxmax()])

    data = data[(data.direction == 'S')
                & (data.timeToReachExpressStation.notnull())
                & (data.timeToReachDestination.notnull())]

    localTrains = data[data.routeId == 1]
    expressTrains = data[(data.routeId == 2) | (data.routeId == 3)]

    # Target Data column, label with the "correct" decision
    switch = []

    for index, local in localTrains.iterrows():
        possibleExpressTrains = expressTrains[
            # 2/3 arrives to 96th street after this 1 train
            (expressTrains.timeToReachExpressStation >= local.timeToReachExpressStation)
            # and this 2/3 train gets to 42nd street first
            & (expressTrains.timeToReachDestination < local.timeToReachDestination)
        ]

        # There is at least one express train arriving that will get to 42nd faster
        if len(possibleExpressTrains) > 0:
            switch.append(1)
        else:
            switch.append(0)

    # Add the "switch" label as a new column to the data set
    s = pandas.DataFrame({"switch" : switch})
    trainingData = pandas.concat([localTrains.reset_index(drop=True), s], axis=1)
    trainingData.to_csv("trainingData_small.csv", index=False)

    localTrains.to_csv("clean_data_small.csv", index=False)

if __name__ == "__main__":

    lengthArg = len(sys.argv)

    if lengthArg < 2:
        print "Missing arguments"
        sys.exit(-1)

    if lengthArg > 2:
        print "Extra arguments"
        sys.exit(-1)

    fileHandle = sys.argv[1]
    main(fileHandle)
