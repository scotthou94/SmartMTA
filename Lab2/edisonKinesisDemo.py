# Group: x007
# Murshed Jamil Ahmed (mja2196)
# Shijun Hou (sh3658)
# Jiahong He (jh3863)
# Robert Fea (rf2638)
# IoT Lab 2, part 3

import boto
import boto.dynamodb2
import boto.kinesis
import mraa
import time
import json

from time import gmtime, strftime
from math import log
import pyupm_i2clcd as lcd

from decimal import Decimal

# Constants for temperature calculation
B = 4275
R0 = 100000

switch_pin_number = 8

# LCD
myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)

# If True, send to DynamoDb, otherwise send to Kinesis
modeIsDynamo = False

# Reads from Temperature Sensor
def getTemperatureInFahrenheit():
    # read in ADC value from the sensor
    raw = tempSensor.read()

    # Calculate celsius temperature based on Grove 
    # sensor documentation.
    R = 1023.0/raw - 1.0
    R = R0 * R
    celsius = 1.0/(log(R/R0)/B+1/298.15)-273.15

    # Convert to fahrenheit temperature
    fahrenheit = celsius * 9.0/5.0 + 32
    return fahrenheit

def pressButton(args):
    global modeIsDynamo
    # Toggle the flag
    modeIsDynamo = not modeIsDynamo
    if modeIsDynamo:
        setLcdDisplay("DynamoDB")
    else:
        setLcdDisplay("Kinesis")

def setLcdDisplay(line):
    myLcd.clear()
    myLcd.setCursor(0,0)
    myLcd.write(line)

def sendTemperatureToDynamo(timeOfTemp, temp):
    cleanTemp = Decimal(str(round(temp, 1)))
    print "Sending ", cleanTemp, "at ", timeOfTemp, " to DynamoDB"
    try:
        record = {'time_of_temp': timeOfTemp, 'temp': cleanTemp}
        table_dynamo.put_item(record)
    except Exception as e:
        print e

def sendTemperatureToKinesis(timeOfTemp, temp):
    cleanTemp = str(round(temp, 1))
    print "Sending ", cleanTemp, "at ", timeOfTemp, " to Kinesis"
    try:
        record = {'time_of_temp': timeOfTemp, 'temp': cleanTemp}
        client_kinesis.put_record("lab2_part3_stream", json.dumps(record), "partitionkey")
    except Exception as e:
        print e

DYNAMO_TABLE_NAME = 'Lab2_Part3_table'
KINESIS_STREAM_NAME = 'lab2_part3_stream'
ACCOUNT_ID = '838267569814'
IDENTITY_POOL_ID = "us-east-1:20f1c3a7-4954-4e95-a5b3-e24065330b3d" #YOUR IDENTITY POOL ID
ROLE_ARN = "arn:aws:iam::838267569814:role/Cognito_edisonDemoKinesisUnauth_Role" #YOUR ROLE_ARN

setLcdDisplay("Wait...")

#################################################
# Instantiate cognito and obtain security token #
#################################################
# Use cognito to get an identity.
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])

# Further setup your STS using the code below
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# Connect to dynamoDB and kinesis
client_dynamo = boto.dynamodb2.connect_to_region(
    'us-east-1',
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

client_kinesis = boto.connect_kinesis(
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey

######################
# Setup DynamoDB Table
######################

table_dynamo = None
try:
    table_dynamo = Table.create(DYNAMO_TABLE_NAME, schema=[HashKey('time_of_temp')], connection=client_dynamo) 
    print "Table ", DYNAMO_TABLE_NAME, " has been created!"
except boto.exception.JSONResponseError:
    print "Table ", DYNAMO_TABLE_NAME, " already exists."
    table_dynamo = Table(DYNAMO_TABLE_NAME, connection=client_dynamo)


#################################################
# Setup switch and temperature sensor #
#################################################

# Initialize Button
# On each press it will switch mode
switch = mraa.Gpio(switch_pin_number)
switch.dir(mraa.DIR_IN)
switch.isr(mraa.EDGE_RISING, pressButton, pressButton)

tempSensor = mraa.Aio(1)

# Intially start with DynamoDB
pressButton(None)

try:
    while (1):
        # Gather data to stream continuously
        fahrenheit = getTemperatureInFahrenheit()
        timeOfTemp = str(time.time())

        # The mode is determined by flag which is toggled by button presses
        if modeIsDynamo:
            sendTemperatureToDynamo(timeOfTemp, fahrenheit)
        else:
            sendTemperatureToKinesis(timeOfTemp, fahrenheit)

        # time.sleep(0.5);
        pass
except KeyboardInterrupt:
    exit










