# External module imports
import gpiod
import time

# Pin Definitons:
ledPin = 37 # Broadcom pin 23 (P1 pin 16)

chip = gpiod.Chip('gpiochip4')
led_line = chip.get_line(ledPin)
led_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)


print("Here we go! Press CTRL+C to exit")
try:
    while 1:
        led_line.set_value(1)
        time.sleep(0.5)
        led_line.set_value(0)
        time.sleep(0.5)
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    led_line.release()
