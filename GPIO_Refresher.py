import gpiozero as GPIO
import time
import sqlite3
import os

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

switchTime = 0.1
pulseCount = 0
samplePeriod = 60 #seconds
wheelCircumference = 0.25 #meter
time_old = time.time()
time1 = time_old
time2 = time1
time3 = time2
databaseName = 'Database.db'

relay1 = GPIO.LED(RELAY_CH1)
sensor = GPIO.Button(SENSOR_PIN, pull_up = None, bounce_time = 0.05, active_state = True)

def pulseCallback(self):
   global pulseCount
   global time_old
   pulseCount = pulseCount + 1
   time1 = time.time()
   speed = (1 / (time1 - time_old)) * wheelCircumference * 60
   time_old = time1
   #print(speed)

sensor.when_released = pulseCallback

if not os.path.isfile(databaseName):
   conn = sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("CREATE TABLE data(timestamp DATETIME, speed REAL);")
   conn.commit()
   curs.execute("CREATE TABLE settings(timestamp DATETIME, sampling_period NUMERIC, circumference NUMERIC, max_meters NUMERIC, setting1 NUMERIC, setting2 NUMERIC, setting3 NUMERIC, setting4 NUMERIC);")
   conn.commit()
   curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), 3, 0.25, 5000, 0, 0, 0, 0);")
   conn.commit()
   conn.close()

def logData(speed):
	
	conn=sqlite3.connect(databaseName)
	curs=conn.cursor()

	curs.execute("INSERT INTO data values(datetime('now', 'localtime'), (?))", speed)
	conn.commit()
	conn.close()

def getSamplingPeriod():
	conn=sqlite3.connect(databaseName)
	curs=conn.cursor()
	for row in curs.execute("SELECT sampling_period FROM settings ORDER BY timestamp DESC LIMIT 1"):
		samplingPeriod = row[0]
		if samplingPeriod > 900 : 
			samplingPeriod = 900
		elif samplingPeriod < 1 :
			samplingPeriod = 1
	conn.close()
	return samplingPeriod

samplePeriod = getSamplingPeriod()

try:
   while True:
      if time.time() > time2+samplePeriod:
         time2 = time.time() 
         speed = pulseCount * wheelCircumference * (60.0 / samplePeriod)
         pulseCount = 0
         print(speed)
         print(type(speed))

         if time.time() > time3 + 60:
            time3 = time.time()
            logData(speed)

      time.sleep(0.01)


except KeyboardInterrupt:
   print("Terminating program...")