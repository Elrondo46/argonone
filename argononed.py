#!/opt/argonone/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# PEP 8, PEP 263.
"""
Argon One Fan and Button Service Daemon
"""

import smbus
import RPi.GPIO as GPIO
import os
import time
from threading import Thread

rev = GPIO.RPI_REVISION
if rev == 2 or rev == 3:
    bus = smbus.SMBus(1)
else:
    bus = smbus.SMBus(0)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
shutdown_pin = 4
GPIO.setup(shutdown_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def shutdown_check():
    while True:
        pulsetime = 1
        def wait_for_it():
          level = GPIO.input(23)
          while (GPIO.input(23)) :
            time.sleep(0.01)
        while GPIO.input(shutdown_pin) == GPIO.HIGH:
            time.sleep(0.01)
            pulsetime += 1
        if pulsetime >= 2 and pulsetime <= 3:
            os.system("reboot")
        elif pulsetime >= 4 and pulsetime <= 5:
            os.system("shutdown now -h")


def get_fanspeed(tempval, configlist):
    for curconfig in configlist:
        curpair = curconfig.split("=")
        tempcfg = float(curpair[0])
        fancfg = int(float(curpair[1]))
        if tempval >= tempcfg:
            return fancfg
    return 0


def load_config(fname):
    newconfig = []
    try:
        with open(fname, "r") as fp:
            for curline in fp:
                if not curline:
                    continue
                tmpline = curline.strip()
                if not tmpline:
                    continue
                if tmpline[0] == "#":
                    continue
                tmppair = tmpline.split("=")
                if len(tmppair) != 2:
                    continue
                tempval = 0
                fanval = 0
                try:
                    tempval = float(tmppair[0])
                    if tempval < 0 or tempval > 100:
                        continue
                except:
                    continue
                try:
                    fanval = int(float(tmppair[1]))
                    if fanval < 0 or fanval > 100:
                        continue
                except:
                    continue
                newconfig.append("{:5.1f}={}".format(tempval, fanval))
        if len(newconfig) > 0:
            newconfig.sort(reverse=True)
    except:
        return []
    return newconfig


def temp_check():
    fanconfig = ["65=100", "60=55", "55=10"]
    tmpconfig = load_config("/etc/argononed.conf")
    if len(tmpconfig) > 0:
        fanconfig = tmpconfig
    address = 0x1a
    prevblock = 0
    while True:
        temp = os.popen("cat /sys/class/thermal/thermal_zone0/temp").readline()
        val = float(temp) / 1000
        block = get_fanspeed(val, fanconfig)
        if block < prevblock:
            time.sleep(30)
        prevblock = block
        try:
            bus.write_byte_data(address,0,block)
        except IOError:
            temp = ""
        time.sleep(30)


try:
    t1 = Thread(target=shutdown_check)
    t2 = Thread(target=temp_check)
    t1.start()
    t2.start()
except:
    t1.stop()
    t2.stop()
    GPIO.cleanup()
