# External module imports
import RPi.GPIO as GPIO
import time

# Pin Definitons:
ledPin = 40 # Broadcom pin 23 (P1 pin 16)


# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(ledPin, GPIO.OUT) # LED pin set as output
GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up

# Initial state for LEDs:
GPIO.output(ledPin, GPIO.LOW)

print("Here we go! Press CTRL+C to exit")
try:
    while 1:
        GPIO.output(ledPin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(ledPin, GPIO.LOW)
        time.sleep(0.5)
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    pwm.stop() # stop PWM
    GPIO.cleanup() # cleanup all GPIO
