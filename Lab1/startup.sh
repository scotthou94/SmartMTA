#!/bin/sh
sleep 10
python /home/root/startup.py
python /home/root/Lab1/startup_mailer.py > /tmp/mailer.txt
date > /tmp/startup.txt
exit 0
