import gpiod
import time

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21

switchTime = 0.1

chip = gpiod.Chip('gpiochip4')
RELAY_CH1_Line = chip.get_line(RELAY_CH1)
RELAY_CH2_Line = chip.get_line(RELAY_CH2)
RELAY_CH3_Line = chip.get_line(RELAY_CH3)

RELAY_CH1_Line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
RELAY_CH2_Line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
RELAY_CH3_Line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)

try:
   while True:
       RELAY_CH1_Line.set_value(1)
       time.sleep(switchTime)
       RELAY_CH2_Line.set_value(1)
       time.sleep(switchTime)
       RELAY_CH3_Line.set_value(1)
       time.sleep(switchTime)

       RELAY_CH1_Line.set_value(0)
       time.sleep(switchTime)
       RELAY_CH2_Line.set_value(0)
       time.sleep(switchTime)
       RELAY_CH3_Line.set_value(0)
       time.sleep(switchTime)
finally:
   led_line.release()