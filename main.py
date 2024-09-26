import gpiozero as GPIO
import time
from datetime import datetime, timedelta
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
unlockTime = time.time()
alarmTime1 = time1
lastPulse = 0
databaseName = 'Database.db'
timeDiff = 0
alarmState = 0
lengthTarget = 1000
unlockFlag = 0
unlockDuration = 30
speed = 0
maxPulseInterval = 3
numSamples1 = 0
numSamples2 = numSamples1


relay1 = GPIO.LED(RELAY_CH1, active_high=False)
sensor = GPIO.Button(SENSOR_PIN, pull_up = None, active_state = True, bounce_time = 0.001)
#sensor = GPIO.Button(SENSOR_PIN, pull_up = False, bounce_time = 0.05)

def pulseCallback(self):
   global pulseCount, lastPulse, pulseCount2, speed, maxPulseInterval
   pulseCount = pulseCount + 1
   pulseCount2 = pulseCount2 + 1
   speed = 60 / (time.time() - lastPulse) * wheelCircumference
   lastPulse = time.time()

sensor.when_released = pulseCallback

if not os.path.isfile(databaseName):
   conn = sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("CREATE TABLE data(timestamp DATETIME, speed REAL, length REAL, alarmSetting INT);")
   conn.commit()
   curs.execute("CREATE TABLE settings(timestamp DATETIME, sampling_period REAL, saving_period NUMERIC, circumference NUMERIC, max_meters NUMERIC, setting1 NUMERIC, setting2 NUMERIC, setting3 NUMERIC, setting4 NUMERIC);")
   conn.commit()
   curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), 0.2, 300, 0.078, 5000, 0, 0, 0, 0);")
   conn.commit()
   conn.close()

def logData(speed, length, alarmSetting):
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("INSERT INTO data values(datetime('now', 'localtime'), (?), (?), (?))", (speed, length, int(alarmSetting)))
   conn.commit()
   conn.close()

def getSettings():
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   for row in curs.execute("SELECT * FROM settings ORDER BY timestamp DESC LIMIT 1"):
      lastEdit = row[0]
      samplingPeriod = row[1]
      savingPeriod = row[2]
      Circumference = row[3]
      return lastEdit, samplingPeriod, savingPeriod, Circumference
   return None, None, None, None

def getLastData():
   for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
      time = row[0]
   return time

def getHistDataSpeed (numSamples1, numSamples2):
   numSamples1 = getLastData()
   curs.execute("SELECT * FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '" + str(numSamples2) + "' ORDER BY timestamp DESC")
   data = curs.fetchall()
   dates = []
   speed = []
   length = []
   alarm = []
   for row in reversed(data):
      dates.append(row[0])
      speed.append(row[1])
      length.append(row[2])
      alarm.append(row[3])
   return dates, speed, length, alarm

def getDigit(number, n):
    return number // 10**n % 10

def setLength(length): #if it looks stupid but works it aint stupid
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

   if length == -1:
      if getDigit(lengthTarget, 0) == 0:
         lengthTarget = lengthTarget + 9
      else:
         lengthTarget = lengthTarget - 1
   elif length == -10:
      if getDigit(lengthTarget, 1) == 0:
         lengthTarget = lengthTarget + 90
      else:
         lengthTarget = lengthTarget - 10
   elif length == -100:
      if getDigit(lengthTarget, 2) == 0:
         lengthTarget = lengthTarget + 900
      else:
         lengthTarget = lengthTarget - 100
   elif length == -1000:
      if getDigit(lengthTarget, 3) == 0:
         lengthTarget = lengthTarget + 9000
      else:
         lengthTarget = lengthTarget - 1000
   elif length == -10000:
      if getDigit(lengthTarget, 4) == 0:
         lengthTarget = lengthTarget + 90000
      else:
         lengthTarget = lengthTarget - 10000

def resetLength():
   global length
   global pulseCount2
   global alarmState
   length = 0
   pulseCount2 = 0
   alarmState = 0

def setAlarm():
   relay1.blink(on_time=0.2, off_time=1)

def resetAlarm():
   relay1.off()

def unclockSetting():
   global unlockFlag
   unlockFlag = 1


lastEdit, samplePeriod, savePeriod, wheelCircumference = getSettings()
runningAvgLong = deque(maxlen = int(savePeriod / samplePeriod))
runningAvgShort = deque(maxlen = 4)
maxLength = deque(maxlen = int(savePeriod / samplePeriod) + 1)

numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
numSamples2 = numSamples1 + timedelta(days=1)

print(getHistDataSpeed (numSamples1, numSamples2))


root = Tk()
root.title('Line Speed and Length Meter')
root.after(50, root.wm_attributes, '-fullscreen', 'true')

ResetButtonColor = '#ba737e'
TargetButtonColor = '#82a9d9'
UnlockButtonColor = '#c9c9c9'

SpeedString = StringVar(value=0)
LengthString = StringVar(value=0)
AlarmLimitString = StringVar(value=0)
Digit1String = StringVar(value=0)
Digit10String = StringVar(value=0)
Digit100String = StringVar(value=0)
Digit1000String = StringVar(value=0)
Digit10000String = StringVar(value=0)

LastLogString = StringVar(value=datetime.now().time())
TimeNowString = StringVar(value=datetime.now().time())
CPUTempString = StringVar(value=GPIO.CPUTemperature().temperature)

SpeedVarString = Label(root, textvariable = SpeedString, font=('bold', 130)).grid(row=2, column=3, padx=(0,0), columnspan=12)
LengthVarString = Label(root, textvariable = LengthString, font=('bold', 130)).grid(row=4, column=3, padx=(0,0), columnspan=12)

Digit10000VarString = Label(root, textvariable = Digit10000String, font=('bold', 40)).grid(row=10, column=2, padx=(0,0))
Digit1000VarString = Label(root, textvariable = Digit1000String, font=('bold', 40)).grid(row=10, column=3, padx=(0,0))
Digit100VarString = Label(root, textvariable = Digit100String, font=('bold', 40)).grid(row=10, column=4, padx=(0,0))
Digit10VarString = Label(root, textvariable = Digit10String, font=('bold', 40)).grid(row=10, column=5, padx=(0,0))
Digit1VarString = Label(root, textvariable = Digit1String, font=('bold', 40)).grid(row=10, column=6, padx=(0,0))

LastLogVarString = Label(root, textvariable = LastLogString, font=('bold', 10)).grid(row=12, column=9)
LastLogVarString = Label(root, textvariable = TimeNowString, font=('bold', 10)).grid(row=12, column=10)
CPUTempVarString = Label(root, textvariable = CPUTempString, font=('bold', 10)).grid(row=12, column=11)


SpeedText = Label(root, text = 'SPEED: ', font=('bold', 30)).grid(row=2, column=1, columnspan = 2)
LengthText = Label(root, text = 'LENGTH: ', font=('bold', 30)).grid(row=4, column=1, columnspan = 2)
LengthTargetText = Label(root, text = 'ALARM SETTING: ', font=('bold', 30)).grid(row=5, column=1, pady=(15,5), columnspan = 4)
MeterMinText = Label(root, text = 'm/min', font=('bold', 50)).grid(row=2, column=16, padx=(10,0), columnspan = 2)
MeterText = Label(root, text = 'm', font=('bold', 50)).grid(row=4, column=16, padx=(10,0), columnspan = 2)
MeterText2 = Label(root, text = 'm', font=('bold', 40)).grid(row=10, column=7, padx=(10,0), columnspan = 1)

ButtonCounterReset = Button(root, text = 'RESET COUNTER', font=('bold', 25), command = resetLength, height = 2, bg = ResetButtonColor).grid(row=9,column=9, padx=(10,10), columnspan = 9)
ButtonAlarmReset = Button(root, text = 'RESET ALARM', font=('bold', 25), command = resetAlarm, height = 2, bg = ResetButtonColor).grid(row=11,column=9, padx=(10,10), columnspan = 9)

Unlock = Button(root, text = 'U  N  L  O  C  K', font=('bold', 25), command = unclockSetting, height = 1, width = 17, bg = UnlockButtonColor).grid(row=12,column=2, padx=(10,10), columnspan = 5)
Plus1 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(1), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Plus1.grid(row=9,column=6, padx=(10,10))
Plus10 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(10), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Plus10.grid(row=9,column=5, padx=(10,10))
Plus100 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(100), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Plus100.grid(row=9,column=4, padx=(10,10))
Plus1000 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(1000), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Plus1000.grid(row=9,column=3, padx=(10,10))
Plus10000 = Button(root, text = '+', font=('bold', 40), command = lambda: setLength(10000), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Plus10000.grid(row=9,column=2, padx=(10,10))

Minus1 = Button(root, text = '-', font=('bold', 40), command = lambda: setLength(-1), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Minus1.grid(row=11,column=6, padx=(10,10))
Minus10 = Button(root, text = '-', font=('bold', 40), command = lambda: setLength(-10), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Minus10.grid(row=11,column=5, padx=(10,10))
Minus100 = Button(root, text = '-', font=('bold', 40), command = lambda: setLength(-100), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Minus100.grid(row=11,column=4, padx=(10,10))
Minus1000 = Button(root, text = '-', font=('bold', 40), command = lambda: setLength(-1000), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Minus1000.grid(row=11,column=3, padx=(10,10))
Minus10000 = Button(root, text = '-', font=('bold', 40), command = lambda: setLength(-10000), height = 1, width = 2, bg = TargetButtonColor, state = DISABLED)
Minus10000.grid(row=11,column=2, padx=(10,10))


try:
   while True:
      if time.time() > time2 + samplePeriod:
         time2 = time.time()

         if time2 > lastPulse + maxPulseInterval:
            speed = 0

         #speed = pulseCount * wheelCircumference * (60.0 / samplePeriod) #meters / minute
         pulseCount = 0
         length = pulseCount2 * wheelCircumference
         maxLength.append(length)
         runningAvgLong.append(speed)
         runningAvgShort.append(speed)
         TimeNowString.set(datetime.now().time())

      if time.time() > time3 + savePeriod:
         time3 = time.time()
         logData(round(mean(runningAvgLong), 2), max(maxLength), lengthTarget)
         LastLogString.set(datetime.now().time())
         CPUTempString.set(GPIO.CPUTemperature().temperature)
      

      if length > lengthTarget and alarmState == 0:
         alarmState = 1
         setAlarm()

      if unlockFlag == 1:
         Plus1.config(state = NORMAL)
         Plus10.config(state = NORMAL)
         Plus100.config(state = NORMAL)
         Plus1000.config(state = NORMAL)
         Plus10000.config(state = NORMAL)
         Minus1.config(state = NORMAL)
         Minus10.config(state = NORMAL)
         Minus100.config(state = NORMAL)
         Minus1000.config(state = NORMAL)
         Minus10000.config(state = NORMAL)
         unlockFlag = 0
         unlockTime = time.time()
      elif unlockFlag == 0 and time.time() > unlockTime + unlockDuration:
         Plus1.config(state = DISABLED)
         Plus10.config(state = DISABLED)
         Plus100.config(state = DISABLED)
         Plus1000.config(state = DISABLED)
         Plus10000.config(state = DISABLED)
         Minus1.config(state = DISABLED)
         Minus10.config(state = DISABLED)
         Minus100.config(state = DISABLED)
         Minus1000.config(state = DISABLED)
         Minus10000.config(state = DISABLED)

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