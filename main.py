import gpiozero as GPIO
import time
import sqlite3
import os
from collections import deque
from statistics import mean
from tkinter import *
from tkinter import ttk
import numpad

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

switchTime = 0.1
pulseCount = 0
pulseCount2 = 0
samplePeriod = 3 #seconds
savePeriod = 300 #seconds
wheelCircumference = 0.23 #meter
time_old = time.time()-5
time1 = time_old
time2 = time1
time3 = time2
lastPulse = 0
databaseName = 'Database.db'
timeDiff = 0
alarmState = 0
lengthTarget = 1000

relay1 = GPIO.LED(RELAY_CH1)
relay1.off()
sensor = GPIO.Button(SENSOR_PIN, pull_up = None, bounce_time = 0.05, active_state = True)

def pulseCallback(self):
   global pulseCount, lastPulse, pulseCount2
   lastPulse = time.time()
   pulseCount = pulseCount + 1
   pulseCount2 = pulseCount2 + 1


sensor.when_released = pulseCallback

if not os.path.isfile(databaseName):
   conn = sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("CREATE TABLE data(timestamp DATETIME, speed REAL, length REAL);")
   conn.commit()
   curs.execute("CREATE TABLE settings(timestamp DATETIME, sampling_period REAL, saving_period NUMERIC, circumference NUMERIC, max_meters NUMERIC, setting1 NUMERIC, setting2 NUMERIC, setting3 NUMERIC, setting4 NUMERIC);")
   conn.commit()
   curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), 3, 300, 0.23, 5000, 0, 0, 0, 0);")
   conn.commit()
   conn.close()

def logData(speed, length):
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   print(type(speed))
   curs.execute("INSERT INTO data values(datetime('now', 'localtime'), (?), (?))", (speed, length))
   conn.commit()
   conn.close()

def getSamplingPeriod():
	conn=sqlite3.connect(databaseName)
	curs=conn.cursor()
	for row in curs.execute("SELECT sampling_period FROM settings ORDER BY timestamp DESC LIMIT 1"):
		samplingPeriod = row[0]
		if samplingPeriod > 900 : 
			samplingPeriod = 900
		elif samplingPeriod < 0.01 :
			samplingPeriod = 0.01
	conn.close()
	return samplingPeriod

def getSavingPeriod():
	conn=sqlite3.connect(databaseName)
	curs=conn.cursor()
	for row in curs.execute("SELECT saving_period FROM settings ORDER BY timestamp DESC LIMIT 1"):
		savingPeriod = row[0]
		if savingPeriod > 1800 : 
			savingPeriod = 1800
		elif savingPeriod < 10 :
			savingPeriod = 10
	conn.close()
	return savingPeriod

def setLength(length):
   global lengthTarget
   lengthTarget = length

def resetLength():
   global length
   global pulseCount2
   length = 0
   pulseCount2 = 0

def resetAlarm():
   global alarmState
   alarmState = 0

samplePeriod = getSamplingPeriod()
savePeriod = getSavingPeriod()
runningAvgLong = deque(maxlen = int(savePeriod / samplePeriod))
runningAvgShort = deque(maxlen = 2)
maxLength = deque(maxlen = int(savePeriod / samplePeriod) + 1)


root = Tk()
root.title('Line Speed and Length Meter')
root.after(50, root.wm_attributes, '-fullscreen', 'true')

SpeedString = StringVar(value=0.00)
LengthString = StringVar(value=0.00)

SpeedVarString = Label(root, textvariable = SpeedString, font=('bold', 130)).grid(row=2, column=1, padx=(10,0), columnspan=2)
LengthVarString = Label(root, textvariable = LengthString, font=('bold', 130)).grid(row=4, column=1, padx=(10,0), columnspan=2)


SpeedText = Label(root, text = 'SPEED: ', font=('bold', 40)).grid(row=1, column=1, pady=(15,15))
LengthText = Label(root, text = 'LENGTH: ', font=('bold', 40)).grid(row=3, column=1, pady=(15,15))
MeterMinText = Label(root, text = 'm/min', font=('bold', 80)).grid(row=2, column=3, padx=(10,0))
MeterText = Label(root, text = 'm', font=('bold', 80)).grid(row=4, column=3, padx=(10,0))

AlarmSetting = numpad.NumpadEntry(root, width=15).grid(row=10, column=1)
AlarmSetting3 = Entry(root, width=15).grid(row=11, column=1)

ButtonAlarmSetting = Button(root, text = 'RESET', command = resetLength).grid(row=10,column=2, padx=(10,10), pady=(10,10))



try:
   while True:
      if time.time() > time2 + samplePeriod:
         time2 = time.time() 
         speed = pulseCount * wheelCircumference * (60.0 / samplePeriod) #meters / minute
         pulseCount = 0
         length = pulseCount2 * wheelCircumference
         maxLength.append(length)
         runningAvgLong.append(speed)
         runningAvgShort.append(speed)

         if time.time() > time3 + savePeriod:
            time3 = time.time()
            logData(round(mean(runningAvgLong), 2), max(maxLength))
            print('Logged')
      
      SpeedString.set('{0: 05.1f}'.format(round(mean(runningAvgShort), 1)))
      LengthString.set('{0: 07.1f}'.format(length))

      try:  # try-except to not cause an exception when there are no/invalid characters in the text input field
         lengthTarget = int(AlarmSetting.get())
      except:
         pass
      
      root.state()
      root.update()
      time.sleep(0.01)


except:
   print("Terminating program...")