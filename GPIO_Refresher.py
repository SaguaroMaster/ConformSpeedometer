import gpiozero as GPIO
import time
import sqlite3

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

switchTime = 0.1

relay1 = GPIO.LED(RELAY_CH1)
sensor = GPIO.Button(SENSOR_PIN, pull_up = None, bounce_time = 0.05, active_state = True)

def impulseCallback(self):
   print("PUUUUUUUUUUUULSE")

sensor.when_released = impulseCallback

conn = sqlite3.connect('Database.db')

try:
   while True:
      time.sleep(100)

except KeyboardInterrupt:
   print("Terminating program...")