#!/usr/bin/env python
###########################################
#                                         #
# Line speed, length, downtime, uptime,   #
# etc.. meter and logger.                 #
# Kristof Berta - Technology              #
# Vicente Torns Slovakia, 2024            #
#                                         #
###########################################

import os
import time
import sqlite3
from tkinter import *
from statistics import mean
from collections import deque
from platform import system as sys
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

## GPIO PINS TO USE FOR RELAYS AND SENSOR
RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

lengthSavePeriod = 5    ## period in seconds in which the current length is saved for backup in case of power outage, crash, etc..
unlockDuration = 20     ## time in seconds until the alarm setting adjustment buttons stay unlocked for after pressing the unlock button
maxPulseInterval = 3    ## max time in seconds between impulses for sensor
wheelCircumference = 0.1005 ## length per impulse in meters
daysToGraph = 2         ## time in days for which the line speed will be graphed on the deviced under the graph button

## INITIALIZE VARIABLES ||DON'T EDIT||
pulseCount = 0
pulseCount2 = 0
samplePeriod = 0.1 #seconds
savePeriod = 300 #seconds
time2 = time.time()-5
time3 = time2
time4 = time3
unlockTime = time.time()
lastPulse = 0
alarmState = 0
lengthTarget = 10000
unlockFlag = 0
speed = 0
numSamples1 = 0
numSamples2 = numSamples1
oldLength = 0
oldSpeed = 0
machineState = 0
machineStateLogged = 0
OS = sys()


if OS == 'Windows':
   print('Windows detected, no GPIO Functionality')
   databaseName = './Database.db'
   logoPath = "./logo.png"
   saveFilePath = "./lengthBackup.txt"
else:
   databaseName = '/home/pi/Database.db'
   logoPath = "/home/pi/ConformSpeedometer/logo.png"
   saveFilePath = "/home/pi/lengthBackup.txt"

   import gpiozero as GPIO

   relay1 = GPIO.LED(RELAY_CH1, active_high=False)
   relay2 = GPIO.LED(RELAY_CH2, active_high=False) 
   sensor = GPIO.Button(SENSOR_PIN, pull_up = None, active_state = True, bounce_time = 0.001)


if not os.path.isfile(databaseName):
   conn = sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("CREATE TABLE data(timestamp DATETIME, speed REAL, length REAL, alarmSetting INT);")
   conn.commit()
   curs.execute("CREATE TABLE stops(timestamp DATETIME, start BOOL, stop BOOL);")
   conn.commit()
   curs.execute("CREATE TABLE settings(timestamp DATETIME, sampling_period REAL, saving_period NUMERIC, circumference NUMERIC, max_meters NUMERIC, setting1 NUMERIC, setting2 NUMERIC, setting3 NUMERIC, setting4 NUMERIC);")
   conn.commit()
   curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), 0.1, 300, (?), 5000, 0, 0, 0, 0);", (wheelCircumference,))
   conn.commit()
   curs.execute("INSERT INTO data values(datetime('now', 'localtime'), 0, 0, 10000);")
   conn.commit()
   curs.execute("INSERT INTO stops values(datetime('now', 'localtime'), False, False);")
   conn.commit()
   conn.close()

def logData(speed, length, alarmSetting):
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("INSERT INTO data values(datetime('now', 'localtime'), (?), (?), (?))", (speed, length, int(alarmSetting)))
   conn.commit()
   conn.close()

def logStops(state):

   startState = 0
   stopState = 0

   if state == 0:
      startState = 0
      stopState = 1
   elif state == 1:
      startState = 1
      stopState = 0
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("INSERT INTO stops values(datetime('now', 'localtime'), (?), (?))", (startState, stopState))
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
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
      time = row[0]
      alarmSetting = row[3]
   return time, alarmSetting

def getHistData (numSamples2):
   global daysToGraph
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   curs.execute("SELECT * FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=daysToGraph)) + "' ORDER BY timestamp DESC")
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

def setLengthTarget():
   global lengthTarget

   Digit1String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 0)))
   Digit10String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 1)))
   Digit100String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 2)))
   Digit1000String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 3)))
   Digit10000String.set('{0: 01.0f}'.format(getDigit(lengthTarget, 4)))

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
      if getDigit(lengthTarget, 4) == 5:
         lengthTarget = lengthTarget - 50000
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
         lengthTarget = lengthTarget + 50000
      else:
         lengthTarget = lengthTarget - 10000

   if lengthTarget < 300:
      lengthTarget = 300

   setLengthTarget()
   
def resetLength():
   global length
   global pulseCount2
   global alarmState
   length = 0
   pulseCount2 = 0

def setAlarm():
   relay1.blink(on_time=0.2, off_time=1)
   relay2.on()

def resetAlarm():
   relay1.off()
   relay2.off()

def unclockSetting():
   global unlockFlag, unlockTime
   unlockFlag = 1

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

   unlockTime = time.time()

def graphWindowCallback():

   graphWindow = Toplevel(root)
   graphWindow.overrideredirect(1)
   graphWindow.title(" ")
   
   numSamples1, lengthTarget = getLastData()
   numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
   numSamples2 = numSamples1 + timedelta(days=1)

   Times, Speeds, Lengths, AlarmLengths = getHistData(numSamples2)

   for i in range(len(Times)):
      Times[i] = Times[i][5:16]

   print(Times)
   print(Speeds)

   fig = Figure(figsize=(12.8,7.4))
   a = fig.add_subplot(111)
   a.set_xlabel("Idő / Time [HH:MM]")
   a.set_ylabel("Sebesség / speed [m/min]")
   a.set_title("Sor sebessége az utóbbi 48 órában / Line speed in the past 48 hours")
   a.set_ylim([0,150])
   a.plot(Times, Speeds, linewidth = 2)
   a.set_xticks([0, int(len(Times)/6), int(len(Times)/3), int(len(Times)/2), int(len(Times)/1.5), int(len(Times)/1.2), int(len(Times)/1.01)])

   canvas = FigureCanvasTkAgg(fig, master = graphWindow)
   canvas.get_tk_widget().pack(expand = True)
   canvas.draw()

   CloseButton = Button(graphWindow, text = 'B E Z Á R    /    C L O S E', command = graphWindow.destroy, width = 70, height = 2, font = ('bold', 20))
   CloseButton.pack()


lastEdit, samplePeriod, savePeriod, wheelCircumference = getSettings()
runningAvgLong = deque(maxlen = int(savePeriod / samplePeriod))
runningAvgShort = deque(maxlen = 4)
maxLength = deque(maxlen = int(savePeriod / samplePeriod) + 1)


def pulseCallback(self):
   global pulseCount2, speed, maxPulseInterval, wheelCircumference, lastPulse
   pulseCount2 = pulseCount2 + 1
   timeDiff = time.time() - lastPulse
   if timeDiff > 0.005 and timeDiff < maxPulseInterval:
      speed = 60 / timeDiff * wheelCircumference

   lastPulse = time.time()

if OS != 'Windows': 
   sensor.when_released = pulseCallback


root = Tk()
root.title('Line Speed and Length Meter')
root.after(50, root.wm_attributes, '-fullscreen', 'true')

bg = PhotoImage( file = logoPath) 
label1 = Label(root, image = bg) 
label1.place(x = 1050,y = 2) 

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
if OS != 'Windows':
   CPUTempString = StringVar(value=GPIO.CPUTemperature().temperature)
else:
   CPUTempString = StringVar(value=69.69)

SpeedVarString = Label(root, textvariable = SpeedString, font=('bold', 130)).grid(row=2, column=3, padx=(0,0), columnspan=12)
LengthVarString = Label(root, textvariable = LengthString, font=('bold', 130)).grid(row=4, column=3, padx=(0,0), columnspan=12)

Digit10000VarString = Label(root, textvariable = Digit10000String, font=('bold', 40)).grid(row=10, column=2, padx=(0,0))
Digit1000VarString = Label(root, textvariable = Digit1000String, font=('bold', 40)).grid(row=10, column=3, padx=(0,0))
Digit100VarString = Label(root, textvariable = Digit100String, font=('bold', 40)).grid(row=10, column=4, padx=(0,0))
Digit10VarString = Label(root, textvariable = Digit10String, font=('bold', 40)).grid(row=10, column=5, padx=(0,0))
Digit1VarString = Label(root, textvariable = Digit1String, font=('bold', 40)).grid(row=10, column=6, padx=(0,0))

LastLogVarString = Label(root, textvariable = LastLogString, font=('bold', 10)).place(x = 0, y = 740)
LastLogVarString = Label(root, textvariable = TimeNowString, font=('bold', 10)).place(x = 0, y = 760)
CPUTempVarString = Label(root, textvariable = CPUTempString, font=('bold', 10)).place(x = 0, y = 780)


SpeedText = Label(root, text = 'SEBESSÉG: ', font=('bold', 30)).grid(row=2, column=1, columnspan = 3)
LengthText = Label(root, text = 'HOSSZ: ', font=('bold', 30)).grid(row=4, column=1, columnspan = 2, padx=(10,0))
LengthTargetText = Label(root, text = 'ALARM BEÁLLITÁS: ', font=('bold', 30)).grid(row=5, column=1, pady=(15,5), padx=(10,0), columnspan = 5)
MeterMinText = Label(root, text = 'm/min', font=('bold', 50)).grid(row=2, column=16, padx=(10,0), columnspan = 2)
MeterText = Label(root, text = 'm', font=('bold', 50)).grid(row=4, column=16, padx=(10,0), columnspan = 2)
MeterText2 = Label(root, text = 'm', font=('bold', 40)).grid(row=10, column=7, padx=(10,0), columnspan = 1)
MadeByText = Label(root, text = 'Tech. dept., BK', font=('bold', 10)).place(x = 50, y = 785)

ButtonCounterReset = Button(root, text = 'SZÁMLÁLÓ RESET', font=('bold', 25), command = resetLength, height = 2, bg = ResetButtonColor, wraplength=190).grid(row=9,column=9, padx=(10,10), columnspan = 9)
ButtonAlarmReset = Button(root, text = 'ALARM RESET', font=('bold', 25), command = resetAlarm, height = 2, bg = ResetButtonColor).grid(row=11,column=9, padx=(10,10), columnspan = 9)

ButtonGraph = Button(root, text = 'GRAFIKON', font=('bold', 15), command = graphWindowCallback, height = 1, bg = UnlockButtonColor).grid(row=12,column=9, padx=(10,10), pady=(15,0), columnspan = 9)

Unlock = Button(root, text = 'F E L N Y I T', font=('bold', 25), command = unclockSetting, height = 1, width = 17, bg = UnlockButtonColor).grid(row=12,column=2, padx=(10,10), columnspan = 5)
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

LengthString.set('{0: 08.1f}'.format(0))
SpeedString.set('{0: 04.0f}'.format(0))
setLengthTarget()


try:
   if os.path.isfile(saveFilePath):
      f1 = open(saveFilePath, "r")
      length = float(f1.read())
      pulseCount2 = length / wheelCircumference
      f1.close()
   else:
      f1 = open(saveFilePath, "w")
      f1.write(str(length))
      f1.close()
      length = 0
      pulseCount2 = 0
except:
   length = 0
   pulseCount2 = 0


while True:

   length = pulseCount2 * wheelCircumference

   if time.time() > time2 + samplePeriod:
      time2 = time.time()

      if time2 > lastPulse + maxPulseInterval:
         speed = 0
      
      maxLength.append(length)
      runningAvgLong.append(speed)
      runningAvgShort.append(speed)
      TimeNowString.set(datetime.now().time())

   if time.time() > time3 + savePeriod:
      time3 = time.time()
      logData(round(mean(runningAvgLong), 2), max(maxLength), lengthTarget)
      LastLogString.set(datetime.now().time())

      if OS != 'Windows':
         CPUTempString.set(GPIO.CPUTemperature().temperature)
   
   if time.time() > time4 + lengthSavePeriod:
      
      f = open(saveFilePath, "w")
      f.write(str(length))
      f.close()
      time4 = time.time()

   if length > lengthTarget and alarmState == 0:
      alarmState = 1
      setAlarm()
   elif length < lengthTarget + 50 and alarmState == 1:
      alarmState = 0


   if unlockFlag == 1 and time.time() > unlockTime + unlockDuration:
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
      unlockFlag = 0
   
   if runningAvgShort[0] != oldSpeed:
      SpeedString.set('{0: 04.0f}'.format(round(mean(runningAvgShort), 0)))
      oldSpeed = runningAvgShort[0]
   
   if length != oldLength:
      LengthString.set('{0: 08.1f}'.format(length))
      oldLength = length

   if speed == 0 and machineState == 1:
      machineState = 0
      logStops(machineState)
   elif speed != 0 and machineState == 0:
      machineState = 1
      logStops(machineState)
   
   root.state()
   root.update()
   time.sleep(0.02)
