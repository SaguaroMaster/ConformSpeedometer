#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import random
from threading import Timer

dbname='/home/pi/dummy.db'
samplePeriod = 60 #seconds
flashCount = 0
time1 = time.time()

import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  


def flashCounter(self):
	global flashCount
	print("Light!")
	flashCount = flashCount + 1	

GPIO.add_event_detect(17, GPIO.FALLING, callback=flashCounter, bouncetime=50)
# log sensor data on database
def logData(power, energy):
	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()

	curs.execute("INSERT INTO data values(datetime('now', 'localtime'), (?), (?))", (power, energy))
	conn.commit()
	conn.close()

def getSetting():
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	for row in curs.execute("SELECT sampling_period FROM settings ORDER BY timestamp DESC LIMIT 1"):
		samplingPeriod = row[0]
		if samplingPeriod > 900 : 
			samplingPeriod = 900
		elif samplingPeriod < 10 :
			samplingPeriod = 10
	conn.close()
	return samplingPeriod
# main function

samplePeriod = getSetting()

while True:
	if time.time() > time1+samplePeriod:
		time1 = time.time()
		energy = flashCount #Wh
		power = energy * 0.36/(samplePeriod/10) # kW
		#print("Power: " + str(power) + "kW, Energy: " + str(energy) + "Wh")
		samplePeriod = getSetting()
		logData(power, energy)
		flashCount = 0
	time.sleep(0.01)
		