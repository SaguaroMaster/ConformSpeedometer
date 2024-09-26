import os
import time
import sqlite3
import calendar
import gpiozero as GPIO
import dateutil.relativedelta
from tkinter import *
from statistics import mean
from collections import deque
from matplotlib.figure import Figure
from datetime import datetime, timedelta

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk) 


RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

pulseCount = 0
pulseCount2 = 0
samplePeriod = 0.1 #seconds
savePeriod = 300 #seconds
wheelCircumference = 0.23 #meter
time2 = time.time()-5
time3 = time2
unlockTime = time.time()
lastPulse = 0
databaseName = 'Database.db'
alarmState = 0
lengthTarget = 1000
unlockFlag = 0
unlockDuration = 20
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
   curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), 0.1, 300, 0.078, 5000, 0, 0, 0, 0);")
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
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
   for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
      time = row[0]
      alarmSetting = row[3]
   return time, alarmSetting

def getHistData (numSamples1, numSamples2):
   conn=sqlite3.connect(databaseName)
   curs=conn.cursor()
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

def graphWindowCallback():

   graphWindow = Toplevel(root)
   #graphWindow.resizable(0, 0)
   graphWindow.overrideredirect(1)
   graphWindow.title(" ")
   #graphWindow.attributes("-fullscreen", True)
   #graphWindow.after(50, graphWindow.attributes, '-fullscreen', 'true')
   #time.sleep(0.051)

   #graphWindow.transient(root)
   #graphWindow.grab_set()
   
   Times, Speeds, Lengths, AlarmLengths = getHistData(numSamples1, numSamples2)

   for i in range(len(Times)):
      Times[i] = Times[i][11:16]

   fig = Figure(figsize=(12.8,7.4))
   a = fig.add_subplot(111)
   a.set_xlabel("Time [HH:MM]")
   a.set_ylabel("Speed [m/min]")
   a.set_title("Line speed for last 2 days, 5 minutes sampling period")
   a.set_ylim([0,150])
   a.plot(Times, Speeds, linewidth = 2)
   a.set_xticks([0, int(len(Times)/6), int(len(Times)/3), int(len(Times)/2), int(len(Times)/1.5), int(len(Times)/1.2), int(len(Times)/1.01)])

   canvas = FigureCanvasTkAgg(fig, master = graphWindow)
   canvas.get_tk_widget().pack(expand = True)
   canvas.draw()

   CloseButton = Button(graphWindow, text = 'B E Z Á R', command = graphWindow.destroy, width = 10, height = 2, font = ('bold', 20))
   CloseButton.pack()


lastEdit, samplePeriod, savePeriod, wheelCircumference = getSettings()
runningAvgLong = deque(maxlen = int(savePeriod / samplePeriod))
runningAvgShort = deque(maxlen = 4)
maxLength = deque(maxlen = int(savePeriod / samplePeriod) + 1)

numSamples1, lengthTarget = getLastData()
numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
numSamples2 = numSamples1 + timedelta(days=1)



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


SpeedText = Label(root, text = 'SEB.: ', font=('bold', 30)).grid(row=2, column=1, columnspan = 2)
LengthText = Label(root, text = 'HOSSZ: ', font=('bold', 30)).grid(row=4, column=1, columnspan = 2)
LengthTargetText = Label(root, text = 'ALARM BEÁLLITÁS: ', font=('bold', 30)).grid(row=5, column=1, pady=(15,5), columnspan = 4)
MeterMinText = Label(root, text = 'm/min', font=('bold', 50)).grid(row=2, column=16, padx=(10,0), columnspan = 2)
MeterText = Label(root, text = 'm', font=('bold', 50)).grid(row=4, column=16, padx=(10,0), columnspan = 2)
MeterText2 = Label(root, text = 'm', font=('bold', 40)).grid(row=10, column=7, padx=(10,0), columnspan = 1)

ButtonCounterReset = Button(root, text = 'SZÁML. RESET', font=('bold', 25), command = resetLength, height = 2, bg = ResetButtonColor).grid(row=9,column=9, padx=(10,10), columnspan = 9)
ButtonAlarmReset = Button(root, text = 'ALARM RESET', font=('bold', 25), command = resetAlarm, height = 2, bg = ResetButtonColor).grid(row=11,column=9, padx=(10,10), columnspan = 9)

ButtonGraph = Button(root, text = 'GRAPH', font=('bold', 15), command = graphWindowCallback, height = 1, bg = UnlockButtonColor).grid(row=12,column=17, columnspan = 9)

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
      time.sleep(0.02)


except:
  print("Terminating program...")