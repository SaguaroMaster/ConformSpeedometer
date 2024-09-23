import gpiozero as GPIO
import time
import sqlite3

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21
SENSOR_PIN = 6

switchTime = 0.1

relay1 = GPIO.LED(RELAY_CH1)
sensor = GPIO.Button(SENSOR_PIN, pull_up = None, bounce_time= 50)

def impulseCallback(self):
   print("PUUUUUUUUUUUULSE")

sensor.when_released = impulseCallback

try:
   while True:
      time.wait(100)

except KeyboardInterrupt:
   print("Terminating program...")