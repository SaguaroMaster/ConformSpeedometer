#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from platform import system as sys

from flask import Flask, render_template, send_from_directory, request

import dateutil.relativedelta
import threading
import platform
import sqlite3
import pandas
import csv
import os

app = Flask(__name__)
hostName = str(platform.node())

if hostName == 'conf1pi':
    activeButton1 = 'active'
    activeButton2 = ''
    activeButton3 = ''
    lineName = 'Conform 1'
elif hostName == 'conf2pi':
    activeButton1 = ''
    activeButton2 = 'active'
    activeButton3 = ''
    lineName = 'Conform 2'
elif hostName == 'conf3pi':
    activeButton1 = ''
    activeButton2 = ''
    activeButton3 = 'active'
    lineName = 'Conform 3'
else:
    activeButton1 = ''
    activeButton2 = ''
    activeButton3 = ''
    lineName = 'unknown device'

if sys() == 'Windows':
    conn=sqlite3.connect('./Database.db', check_same_thread=False)
    databaseName = './Database.db'
else:
    conn=sqlite3.connect('/home/pi/Database.db', check_same_thread=False)
    databaseName = '/home/pi/Database.db'
curs=conn.cursor()

lock = threading.Lock()



def logIp(page):

    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr) 
    curs.execute("INSERT INTO log values(datetime('now', 'localtime'), (?), (?))", (ip, page))
    conn.commit()

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
    return time

def setGlobalVars():
    global numSamples1, numSamples2
    numSamples1, nada2, nada3, nada4 = getLastData()
    numSamples1 = datetime(*datetime.strptime(numSamples1, "%Y-%m-%d %H:%M:%S").timetuple()[:3])
    numSamples2 = numSamples1 + timedelta(days=1, hours=6)

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
	timeInterval = pandas.date_range(str(numSamples2 - timedelta(days=365))[:10],str(numSamples2)[:10],freq='M').tolist()
	for entry1 in timeInterval[:len(timeInterval)]:
		entry2 = entry1 + dateutil.relativedelta.relativedelta(months=1)
		curs.execute("SELECT SUM(speed) FROM data WHERE timestamp >= '" + str(entry1) + "' AND timestamp <= '" + str(entry2) + "'")
		dataSum = curs.fetchall()
		datesSum.append(str(entry2))
		lengthSum.append(dataSum[0][0])
	lengthSum = [0 if v is None else v*5/1000 for v in lengthSum]

	return datesSum, lengthSum

def getProductivityToday(numSamples2):

    curs.execute("SELECT * FROM stops WHERE timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '"+ str(numSamples2) +"';")
    data = curs.fetchall()
    
    StoppedDates = []
    StoppedIntervals = []

    if len(data) != 0:
        oldDate = datetime(*datetime.strptime(data[0][0], "%Y-%m-%d %H:%M:%S").timetuple()[:6])
        oldState = data[0][1]
        for i in data:

            Date = datetime(*datetime.strptime(i[0], "%Y-%m-%d %H:%M:%S").timetuple()[:6])

            if i[1] == 1 and i[2] == 0 and oldState !=1:
                # its a start
                timeDelta = Date - oldDate
                if timeDelta > timedelta(seconds = 20):
                    StoppedDates.append([oldDate, Date])

            oldDate = Date
            oldState = i[1]
        
        for i in StoppedDates:
            timeDelta = i[1] - i[0]
            if timeDelta > timedelta(seconds = 20):
                StoppedIntervals.append(timeDelta)

        
        
        timesStopped = len(StoppedIntervals)
        totalStoppedTime = sum(StoppedIntervals, timedelta())

        return totalStoppedTime, timesStopped, StoppedDates
    
    else:
        return timedelta(seconds=0), 0, StoppedDates

def getProductivityMonth(numSamples2):

    curs.execute("SELECT * FROM stops WHERE timestamp >= '" + str(numSamples2 - timedelta(days=30)) + "' AND timestamp <= '"+ str(numSamples2) +"';")
    data = curs.fetchall()
    
    StoppedDates = []
    StoppedIntervals = []

    if len(data) != 0:
        oldDate = datetime(*datetime.strptime(data[0][0], "%Y-%m-%d %H:%M:%S").timetuple()[:6])
        oldState = data[0][1]
        for i in data:

            Date = datetime(*datetime.strptime(i[0], "%Y-%m-%d %H:%M:%S").timetuple()[:6])

            if i[1] == 1 and i[2] == 0 and oldState !=1:
                # its a start
                timeDelta = Date - oldDate
                if timeDelta > timedelta(seconds = 20):
                    StoppedDates.append([oldDate, Date])

            oldDate = Date
            oldState = i[1]
        
        for i in StoppedDates:
            timeDelta = i[1] - i[0]
            if timeDelta > timedelta(seconds = 20):
                StoppedIntervals.append(timeDelta)
        
        timesStopped = len(StoppedIntervals)
        totalStoppedTime = sum(StoppedIntervals, timedelta())

        return totalStoppedTime, timesStopped, StoppedDates
    
    else:
        return timedelta(seconds=0), 0, StoppedDates

def getProductivityAlltime():
    curs.execute("SELECT * FROM stops;")
    data = curs.fetchall()
    
    StoppedDates = []
    StoppedIntervals = []

    if len(data) != 0:
        oldDate = datetime(*datetime.strptime(data[0][0], "%Y-%m-%d %H:%M:%S").timetuple()[:6])
        oldState = data[0][1]
        for i in data:

            Date = datetime(*datetime.strptime(i[0], "%Y-%m-%d %H:%M:%S").timetuple()[:6])

            if i[1] == 1 and i[2] == 0 and oldState !=1:
                # its a start
                timeDelta = Date - oldDate
                if timeDelta > timedelta(seconds = 20):
                    StoppedDates.append([oldDate, Date])

            oldDate = Date
            oldState = i[1]
        
        for i in StoppedDates:
            timeDelta = i[1] - i[0]
            if timeDelta > timedelta(seconds = 20):
                StoppedIntervals.append(timeDelta)
        
        timesStopped = len(StoppedIntervals)
        totalStoppedTime = sum(StoppedIntervals, timedelta())

        return totalStoppedTime, timesStopped, StoppedDates
    
    else:
        return timedelta(seconds=0), 0, StoppedDates

def getAvgSpeed(numSamples2):
    curs.execute("SELECT AVG(speed) FROM data WHERE timestamp >= '" + str(numSamples2 - timedelta(days=1)) + "' AND timestamp <= '"+ str(numSamples2) +"';")
    dataSum = curs.fetchall()
    avgSpeed = round(dataSum[0][0], 1)

    return avgSpeed

def saveToExcel(csvName):
    curs.execute("SELECT * FROM data;")
    data = curs.fetchall()
    if os.path.isfile(csvName):
        os.remove(csvName) 

    with open(csvName, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date and Time', 'Speed [m/min]', 'Length [m]', 'Alarm Setting [m]'])
        writer.writerows(data)

def readLog():
    curs.execute("SELECT * FROM log;")
    data = curs.fetchall()
    return data

# main route 
@app.route("/")
def index():
    global  numSamples1, numSamples2, activeButton1, activeButton2, activeButton3, lineName
    setGlobalVars()
    logIp("index")
    lastEdit, samplingPeriod, language, theme = getSettings()
    
    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2 - timedelta(days = 1))[:10]

    lastDate, power, length, ads = getLastData()
    firstDate = getFirstData()
    power = round(power, 2)
    length = round(length, 2)

    Dates, Speeds, Lengths, Alarms = getHistData(numSamples2)
    DatesSum1, LengthsSum1 = getHistDataLengthMonthly(numSamples2)
    avgSpeed = getAvgSpeed(numSamples2)

    totalStoppedTime24h, timesStopped24h, StoppedDates24h = getProductivityToday(numSamples2)
    totalStoppedTime30d, timesStopped30d, StoppedDates30d = getProductivityMonth(numSamples2)
    #totalStoppedTimeAll, timesStoppedAll, StoppedDatesAll = getProductivityAlltime()

    for i in range(len(Dates)):
      Dates[i] = Dates[i][5:16]

    for i in range(len(DatesSum1)):
        DatesSum1[i] = DatesSum1[i][:7]

    productivity24h = round(totalStoppedTime24h / timedelta(hours = 24) * 100, 1)
    productivity30d = round(totalStoppedTime30d / timedelta(days = 30) * 100, 1)


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
        'downTime24h'               : totalStoppedTime24h,
        'timesStopped24h'           : timesStopped24h,
        'productivity24h'           : productivity24h,
        'downTime30d'               : totalStoppedTime30d,
        'timesStopped30d'           : timesStopped30d,
        'productivity30d'           : productivity30d,
        'avgSpeed'                  : avgSpeed,
        'lineName'                  : lineName,
        'activeButton1'             : activeButton1,
        'activeButton2'             : activeButton2,
        'activeButton3'             : activeButton3,
        'timeNow'                   : datetime.now().time()
    }

    return render_template('dashboard.html', **templateData)

@app.route('/', methods=['POST'])
def my_form_post():
    global  numSamples1, numSamples2, activeButton1, activeButton2, activeButton3, lineName
    lastEdit, samplingPeriod, savingPeriod, lengthPerPulse = getSettings()
    numSamples2 = request.form['numSamples2']
    numSamples2 = datetime.strptime(numSamples2, "%Y-%m-%d")

    logIp("getDate " + str(numSamples2))

    numSamples1_disp = str(numSamples1)[:10]
    numSamples2_disp = str(numSamples2)[:10]
    numSamples2 = numSamples2 + timedelta(days=1, hours=6)
    lastDate, power, length, xxxxx = getLastData()
    firstDate = getFirstData()
    power = round(power, 2)
    length = round(length, 2)

    Dates, Speeds, Lengths, Alarms = getHistData(numSamples2)
    DatesSum1, LengthsSum1 = getHistDataLengthMonthly(numSamples2)
    avgSpeed = getAvgSpeed(numSamples2)

    totalStoppedTime24h, timesStopped24h, StoppedDates24h = getProductivityToday(numSamples2)
    totalStoppedTime30d, timesStopped30d, StoppedDates30d = getProductivityMonth(numSamples2)
    #totalStoppedTimeAll, timesStoppedAll, StoppedDatesAll = getProductivityAlltime()

    for i in range(len(Dates)):
      Dates[i] = Dates[i][5:16]

    for i in range(len(DatesSum1)):
        DatesSum1[i] = DatesSum1[i][:7]

    productivity24h = round(totalStoppedTime24h / timedelta(hours = 24) * 100, 1)
    productivity30d = round(totalStoppedTime30d / timedelta(days = 30) * 100, 1)

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
        'downTime24h'               : totalStoppedTime24h,
        'timesStopped24h'           : timesStopped24h,
        'productivity24h'           : productivity24h,
        'downTime30d'               : totalStoppedTime30d,
        'timesStopped30d'           : timesStopped30d,
        'productivity30d'           : productivity30d,
        'avgSpeed'                  : avgSpeed,
        'lineName'                  : lineName,
        'activeButton1'             : activeButton1,
        'activeButton2'             : activeButton2,
        'activeButton3'             : activeButton3,
        'timeNow'                   : datetime.now().time()
    }

    return render_template('dashboard.html', **templateData)

@app.route('/download', methods=['GET', 'POST'])
def download():
    logIp("downloadDB")

    return send_from_directory("/home/pi", "Database.db")

@app.route('/downloadcsv', methods=['GET', 'POST'])
def downloadcsv():
    logIp("downloadCSV")

    csvName = 'ExportedData.csv'
    saveToExcel(csvName)
    return send_from_directory("/home/pi", csvName)


@app.route("/downtime24h")
def downtime24h():
    global numSamples2

    logIp("downtime24h " + str(numSamples2))
    
    totalStoppedTime24h, timesStopped24h, StoppedDates24h = getProductivityToday(numSamples2)

    formattedString = []

    for i in StoppedDates24h:
        formattedString.append([str(i[0]), str(i[1])])

    return formattedString

@app.route("/downtime30d")
def downtime30d():
    global numSamples2   

    logIp("downtime30d " + str(numSamples2))
    
    totalStoppedTime24h, timesStopped24h, StoppedDates24h = getProductivityMonth(numSamples2)

    formattedString = []

    for i in StoppedDates24h:
        formattedString.append([str(i[0]), str(i[1])])

    return formattedString

@app.route("/help")
def help():
    global  numSamples1, numSamples2

    logIp("help")
    
    lastDate, power, length, ads = getLastData()
    power = round(power, 2)
    length = round(length, 2)

    Dates, Speeds, Lengths, Alarms = getHistData(numSamples2)
    avgSpeed = getAvgSpeed(numSamples2)

    templateData = {
        'speed'						: power,
        'length'    				: length,
        'maxDate'					: lastDate[:10],
        'maxDateFull'				: lastDate[11:],
        'speedX'					: Dates,
        'speedY'					: Speeds,
        'lengthX'	        		: Dates,
        'lengthY'		        	: Lengths,
        'alarmX'		    		: Dates,
        'alarmY'		       		: Alarms,
        'avgSpeed'                  : avgSpeed
    }

    return render_template('help.html', **templateData)

@app.route("/log")
def log():
    logIp("log")
    logs = readLog()
    return logs

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8000, debug=False)
