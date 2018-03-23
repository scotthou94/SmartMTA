'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 4: Part 2
'''

#**********************************************************************************************
# * Copyright (C) 2015-2016 Sareena Abdul Razak sta2378@columbia.edu
# * 
# * This file is part of New-York-MTA-Subway-Trip-Planner.
# * 
# * New-York-MTA-Subway-Trip-Planner can not be copied and/or distributed without the express
# * permission of Sareena Abdul Razak
# * Edited by Peter Wei pw2428@columbia.edu, February 19, 2018
# *********************************************************************************************
# Usage python mta.py

import json,time,csv,sys
from threading import Thread

import boto3
from boto3.dynamodb.conditions import Key, Attr

sys.path.append('../utils')
import aws


DYNAMODB_TABLE_NAME = "mtaData"

# prompt
def prompt():
    print ""
    print ">Available Commands are : "
    print "1. plan trip"
    print "2. subscribe to message feed"
    print "3. exit"  

def buildStationssDB():
    stations = []
    with open('stops.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            stations.append(row[0])
    return stations

def getDirectedStopId(stopId, direction):
    """
    Return a stopId suffixed with the given direction.
    :param stopId: The stopId (with or without direction)
    :param direction: Direction as either "N" or "S"
    :return: string stopId suffixed with direction if not already included
    """
    if "N" not in stopId and "S" not in stopId:
        return stopId + direction
    return stopId

def getIncomingTrainsToStation(table, direction, routeId, stopId):
    """
    Return list of trips heading toward the given station on a given route.
    :param table: DynamoDB table object
    :param direction: Direction either as "N" or "S" to filter by
    :param routeId: routeId to filter by
    :param stopId: station to stop at
    :return: list of trip records to the given station
    """
    if (type(routeId) is list) and (len(routeId) > 0):
        routeAttr = Attr('routeId').eq(routeId[0])
        for r in routeId:
            routeAttr = routeAttr | Attr('routeId').eq(r)
    else:
        routeAttr = Attr('routeId').eq(routeId)

    response = table.scan(
        FilterExpression=routeAttr & Attr('direction').eq(direction)
    )
    trips = response['Items']
    trains = []
    stopId = getDirectedStopId(stopId, direction)

    # Get trains that will be arriving at the given station
    for trip in trips:
        if stopId in trip['futureStopData']:
            trains.append(trip)
    return trains

def getEarliestTrain(trains, stopId, direction, timestamp=None):
    """
    Return the train that will arrive earliest at a given stop
    :param trains: List of trip records from the database
    :param stopId: Stop to arrive at in the future
    :param direction: Direction of the train
    :param timestamp: Optional timestamp to arrive after
    :return: One trip record for the train arrive next at the given station
    """
    stopId = getDirectedStopId(stopId, direction)
    earliestTrain = None
    for train in trains:
        if earliestTrain is None:
            # Set the initial earliest train
            if timestamp is None:
                earliestTrain = train
            elif train['futureStopData'][stopId][0]['arrivalTime'] >= timestamp:
                # If timestamp is provided, train must arrive after it.
                earliestTrain = train
        else:
            earliestArrival = earliestTrain['futureStopData'][stopId][0]['arrivalTime']
            currentArrival = train['futureStopData'][stopId][0]['arrivalTime']
            if timestamp is None:
                if currentArrival < earliestArrival:
                    earliestTrain = train
            else:
                if currentArrival >= timestamp and currentArrival < earliestArrival:
                    earliestTrain = train

    return earliestTrain

def getTimeToReachFutureStop(train, stopId, direction):
    """
    Return when a train will arrive at the given future stop
    :param train: trip record from the database
    :param stopId: The station ID to arrive at in the future
    :param direction:
    :return:
    """
    stopId = getDirectedStopId(stopId, direction)
    return train['futureStopData'][stopId][0]['arrivalTime']

def addSubscriber(sns, topicArn, phoneNumber):
    """
    Add the given phone number to the list of sms subscribers.
    :param sns: SNS Client
    :param topicArn: ARN of the notification Topic
    :param phoneNumber: Phone number to subscribe (1-123-555-9999 format)
    :return:
    """
    print "Subscribing . . . "
    protocolText = 'sms'
    subscribeResponse = sns.subscribe(
        TopicArn=topicArn,
        Protocol=protocolText,
        Endpoint=phoneNumber
    )

def sendNotification(sns, topicArn, message):
    """
    Send the given message to all subscribers of the given Topic ARN
    :param sns SNS Client object
    :param topicArn Topic ARN string
    :param message Message string to send (string)
    :return: None
    """
    response = sns.publish(
        TopicArn=topicArn,
        Message=message,
    )

def getDirectionOfStops(stations, sourceStopId, destinationStopId):
    """
    Return the direction to go from a source to a destination station
    :param stations: List of station IDs parsed from CSV
    :param sourceStopId: stopId of starting point
    :param destinationStopId: stopId of ending station
    :return: "S" if the destination is south, "N" if north or None if its the same station
    """
    sourceIndex = stations.index(sourceStopId)
    destinationIndex = stations.index(destinationStopId)
    if sourceIndex == destinationIndex:
        return None
    elif sourceIndex < destinationIndex:
        # Source station is higher up than destination
        # Must go south
        return 'S'
    else:
        # Source station is downtown from destination
        # Must go north
        return 'N'

def isValidSourceStation(sourceStopId):
    """
    Return whether or not the source station is north of 96th or is Times Sq.
    :param sourceStopId:
    :return:
    """
    try:
        # Starting in Times Sq
        if int (sourceStopId) == int (timesSquareStopId):
            return True

        # Starting north of 96th
        if int(sourceStopId) <= int(ninetySixthStopId) and int(sourceStopId) >= int(firstStopId):
            return True
    except ValueError:
        print "ERROR: Your station ID must be a number only (no direction suffix)"

    return False

def isValidDestinationStation(destinationStopId):
    """
    Return whether or not the destination is valid
    :param destinationStopId:
    :return:
    """
    # It just so happens to the same rules for source
    # but that may not always be the case
    return isValidSourceStation(destinationStopId)


# Global stop constants for important stations
ninetySixthStopId = '120'
timesSquareStopId = '127'
firstStopId = '101'

def main():
    dynamodb = aws.getResource('dynamodb','us-east-1')
    snsClient = aws.getClient('sns','us-east-1')
    snsResource = aws.getResource('sns','us-east-1')

    # Create topic if it doesn't already exist
    createResponse = snsClient.create_topic(Name='mtaSub')
    topicArn = createResponse['TopicArn']
    
    dynamoTable = dynamodb.Table(DYNAMODB_TABLE_NAME)

    # Get list of all stopIds
    stations = buildStationssDB()

    while True:
        prompt()
        sys.stdout.write(">select a command : ")
        userIn = sys.stdin.readline().strip()
        if len(userIn) < 1 :
            print "Command not recognized"
        else:
            if userIn == '1':
                sys.stdout.write(">Enter source : ")
                sourceStop = sys.stdin.readline().strip()
                if sourceStop not in stations:
                    sys.stdout.write(">Invalid stop id. Enter a valid stop id")
                    sys.stdout.flush()
                    continue

                if not isValidSourceStation(sourceStop):
                    sys.stdout.write('>You must start north of 96th street or at Times Sq.')
                    sys.stdout.flush()
                    continue

                sys.stdout.write(">Enter destination : ")
                destinationStop = sys.stdin.readline().strip()
                if destinationStop not in stations:
                    sys.stdout.write(">Invalid stop id. Enter a valid stop id")
                    sys.stdout.flush()
                    continue

                if not isValidDestinationStation(sourceStop):
                    sys.stdout.write('>You must end north of 96th street or at Times Sq.')
                    sys.stdout.flush()
                    continue

                if sourceStop == destinationStop:
                    sys.stdout.write('>You are already at the station!')
                    sys.stdout.flush()
                    continue

                sys.stdout.write(">Type N for uptown, S for downtown: ")
                direction = sys.stdin.readline().strip()

                # Validate direction
                if direction not in ['N', 'S']:
                    sys.stdout.write(">Invalid direction. Enter a valid direction")
                    sys.stdout.flush()
                    continue

                # You can figure out the direction from the source and destinations
                actualDirection = getDirectionOfStops(stations, sourceStop, destinationStop)
                if actualDirection != direction:
                    sys.stdout.write(">Wrong direction!")
                    sys.stdout.flush()
                    continue

                if sourceStop == timesSquareStopId:
                    sourceStop = getDirectedStopId(sourceStop, direction)
                    destinationStop = getDirectedStopId(destinationStop, direction)
                    # Find incoming local trains
                    incomingLocals = getIncomingTrainsToStation(dynamoTable, direction, '1', sourceStop)
                    print "Local trains incoming to ", sourceStop
                    for l in incomingLocals:
                        print l['tripId']
                    earliestLocal = getEarliestTrain(incomingLocals, sourceStop, direction)
                    print "The next local train coming is ", earliestLocal['tripId']
                    print "It arrives at ", earliestLocal['futureStopData'][sourceStop][0]['arrivalTime']

                    incomingExpresses = getIncomingTrainsToStation(dynamoTable, direction, ['2', '3'], sourceStop)
                    print "Express trains incoming to ", sourceStop
                    for e in incomingExpresses:
                        print e["tripId"]
                    earliestExpress = getEarliestTrain(incomingExpresses, sourceStop, direction)
                    print "The next express train coming is ", earliestExpress['tripId']
                    print "It arrives at ", earliestExpress['futureStopData'][sourceStop][0]['arrivalTime']

                    # Go directly on local
                    localArrivalTime = getTimeToReachFutureStop(earliestLocal, destinationStop, direction)
                    print "The local train will arrive at destination ", destinationStop, " at ", localArrivalTime

                    # Stop at 96th and get off the express
                    expressTo96thTime = getTimeToReachFutureStop(earliestExpress, ninetySixthStopId, direction)
                    # Next local arriving at 96th after that
                    incomingLocals = getIncomingTrainsToStation(dynamoTable, direction, '1', ninetySixthStopId)
                    earliestLocal = getEarliestTrain(incomingLocals, ninetySixthStopId, direction, expressTo96thTime)
                    expressAndLocalArrivalTime = getTimeToReachFutureStop(earliestLocal, destinationStop, direction)
                    print "If you take an express, you must switch at ", ninetySixthStopId
                    print "Express will be at your destination at ", expressAndLocalArrivalTime

                    if localArrivalTime < expressAndLocalArrivalTime:
                        print "Take the next local"
                        sendNotification(snsClient, topicArn, "Take Local")
                    else:
                        print "Take the express to 96th"
                        sendNotification(snsClient, topicArn, "Take Express")
                    continue

                sourceStop = getDirectedStopId(sourceStop, direction)
                destinationStop = getDirectedStopId(destinationStop, direction)
                ninetySixthStop = getDirectedStopId(ninetySixthStopId, direction)

                # The next train coming at your source station
                potentialTrains = getIncomingTrainsToStation(table=dynamoTable, direction=direction, routeId='1',
                                                             stopId=sourceStop)
                currentLocalTrain = getEarliestTrain(trains=potentialTrains, stopId=sourceStop, direction=direction)
                print "The next local train to ", sourceStop, " will arrive at ", \
                    currentLocalTrain['futureStopData'][sourceStop][0]['arrivalTime']

                # Time it gets to 96th street
                arrival96th = currentLocalTrain['futureStopData'][ninetySixthStop][0]['arrivalTime']
                print "It will arrive at 96th Street at ", arrival96th

                # Next local train when you arrive at 96th
                print "When you get to 96th street . . . "
                localsTo96th = getIncomingTrainsToStation(dynamoTable, direction, '1', ninetySixthStop)
                # Task 1: Print trip IDs
                for l in localsTo96th:
                    print l['tripId']
                local96th = getEarliestTrain(localsTo96th, ninetySixthStop, direction, arrival96th)
                # Task 3
                print "Earliest Local Train: ", local96th['tripId']
                print "It will arrive at ", local96th['futureStopData'][ninetySixthStop][0]['arrivalTime']

                # Next express train when you arrive at 96th
                expressesTo96th = getIncomingTrainsToStation(dynamoTable, direction, ['2', '3'], ninetySixthStop)
                # Task 2: Print express trip IDs
                for e in expressesTo96th:
                    print e['tripId']
                express96th = getEarliestTrain(expressesTo96th, ninetySixthStop, direction, arrival96th)
                print "Earliest Express Train: ", express96th['tripId']
                print "It will arrive at ", express96th['futureStopData'][ninetySixthStop][0][
                    'arrivalTime']

                # local time to get to 42nd
                timeToDestinationLocal = currentLocalTrain['futureStopData'][destinationStop][0]['arrivalTime']
                timeToDestinationExpress = express96th['futureStopData'][destinationStop][0]['arrivalTime']

                # Task 5
                print "Local will arrive at destination ", destinationStop, " at ", timeToDestinationLocal
                print "Express will arrive at destination ", destinationStop, " at ", timeToDestinationExpress

                # Task 6a
                if timeToDestinationLocal > timeToDestinationExpress:
                    print "Switch over to express"
                    sendNotification(snsClient, topicArn, "Switch to express @ 96th")
                else:
                    print "Stay with Local"
                    sendNotification(snsClient, topicArn, "Stay on local @ 96th")

            elif userIn == '2':
                sys.stdout.write(">Enter Phone No. ")
                phone_number = sys.stdin.readline().strip()
                # Task 9
                addSubscriber(snsClient, topicArn, phone_number)
            elif userIn == '3':
                print "Bye, Felicia . . ."
                exit(0)
            else:
                print "Unknown command. Terminating."
                sys.exit(6)


if __name__ == "__main__":
    main()
