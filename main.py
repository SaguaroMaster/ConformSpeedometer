import gpiozero as GPIO
import time
import sqlite3
import os
from collections import deque
from statistics import mean
from tkinter import *
from tkinter import ttk

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
alarmTime1 = time1
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

def getDigit(number, n):
    return number // 10**n % 10

def setLength(length):
   global lengthTarget

   lengthTarget = int(lengthTarget)

   if length == 1:
      if getDigit(lengthTarget, 0) == 9:
         lengthTarget = lengthTarget - 9
      else:
         lengthTarget = lengthTarget + 1
   elif length == 10:
      if getDigit(lengthTarget, 1) == 9:
         lengthTarget = lengthTarget - 90
      else:
         lengthTarget = lengthTarget + 10
   elif length == 100:
      if getDigit(lengthTarget, 2) == 9:
         lengthTarget = lengthTarget - 900
      else:
         lengthTarget = lengthTarget + 100
   elif length == 1000:
      if getDigit(lengthTarget, 3) == 9:
         lengthTarget = lengthTarget - 9000
      else:
         lengthTarget = lengthTarget + 1000
   elif length == 10000:
      if getDigit(lengthTarget, 4) == 9:
         lengthTarget = lengthTarget - 90000
      else:
         lengthTarget = lengthTarget + 10000

def resetLength():
   global length
   global pulseCount2
   global alarmState
   length = 0
   pulseCount2 = 0
   alarmState = 0

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

SpeedString = StringVar(value=0)
LengthString = StringVar(value=0)
AlarmLimitString = StringVar(value=0)
Digit1String = StringVar(value=0)
Digit10String = StringVar(value=0)
Digit100String = StringVar(value=0)
Digit1000String = StringVar(value=0)
Digit10000String = StringVar(value=0)

SpeedVarString = Label(root, textvariable = SpeedString, font=('bold', 130)).grid(row=2, column=3, padx=(0,0), columnspan=12)
LengthVarString = Label(root, textvariable = LengthString, font=('bold', 130)).grid(row=4, column=3, padx=(0,0), columnspan=12)

Digit10000VarString = Label(root, textvariable = Digit10000String, font=('bold', 40)).grid(row=10, column=2, padx=(0,0))
Digit1000VarString = Label(root, textvariable = Digit1000String, font=('bold', 40)).grid(row=10, column=3, padx=(0,0))
Digit100VarString = Label(root, textvariable = Digit100String, font=('bold', 40)).grid(row=10, column=4, padx=(0,0))
Digit10VarString = Label(root, textvariable = Digit10String, font=('bold', 40)).grid(row=10, column=5, padx=(0,0))
Digit1VarString = Label(root, textvariable = Digit1String, font=('bold', 40)).grid(row=10, column=6, padx=(0,0))


SpeedText = Label(root, text = 'SPEED: ', font=('bold', 30)).grid(row=2, column=1, pady=(15,15), columnspan = 2)
LengthText = Label(root, text = 'LENGTH: ', font=('bold', 30)).grid(row=4, column=1, pady=(15,15), columnspan = 2)
LengthTargetText = Label(root, text = 'ALARM SETTING: ', font=('bold', 30)).grid(row=5, column=1, pady=(15,15), columnspan = 4)
MeterMinText = Label(root, text = 'm/min', font=('bold', 50)).grid(row=2, column=16, padx=(10,0), columnspan = 2)
MeterText = Label(root, text = 'm', font=('bold', 50)).grid(row=4, column=16, padx=(10,0), columnspan = 2)
MeterText2 = Label(root, text = 'm', font=('bold', 40)).grid(row=10, column=7, padx=(10,0), columnspan = 1)

ButtonAlarmReset = Button(root, text = 'ALARM RESET', font=('bold', 10), command = resetLength, height = 5, width = 15).grid(row=10,column=8, padx=(10,10))

Plus1 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(1), height = 1, width = 2).grid(row=11,column=6, padx=(10,10))
Plus10 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(10), height = 1, width = 2).grid(row=11,column=5, padx=(10,10))
Plus100 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(100), height = 1, width = 2).grid(row=11,column=4, padx=(10,10))
Plus1000 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(1000), height = 1, width = 2).grid(row=11,column=3, padx=(10,10))
Plus10000 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(10000), height = 1, width = 2).grid(row=11,column=2, padx=(10,10))



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
      
      if length > lengthTarget:
         if time.time() > alarmTime1 + 0.5 :
            relay1.on()
            alarmTime1 = time.time()
         else
            relay1.off()

      SpeedString.set('{0: 06.1f}'.format(round(mean(runningAvgShort), 1)))
      LengthString.set('{0: 08.1f}'.format(length))
      Digit1String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 0)))
      Digit10String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 1)))
      Digit100String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 2)))
      Digit1000String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 3)))
      Digit10000String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 4)))
      
      root.state()
      root.update()
      time.sleep(0.01)


except:
   print("Terminating program...")