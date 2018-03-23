'''
Group Name: x007
 Murshed Jamil Ahmed (mja2196)
 Shijun Hou (sh3658)
 Jiahong He (jh3863)
 Robert Fea (rf2638)
IoT Lab 2, part 1
'''

import mraa
from time import gmtime, strftime
from firebase import firebase
import json as simplejson
from math import log

# Constants for temperature calculation
B = 4275
R0 = 100000

switch_pin_number = 8

# interrupt to check temperature value for button press
def buttonPress(args):
	print 'Button Pressed'
	# read in ADC value from the sensor
	tempSensor = mraa.Aio(1)
	raw = tempSensor.read()

	print 'Reading temperature'
	# Calculate celsius temperature based on Grove 
	# sensor documentation.
	R = 1023.0/raw - 1.0
	R = R0 * R
	celsius = 1.0/(log(R/R0)/B+1/298.15)-273.15

	# Convert to fahrenheit temperature
	fahrenheit = celsius * 9.0/5.0 + 32
	# string = "Temp: " + ('%.1f' % fahrenheit) + " F"
	print 'Temperature Calculated'

	try:
		fb = firebase.FirebaseApplication('https://x007-cb9e4.firebaseio.com',None)
		# result = firebase.get('',None)
		# print result
		print 'Established Firebase connection'
	except Exception as e:
		print e
		
	timeCheck = strftime("%Y-%m-%d %H:%M:%S", gmtime())
	# '2009-01-05 22:14:39'

	data = {timeCheck:fahrenheit}
	print data
	#data = simplejson.dumps(data)

	print 'Beginning post'
	try:
		post = fb.post('',data)
	except Exception as e:
		print e

	print 'Done with post'
	print post


# Initialize the switch pin as GPIO and set its 
# interrupt handler
switch = mraa.Gpio(switch_pin_number)
switch.dir(mraa.DIR_IN)
switch.isr(mraa.EDGE_RISING, buttonPress, buttonPress)

try:
	# Just keep the program running...
	while(1):
		pass
except KeyboardInterrupt:
	# ... until the user decides to quit with CRTL+C
	exit
