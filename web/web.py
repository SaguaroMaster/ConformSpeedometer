#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from platform import system as sys
from flask import Flask, render_template, send_from_directory, make_response, request

import io
import threading
import pandas
import dateutil.relativedelta
import sqlite3


app = Flask(__name__)

minSpeed = 5 # minimum line speed below which production is considered stopped (m/min)


if sys() == 'Windows':
    conn=sqlite3.connect('./Database.db', check_same_thread=False)
    databaseName = './Database.db'
else:
    conn=sqlite3.connect('/home/pi/Database.db', check_same_thread=False)
    from gpiozero import CPUTemperature
    databaseName = '/home/pi/Database.db'
curs=conn.cursor()

lock = threading.Lock()

def getLastData():
    for row in curs.execute("SELECT * FROM data ORDER BY timestamp DESC LIMIT 1"):
        time = row[0]
        speed = row[1]
        length = row[2]
        alarmSetting = row[3]
    return time, speed, length, alarmSetting

def getFirstData():
    for row in curs.execute("SELECT * FROM data ORDER BY timestamp ASC LIMIT 1"):
        time = str(row[0])
    #conn.close()
    return time

def setGlobalVars():
    global numSamples1, numSamples2
    numSamples1, nada2, nada3, nada4 = getLastData()
    numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
    numSamples2 = numSamples1 + timedelta(days=1)

def getCPUTemp():
    if sys() == 'Windows':
        temp = 69.69
    else:
        temp = round(CPUTemperature().temperature, 1)
    return temp

def basicTemplate():
    global  numSamples1, numSamples2
    setGlobalVars()

    numSamples2_1 = numSamples2 - timedelta(days=1)
    
    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2_1)[:10]
    
    lastDate, power, energyToday, xxx = getLastData()
    firstDate = getFirstData()
    power = round(power, 2)

    templateData = {
        'power'						: power,
        'energytoday'				: energyToday,
        'minDateSel'				: numSamples1_disp,
        'maxDateSel'				: numSamples2_disp,
        'minDate'					: firstDate[:10],
        'maxDate'					: lastDate[:10],
        'maxDateFull'				: lastDate[11:],
        'sysTemp'					: getCPUTemp()
    }

    return templateData

def saveSettings(samplingPeriod, language, theme):
    curs.execute("INSERT INTO settings values(datetime('now', 'localtime'), (?), (?), (?))", (samplingPeriod, language, theme))
    conn.commit()

def getSettings():
   for row in curs.execute("SELECT * FROM settings ORDER BY timestamp DESC LIMIT 1"):
      lastEdit = row[0]
      samplingPeriod = row[1]
      savingPeriod = row[2]
      Circumference = row[3]
      return lastEdit, samplingPeriod, savingPeriod, Circumference
   return None, None, None, None
    
def getHistData (numSamples2):
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


#initialize global variables
global numSamples1, numSamples2
setGlobalVars()

def getHistDataLengthMonthly (numSamples2):
	datesSum = []
	lengthSum = []
	timeInterval = pandas.date_range(str(numSamples2 - timedelta(days=365))[:10],str(numSamples2)[:10],freq='ME').tolist()
	for entry1 in timeInterval[:len(timeInterval)]:
		entry2 = entry1 + dateutil.relativedelta.relativedelta(months=1)
		curs.execute("SELECT SUM(speed) FROM data WHERE timestamp >= '" + str(entry1) + "' AND timestamp <= '" + str(entry2) + "'")
		dataSum = curs.fetchall()
		datesSum.append(str(entry2))
		lengthSum.append(dataSum[0][0])
	lengthSum = [0 if v is None else v*5 for v in lengthSum]

	return datesSum, lengthSum

def getProductivityToday(numSamples2):
    global minSpeed

    curs.execute("SELECT COUNT(speed) FROM data WHERE speed < (?) AND timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '"+ str(numSamples2) +"';", (minSpeed,))
    dataSum = curs.fetchall()
    dataSum = dataSum[0][0]
    curs.execute("SELECT COUNT(speed) FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '"+ str(numSamples2) +"';")
    totalEntries = curs.fetchall()
    totalEntries = totalEntries[0][0]


    if dataSum != 0:
        productivity = (1 - (dataSum) / (totalEntries)) * 100
    elif dataSum == 0:
        productivity = 100
    else:
        productivity = -1

    return round(productivity, 2)

def getProductivityMonth(numSamples2):
    global minSpeed

    curs.execute("SELECT COUNT(speed) FROM data WHERE speed < (?) AND timestamp >= '" + str(numSamples2 - timedelta(days=30)) + "';", (minSpeed,))
    dataSum = curs.fetchall()
    dataSum = dataSum[0][0]

    curs.execute("SELECT COUNT(speed) FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=30)) + "' AND timestamp <= '"+ str(numSamples2) +"';")
    totalEntries = curs.fetchall()
    totalEntries = totalEntries[0][0]

    if dataSum != 0:
        productivity = (1 - (dataSum) / (totalEntries)) * 100
    elif dataSum == 0:
        productivity = 100
    else:
        productivity = -1

    return round(productivity, 2)

def getProductivityAlltime(numSamples2):
    global minSpeed

    curs.execute("SELECT COUNT(speed) FROM data WHERE speed < (?);",(minSpeed,))
    dataSum = curs.fetchall()
    curs.execute("SELECT COUNT(speed) FROM data;")
    totalEntries = curs.fetchall()
    totalEntries = totalEntries[0][0]
    dataSum = dataSum[0][0]

    if dataSum != 0:
        productivity = (1 - (dataSum) / totalEntries) * 100
    elif dataSum == 0:
        productivity = 100
    else:
        productivity = -1

    return round(productivity, 2)

def getAvgSpeed(numSamples2):
    curs.execute("SELECT AVG(speed) FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '"+ str(numSamples2) +"';")
    dataSum = curs.fetchall()
    avgSpeed = round(dataSum[0][0], 1)

    return avgSpeed






# main route 
@app.route("/")
def index():
    global  numSamples1, numSamples2
    setGlobalVars()
    lastEdit, samplingPeriod, language, theme = getSettings()


    numSamples2_1 = numSamples2 + timedelta(days=1)
    
    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2_1)[:10]
    
    lastDate, power, length, ads = getLastData()
    firstDate = getFirstData()
    power = round(power, 2)
    length = round(length, 2)

    Dates, Speeds, Lengths, Alarms = getHistData(numSamples2)
    DatesSum1, LengthsSum1 = getHistDataLengthMonthly(numSamples2)
    ProcutivityToday = getProductivityToday(numSamples2)
    ProcutivityMonth = getProductivityMonth(numSamples2)
    ProcutivityAlltime = getProductivityAlltime(numSamples2)
    avgSpeed = getAvgSpeed(numSamples2)

    for i in range(len(Dates)):
      Dates[i] = Dates[i][11:16]

    for i in range(len(DatesSum1)):
        DatesSum1[i] = DatesSum1[i][:11]

    templateData = {
        'speed'						: power,
        'length'    				: length,
        'minDateSel'				: numSamples1_disp,
        'maxDateSel'				: numSamples2_disp,
        'minDate'					: firstDate[:10],
        'maxDate'					: lastDate[:10],
        'maxDateFull'				: lastDate[11:],
        'speedX'					: Dates,
        'speedY'					: Speeds,
        'lengthsDailyX'			    : DatesSum1,
        'lengthsDailyY'		    	: LengthsSum1,
        'lengthX'	        		: Dates,
        'lengthY'		        	: Lengths,
        'alarmX'		    		: Dates,
        'alarmY'		       		: Alarms,
        'sysTemp'					: getCPUTemp(),
        'samplingPeriod'			: samplingPeriod,
        'uptimeDay'                 : ProcutivityToday,
        'uptimeMonth'               : ProcutivityMonth,
        'uptimeAll'                 : ProcutivityAlltime,
        'avgSpeed'                  : avgSpeed
    }

    return render_template('dashboard.html', **templateData)

@app.route('/', methods=['POST'])
def my_form_post():
    global  numSamples1, numSamples2
    lastEdit, samplingPeriod, savingPeriod, lengthPerPulse = getSettings()
    numSamples2 = request.form['numSamples2']
    numSamples2 = datetime.strptime(numSamples2, "%Y-%m-%d")

    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2)[:10]
    numSamples2 = numSamples2 + timedelta(days=1)
    lastDate, power, length,xxxxx = getLastData()
    firstDate = getFirstData()
    power = round(power, 2)
    length = round(length, 2)

    Dates, Speeds, Lengths, Alarms = getHistData(numSamples2)
    DatesSum1, LengthsSum1 = getHistDataLengthMonthly(numSamples2)
    ProcutivityToday = getProductivityToday(numSamples2)
    ProcutivityMonth = getProductivityMonth(numSamples2)
    ProcutivityAlltime = getProductivityAlltime(numSamples2)
    avgSpeed = getAvgSpeed(numSamples2)

    for i in range(len(Dates)):
      Dates[i] = Dates[i][11:16]

    for i in range(len(DatesSum1)):
        DatesSum1[i] = DatesSum1[i][:11]

    templateData = {
        'speed'						: power,
        'length'    				: length,
        'minDateSel'				: numSamples1_disp,
        'maxDateSel'				: numSamples2_disp,
        'minDate'					: firstDate[:10],
        'maxDate'					: lastDate[:10],
        'maxDateFull'				: lastDate[11:],
        'speedX'					: Dates,
        'speedY'					: Speeds,
        'lengthsDailyX'			    : DatesSum1,
        'lengthsDailyY'		    	: LengthsSum1,
        'lengthX'	        		: Dates,
        'lengthY'		        	: Lengths,
        'alarmX'		    		: Dates,
        'alarmY'		       		: Alarms,
        'sysTemp'					: getCPUTemp(),
        'samplingPeriod'			: samplingPeriod,
        'uptimeDay'                 : ProcutivityToday,
        'uptimeMonth'               : ProcutivityMonth,
        'uptimeAll'                 : ProcutivityAlltime,
        'avgSpeed'                  : avgSpeed
    }

    return render_template('dashboard.html', **templateData)

@app.route('/download', methods=['GET', 'POST'])
def download():
    if sys() == 'Windows':
        return send_from_directory("/", "./Database.db")
    else:
        return send_from_directory("/home/pi", "Database.db")


if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8000, debug=False)
