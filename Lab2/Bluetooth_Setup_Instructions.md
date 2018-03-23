### When Do I use this?
When demonstrating Lab2Part4.py with the Wiced sensor.

### Hardware Setup
* Insert the coin cell battery into the Wiced sensor and close the cover tightly
** Make sure the light turns on, otherwise you need a new battery
* Connect the Grove LCD screen to the I2C port (corner port)

### Reset Bluetooth on the Board
Run the following three commands in the terminal
```
rfkill unblock bluetooth
killall bluetoothd
hciconfig hci0 up
```

### Pairing and connecting
* Run the `bluetoothctl` command on the terminal
* If you aren't already paired, run `pair 00:10:18:01:20:E3`
** Be sure the Wiced sensor is _awake_!
* If you are not automatically connected, run `connect 00:10:18:01:20:E3`
* *IMPORTANT*: run `disconnect 00:10:18:01:20:E3` before you exit `bluetoothctl`. If it remains connected, the `gatttool` will not be able to connect to it for the demo.

### Add GATT tool to your path
Execute the following on the terminal
```
export PATH=$PATH:~/bluez-5.24/attrib/
```
When you reboot, your global path variable is reset. 

### Connecting for the Demo
* Run the script with `python Lab2Part4.py`
* Make sure that you hit the wake button on the Wiced sensor or the script will not be able to connect and will crash.
* If it does crash, re-run and make sure the sensor is awake!