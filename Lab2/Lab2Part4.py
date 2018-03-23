# Group: x007
# Murshed Jamil Ahmed (mja2196)
# Shijun Hou (sh3658)
# Jiahong He (jh3863)
# Robert Fea (rf2638)
# IoT Lab 2, part 4

# Temperature Monitor
# Display the current temperature to a display from the Wiced Sensor

# Setup Instructions:
# Connect the LCD screen to the I2C port
# Run the following three commands
# rfkill unblock bluetooth
# killall bluetoothd
# hciconfig hci0 up
# Before running this script use `bluetoothctl` and make sure this device is disconnected already
# Otherwise the GATT Tool will have trouble connecting to it
# Make sure the `gatttool` is in your PATH variable

import pexpect
import sys
import time
import pyupm_i2clcd as lcd

# CONSTANTS
prefix = "Notification handle = 0x002a value: "
prefixLen = len(prefix)

# LCD
myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)

def convertCelsiusToFahrenheit(celsius):
    fahrenheit = celsius * 9.0/5.0 + 32
    return fahrenheit

# Reads the Hex digits for temperature from sensor notifications
# Parses through the given line looking for the right format
def getHexTemperature(rawLine):
    # remove white spaces
    line = rawLine.strip()

    # Skip empty lines
    if len(line) <= 0:
        print "empty line: ", line
        return ""

    # Must be a notification string
    prefixIndex = line.find(prefix)
    if prefixIndex == -1:
        return ""

    # Get all the byte values after the prefix
    dataString = line[(prefixIndex + prefixLen):]
    data = dataString.split()

    # We only care about climate data which is 7 bytes long (including header)
    if len(data) != 7:
        return ""

    # Temperature is stored in last two bytes, which is little endian
    # print "Raw Climate Data: ", data
    firstByte = data[-1]
    secondByte = data[-2]
    temperatureHex = firstByte + secondByte
    return temperatureHex

def convertHexTemperatureToCelsius(hexTemperature):
    # The hexidecimal value is actually 10x the real temperature
    celsius = int(hexTemperature, 16) / 10.0
    return celsius

def sendToDisplay(line):
    print line

    # Write the message to the display, starting at the first cell
    myLcd.clear()
    myLcd.setCursor(0,0)
    myLcd.write(line)

################
####  MAIN  ####
################
sendToDisplay("Wait . . . ")

# Wiced Sensor Device Address
bluetooth_adr = '00:10:18:01:20:E3'

# Spawn a process to run the GATT tool
tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
tool.expect('\[LE\]>')

# Attempt to connect and wait for 5 seconds for confirmation
print "Preparing to connect. You might need to press the side button..."
tool.sendline('connect')
tool.expect("Connection successful", timeout=5)
print "Wiced sensor connected!"
sendToDisplay("Connected!")

# Write to the CCCD to subscribe to notifications
tool.expect('\[LE\]>')
tool.sendline('char-write-req 0x2b 0x01')
time.sleep(1)

print "Begin reading data"

try:
    while True:
        # time.sleep(0.2)
        line = tool.readline()
        hexTemperature = getHexTemperature(line)
        if len(hexTemperature) == 0:
            # Line was not climate data notification
            # We don't care about it
            continue

        celsius = convertHexTemperatureToCelsius(hexTemperature)
        fahrenheit = convertCelsiusToFahrenheit(celsius)
        sendToDisplay("Temp: " + str(celsius) + " C")

except KeyboardInterrupt:
    print "Terminating, just a moment."

    # Stop notifying and close the GATT tool
    tool.sendline('char-write-req 0x2b 0x00')
    time.sleep(1)
    tool.close()
    sendToDisplay('Bye!')
    exit()