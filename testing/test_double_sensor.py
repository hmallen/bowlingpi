import logging
import os
import sys
import time

import RPi.GPIO as GPIO

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pin_reference = GPIO.BOARD  # This sets everything to use PHYSICAL pin numbers. Can be changed for wiringPi or BCM numbers, if required.

sensor_one = 7    # Physical pin numbering
sensor_two = 11    # Physical pin numbering

switch_bounce = 200     # ms

#global gpio_event_detected
gpio_event_detected = False     # Is this boolean necessary?


def callback_sensor_event(channel):
    #global gpio_event_detected

    logger.info('Callback function triggered by GPIO event detection.')

    logger.info('Channel Event: ' + str(channel))

    gpio_event_detected = True      # What is purpose of this variable? Won't reset to False...
    logger.debug('gpio_event_detected: ' + str(gpio_event_detected))

    ## None of the code below is necessary, since it's handled by callback function itself
    #print('Event detected {0}'.format(channel))

    #curr_val = GPIO.input(channel)     # This is already handled by the event detection

    #print(' Value {0}'.format(curr_val))


def main():
    global gpio_event_detected

    logger.debug('Entering main loop.')

    while True:
        # Things to do while waiting for a GPIO event

        if gpio_event_detected == True:
            gpio_event_detected = False     # Reset boolean that was set to true on event detection

        time.sleep(0.1)     # 0.1s delay added to SIGNIFICANTLY reduce CPU load

    logger.debug('Leaving main loop.')


if __name__ == '__main__':
    try:
        # Set mode to reference PHYSICAL pin numbers as opposed to BCM or wiringPi
        GPIO.setmode(pin_reference)

        # Setup pins as inputs with pulldown resistors
        GPIO.setup(sensor_one, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(sensor_two, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Add callback functions for pins, triggered by rising-edge detection
        GPIO.add_event_detect(sensor_one, GPIO.RISING, callback=callback_sensor_event, bouncetime=switch_bounce)
        GPIO.add_event_detect(sensor_two, GPIO.RISING, callback=callback_sensor_event, bouncetime=switch_bounce)

        # Enter main loop to begin persistent monitoring functions (may want to switch to multiprocessing or threading)
        main()  # Better to use "main" than "run" due to potential conflicts with imported modules

        #if GPIO.event_detected(sensor_one):  # You already have a callback function defined, so this isn't required
            #gpio_event_detected = False

    except Exception as e:
        logger.exception('Exception raised.')
        logger.exception(e)

    except KeyboardInterrupt:
        logger.info('Exit signal received.')

        sys.exit()
