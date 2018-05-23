import logging
import os
import sys
import time

import RPi.GPIO as GPIO

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pin_reference = GPIO.BOARD

gpio_pin = 7    # Physical pin number

switch_bounce = 200     # ms

gpio_event_detected = False


def callback_sensor_event(channel):
    #global gpio_event_detected

    logger.info('Callback function triggered by GPIO event detection.')

    logger.info('Channel Event: ' + str(channel))

    gpio_event_detected = True      # What is purpose of this variable? Won't reset to False...
    logger.debug('gpio_event_detected: ' + str(gpio_event_detected))

    #print('Event detected {0}'.format(channel))

    #curr_val = GPIO.input(channel)     # This is already handled by the event detection

    #print(' Value {0}'.format(curr_val))


def main():
    logger.debug('Entering main loop.')

    while True:
        # Wait for a GPIO event
        # 0.1s delay added to significantly reduce CPU load

        time.sleep(0.1)

    logger.debug('Leaving main loop.')


if __name__ == '__main__':
    try:
    GPIO.setmode(pin_reference)

    GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.add_event_detect(gpio_pin, GPIO.RISING, callback=callback_sensor_event, bouncetime=switch_bounce)

    main()  # Better to use "main" than "run" due to potential conflicts

    #if GPIO.event_detected(gpio_pin):  # You already have a callback function defined
        #gpio_event_detected = False

    except Exception as e:
        logger.exception('Exception raised.')
        logger.exception(e)

    except KeyboardInterrupt:
        logger.info('Exit signal received.')

        sys.exit()
