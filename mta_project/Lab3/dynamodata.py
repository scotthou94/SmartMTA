'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 3: dynamodata.py
'''

# *********************************************************************************************
# Program to update dynamodb with latest data from mta feed. It also cleans up stale entried from db
# Usage python dynamodata.py
# *********************************************************************************************
import json, time, sys
from collections import OrderedDict
from threading import Thread, Timer

import boto3
from boto3.dynamodb.conditions import Key,Attr

import datetime
import time

from botocore.exceptions import ClientError
import botocore.errorfactory

# Used to gracefully stop the threads
continueThreads = True

def getCurrentTime():
    """
    Returns the current date for printing purposes
    :return: datetime
    """
    return datetime.datetime.now().time()

def addNewData():
    """
    Reads parsed data from the MTA feed and batch writes them to DynamoDB.
    :param delay: How long to sleep in seconds on each iteration
    :param mtaUpdate: An instance of an mtaUpdates class object
    :return: None
    """
    # Create a thread that recursively calls this function every 30 seconds
    try:
        delay = 30.0
        if addNewData:
            # Recursively call the function again in 30 seconds
            # with a delayed thread call
            # Set as a daemon so it dies gracefully with the main thread
            t = Timer(delay, addNewData)
            t.setDaemon(True)
            t.start()
        else:
            return
    except TypeError as e:
        print "Thread for adding, finishing."
        return

    print getCurrentTime(), " Adding new data to Dynamo"
    insertData = parseData(mtaUpdate)
    with table.batch_writer(overwrite_by_pkeys=['tripId']) as batch:
        for dict in insertData:
            batch.put_item(Item=dict)

    print "Finished adding data"


def cleanOldData():
    """
    Removes data older than 2 minutes from DynamoDB, then sleeps
    :param delay: Number of seconds to sleep after each iteration
    :return: None
    """

    try:
        delay = 60.0
        if cleanOldData:
            # Recursively call the function again in 60 seconds
            # with a delayed thread call
            t = Timer(delay, cleanOldData)
            t.setDaemon(True)
            t.start()
        else:
            return
    except TypeError:
        print "Thread for deleting, finishing"
        return

    try:
        print getCurrentTime(), " Removing Old data from Dynamo"

        # Scan the table for anything older than 2 minutes
        expire = int(time.time()) - 120
        response = table.scan(
            FilterExpression=Attr('timestamp').lt(expire)
        )
        expireList = response['Items']

        # Delete any trip updates that matched the previous scan
        expire = int(time.time()) - 120
        for item in expireList:
            table.delete_item(
                Key={
                    'tripId': item['tripId']
                },
                ConditionExpression=Attr('timestamp').lt(expire)
            )

        print "Finished Cleaning old data!"
    except ClientError as e:
        # Ignore any errors as a result of no data being older than 2 minutes
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print e.response['Error']['Message']


def parseData(mtaUpdate):
    """
    Pulls all the data from the MTA feed message objects and converts them to a list of dictionaries for insertion.
    :param mtaUpdate: Instance of mtaUpdates class
    :return: List
    """
    tripupdates = mtaUpdate.getTripUpdates()
    print "# Trip Updates: ", len(tripupdates)
    data = []

    # Convert to an ordered dictionary and add to the list
    for t in tripupdates:
        data.append(mtaUpdate.getOrderedDictOfTripUpdate(t))
    return data

def createTableIfNotExists(dynamodb):
    """
    Creates the mtaData table if it doesn't exist already.
    :param dynamodb: DynamoDB client instance
    :return: None
    """
    try:
        table = dynamodb.create_table(
            TableName='mtaData',
            KeySchema=[
                {
                    'AttributeName': 'tripId',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'tripId',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='mtaData')
    except Exception as e:
        print e.message
        print "Table already exists, not creating again"

####################
#####   MAIN   #####
####################
sys.path.append('../utils')
import tripupdate, vehicle, alert, mtaUpdates, aws

with open('../key.txt', 'rb') as keyfile:
    APIKEY = keyfile.read().rstrip('\n')
    keyfile.close()

mtaUpdate = mtaUpdates.mtaUpdates(APIKEY)
dynamodb = aws.getResource('dynamodb', 'us-east-1')

createTableIfNotExists(dynamodb)
table = dynamodb.Table('mtaData')

addNewData()
cleanOldData()

try:
    while True:
        pass
except KeyboardInterrupt:
    # When the program has been killed, let the threads know to stop on their next iteration
    # This prevents killing the threads in the middle of an operation
    continueThreads = False
    print
    print "Exiting . . ."
    print "Please wait for threads to finish up"
    exit()
