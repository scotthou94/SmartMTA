# Group: x007
# Murshed Jamil Ahmed (mja2196)
# Shijun Hou (sh3658)
# Jiahong He (jh3863)
# Robert Fea (rf2638)
# IoT Lab 1

# Lab 1: Temperature Monitor
# Display the current temperature to a display every time a button is pressed

import mraa
import time
from math import log
import pyupm_i2clcd as lcd
import time
 
# Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)

# Constants for temperature calculation
B = 4275
R0 = 100000

switch_pin_number=8
 
# Interrupt called on each button press
def buttonPress(args):
	# Read in ADC value from the sensor
	tempSensor = mraa.Aio(1)
	raw = tempSensor.read()
	#print "Raw ADC: ", raw

	# Calculate the celsius temperature based on the Grove sensor documentation
	R = 1023.0/raw - 1.0
	R = R0 * R
	celsius = 1.0/(log(R/R0)/B+1/298.15)-273.15

	# Convert to fahrenheit temperature
	fahrenheit = celsius * 9.0/5.0 + 32
	string = "Temp: " + ('%.1f' % fahrenheit) + " F"
	print string

	# clear scren and write message
	myLcd.setCursor(0,0)
	myLcd.write("                ");

	# Write the message to the display, starting at the first cell
	myLcd.setCursor(0,0)
	myLcd.write(string)

# Initialize the switch pin as GPIO and set its interrupt handler
switch = mraa.Gpio(switch_pin_number)
switch.dir(mraa.DIR_IN)
switch.isr(mraa.EDGE_RISING, buttonPress, buttonPress)

try:
	# Just keep the program running . . .
	while(1):
		pass
except KeyboardInterrupt:
	# . . . until the user decides to quit with CTRL+C
	exit
