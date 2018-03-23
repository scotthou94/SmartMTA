'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 5
'''
import time,csv,sys

import signal
from pytz import timezone
from datetime import datetime

sys.path.append('../utils')
import mtaUpdates
from S3 import S3

# This script should be run seperately before we start using the application
# Purpose of this script is to gather enough data to build a training model for Amazon machine learning
# Each time you run the script it gathers data from the feed and writes to a file
# You can specify how many iterations you want the code to run. Default is 50
# This program only collects data. Sometimes you get multiple entries for the same tripId. we can timestamp the 
# entry so that when we clean up data we use the latest entry

# Change DAY to the day given in the feed
DAY = datetime.today().strftime("%A")
TIMEZONE = timezone('America/New_York')

global ITERATIONS

#Default number of iterations
ITERATIONS = 100

STOP_ID_96TH = '120S'
STOP_ID_42ND = '127S'

#################################################################
####### Note you MAY add more datafields if you see fit #########
#################################################################

# column headers for the csv file
columns =['timestamp','tripId','route','day','timeToReachExpressStation','timeToReachDestination']


def getTimeToReachFutureStop(tu, stopId):
    # Check vehicle data first as per requirement
    if tu.vehicleData is not None:
        if tu.vehicleData.currentStopId == stopId:
            return tu.vehicleData.timestamp

    # Otherwise check the future stop data
    if stopId in tu.futureStops:
        return tu.futureStops[stopId][0]['arrivalTime']

    return None

def convertTimestampToMinutes(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    hours = int(dt.strftime('%H'))
    minutes = int(dt.strftime('%M'))
    newTime = (hours * 60) + minutes
    return newTime

def getCsvRow(tu, timestamp):
    """
    Return dictionary of tripUpdate data suitable for CSV storage.
    :param tu: a tripUpdate object
    :return: dictionary
    """
    d = []

    d.append(convertTimestampToMinutes(timestamp)) # timestamp from feed
    d.append(tu.tripId) # tripId
    # for convenience, everything before the first underscore
    d.append(tu.tripId.split('_')[0])

    d.append(tu.routeId) #routeId
    d.append(datetime.fromtimestamp(timestamp).strftime("%A")) # Day of the week

    # Extract the trip direction (N or S) from the tripId
    direction = tu.direction
    if tu.tripId:
        direction = tu.tripId[10]
    d.append(direction) # direction

    d.append(getTimeToReachFutureStop(tu, STOP_ID_96TH)) # time to reach 96th
    d.append(getTimeToReachFutureStop(tu, STOP_ID_42ND)) # time to reach 42nd

    print d
    return d

def parseData(mtaUpdate):
    """
    Pull the data from the MTA feed message objects and convert them to a list of dictionaries.
    :param mtaUpdate: Instance of mtaUpdates class
    :return: List
    """
    tripupdates = mtaUpdate.getTripUpdates()
    print "# Trip Updates: ", len(tripupdates)
    data = []

    # Convert to an ordered dictionary and add to the list
    for t in tripupdates:
        if t.routeId not in ['1', '2', '3']:
            continue
        data.append(getCsvRow(t, mtaUpdate.timestamp))
    return data

def appendToCsvFile(fileName, data):
    with open(fileName, 'ab') as f:
        writer = csv.writer(f)
        for d in data:
            writer.writerow(d)
    return

def pushToS3(fileName):
    print "Pushing to S3 . . . "
    s3Wrapper = S3(fileName)
    s3Wrapper.uploadData()

def main(fileName):
    # API key
    with open('../key.txt', 'rb') as keyfile:
        APIKEY = keyfile.read().rstrip('\n')
        keyfile.close()

    ### INSERT YOUR CODE HERE ###

    mtaUpdate = mtaUpdates.mtaUpdates(APIKEY)

    try:
        i = 0
        while i < 150:
            dataList = parseData(mtaUpdate)
            appendToCsvFile(fileName, dataList)
            print "CSV updated!"

            # Data is only published by the MTA every 30 seconds
            # No reason to hammer the server
            time.sleep(30)
            i = i + 1
    except KeyboardInterrupt:
        print "Exiting"
        exit()

    pushToS3(fileName)

if __name__ == "__main__":
    main('data_monday.csv')
