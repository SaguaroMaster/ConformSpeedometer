import gpiozero as GPIO
import time
import sqlite3

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

switchTime = 0.1
pulseCount = 0
samplePeriod = 60 #seconds
wheelCircumference = 0.25 #meter
time_old = time.time()

relay1 = GPIO.LED(RELAY_CH1)
sensor = GPIO.Button(SENSOR_PIN, pull_up = None, bounce_time = 0.05, active_state = True)

def pulseCallback(self):
   global pulseCount
   global speed
   pulseCount = pulseCount + 1
   time1 = time.time()
   speed = (1 / (time1 - time_old)) * wheelCircumference
   time_old = time1
   print(speed)


sensor.when_released = pulseCallback

conn = sqlite3.connect('Database.db') #Create database if doesnt exist, otherwise just connect

try:
   while True:
      if time.time() > time1+samplePeriod:
         time1 = time.time()
         time.sleep(100)

except KeyboardInterrupt:
   print("Terminating program...")