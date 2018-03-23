# *********************************************************************************************
# Program to update dynamodb with latest data from mta feed. It also cleans up stale entried from db
# Usage python dynamodata.py
# *********************************************************************************************
import json, time, sys
from collections import OrderedDict
from threading import Thread
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key,Attr
import threading
sys.path.append('../utils')
import tripupdate, vehicle, alert, mtaUpdates, aws

with open('../key.txt', 'rb') as keyfile:
    APIKEY = keyfile.read().rstrip('\n')
    keyfile.close()

mtaUpdate = mtaUpdates.mtaUpdates(APIKEY)
tripUpdates = mtaUpdate.getTripUpdates()

dynamodb = aws.getResource('dynamodb', 'us-east-1')
table = dynamodb.Table('mtaData')

global e_flag
e_flag = False

def addData(data):
	while(1):
		print 'thread2'
		print e_flag
		if e_flag:
			print "addData return"
			return
		time.sleep(1)

def thread1():
	now0 = datetime.now()
	ts = int(time.mktime(now0.timetuple()))
	new_data = OrderedDict({
		'tripId': 'verynewid',
		'timestamp': ts,
		})
	try:
		table.put_item(Item=new_data)
	except Exception as e:
		raise
	else:
		print 'put new data succeed'
	while(1):
		print e_flag
		if e_flag:
			return
		print 'thread1'
		time.sleep(1)
		now = datetime.now()
		delta = timedelta(seconds=30)
		expire = now - delta
		print 'now:', now
		print 'expire time: ', expire
		expire = int(time.mktime(expire.timetuple()))
		print 'expire timestamp: ', expire
		# query database for data older than 2 minutes
		response = table.scan(
    		FilterExpression=Attr('timestamp').lt(expire)
		)
		expire_list = response['Items']
		print len(expire_list), 'items expire'
		# iterate through expire list and clean the data
		for item in expire_list:
			clean_old_data(item, expire)

def clean_old_data(dict_item, expire):
	print 'item timestamp:', dict_item['timestamp']
	try:
		response = table.delete_item(
			Key={
        		'tripId': dict_item['tripId']
        	},
        	# make sure at this time it remain expire
        	ConditionExpression=Attr('timestamp').lt(expire),
    	)
	except ClientError as e:
		if e.response['Error']['Code'] == "ConditionalCheckFailedException":
			print e.response['Error']['Message']
		else:
			raise
	else:
		print 'delete_item succeeded'


def thread2():
	data = 0
	addData(data)
	print 'thread2 exit'
	return

# creaete 2 threads
t1 = threading.Thread(name='uploader', target=thread2)
t2 = threading.Thread(name='cleaner', target=thread1)

t1.start()
t2.start()
while 1:
	time.sleep(1)
	print 'main thread'
	try:
		pass
	except KeyboardInterrupt:
		e_flag = True
		print 'main thread exits'
		sys.exit
'''
t1.join()
t2.join()
'''




