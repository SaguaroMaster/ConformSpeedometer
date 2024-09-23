import gpiod
import time

RELAY_CH1 = 26
RELAY_CH2 = 20
RELAY_CH3 = 21

SENSOR_PIN = 18

switchTime = 0.1

chip = gpiod.Chip('gpiochip4')
RELAY_CH1_Line = chip.get_line(RELAY_CH1)
RELAY_CH2_Line = chip.get_line(RELAY_CH2)
RELAY_CH3_Line = chip.get_line(RELAY_CH3)

sensor_line = chip.get_line(SENSOR_PIN)


RELAY_CH1_Line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
RELAY_CH2_Line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
RELAY_CH3_Line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)

sensor_line.request(consumer="Sensor", type=gpiod.LINE_REQ_DIR_IN)

try:
   while True:
    '''
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
    
    '''

    sensor_state = sensor_line.get_value()
    print(sensor_state)

except KeyboardInterrupt:
    RELAY_CH1_Line.set_value(1)
    time.sleep(switchTime)
    RELAY_CH2_Line.set_value(1)
    time.sleep(switchTime)
    RELAY_CH3_Line.set_value(1)
    time.sleep(switchTime)

    RELAY_CH1_Line.release()
    RELAY_CH2_Line.release()
    RELAY_CH3_Line.release()