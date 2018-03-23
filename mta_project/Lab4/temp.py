'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 4: Part 1
'''

import mraa
from math import log
import json
import boto3

# Temperature sensor constants
B = 4275
R0 = 100000
tempSensorPin = 1

def getTemperature():
    """
    Read temperature from the sensor converted to Fahrenheit
    :return: float
    """
    # Read raw value from sensor
    tempSensor = mraa.Aio(tempSensorPin)
    raw = tempSensor.read()
    # raw = 512

    # Convert raw temperature reading
    R = 1023.0 / raw - 1.0
    R = R0 * R
    celsius = 1.0 / (log(R / R0) / B + 1 / 298.15) - 273.15
    fahrenheit = celsius * 9.0 / 5.0 + 32
    return fahrenheit

def addSubscribers(sns, topicArn):
    """
    Add a text and email subscriber to the topic.
    :return: None
    """
    protocolText = 'sms'
    protocolEmail = 'email'
    endpointText = '1-347-612-6598'
    endpointEmail = 'mja2196@columbia.edu'

    # Subscribe to text alerts
    subscribeResponse = sns.subscribe(
        TopicArn=topicArn,
        Protocol=protocolText,
        Endpoint=endpointText
    )
    textSubscriptionArn = subscribeResponse['SubscriptionArn']
    print "Text Subscription ARN: ", textSubscriptionArn

    # Subscribe to email alerts
    subscribeResponse = sns.subscribe(
        TopicArn=topicArn,
        Protocol=protocolEmail,
        Endpoint=endpointEmail
    )
    emailSubscriptionArn = subscribeResponse['SubscriptionArn']
    print "Email Subscription ARN: ", emailSubscriptionArn

def printSubscribers(sns, topicArn):
    """
    Print the current subscribers to the given topic
    :param sns: SNS Client
    :param topicArn: Topic ARN string
    :return: None
    """
    response = sns.list_subscriptions_by_topic(TopicArn=topicArn)
    subscriptions = response['Subscriptions']
    print "== Current Subscribers =="
    for sub in subscriptions:
        print sub['Protocol'], ': ', sub['Endpoint']
    print

def sendNotification(sns, topicArn, message, subject):
    """
    Send the given message to all subscribers of the given Topic ARN
    :param sns SNS Client object
    :param topicArn Topic ARN string
    :param message Message string to send (JSON string)
    :param Email subject string
    :return: None
    """
    response = sns.publish(
        TopicArn=topicArn,
        Message=message,
        Subject=subject,
        MessageStructure='json'
    )
    messageId = response['MessageId']
    print "Notification sent with Message ID ", messageId

# Set up AWS Connections
#########
COGNITO_ID = "EdisonApp"
ACCOUNT_ID = '838267569814'
IDENTITY_POOL_ID = 'us-east-1:9a239937-25b7-4dae-91aa-5dfecde80f86'
ROLE_ARN = 'arn:aws:iam::838267569814:role/Cognito_EdisonAppUnauth_Role'

cognito = boto3.client('cognito-identity','us-east-1')
cognito_id = cognito.get_id(AccountId=ACCOUNT_ID, IdentityPoolId=IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(IdentityId=cognito_id['IdentityId'])

sts = boto3.client('sts')
assumedRoleObject = sts.assume_role_with_web_identity(RoleArn=ROLE_ARN,
                                                      RoleSessionName=COGNITO_ID,
                                                      WebIdentityToken=oidc['Token'])
credentials = assumedRoleObject['Credentials']
##########

sns = boto3.client('sns',
                   'us-east-1',
                   aws_access_key_id=credentials['AccessKeyId'],
                   aws_secret_access_key=credentials['SecretAccessKey'],
                   aws_session_token=credentials['SessionToken'])

# Create topic if it doesn't already exist
createResponse = sns.create_topic(Name='lab4_temperature')
topicArn = createResponse['TopicArn']

printSubscribers(sns, topicArn)

# Send a different message to each protocol (just for fun)
subject = "Temperature update"
message = "Temperature: " + ("%.1f" % getTemperature()) + " F"
messageJson = {}
messageJson['default'] = message
messageJson['email'] = 'Greetings! ' + message
print "Message: " + json.dumps(messageJson)

sendNotification(sns, topicArn, json.dumps(messageJson), subject)
