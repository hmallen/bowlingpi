import logging
import os
import sys
import time

import RPi.GPIO as GPIO

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pin_reference = GPIO.BOARD

gpio_pin_upper = 7    # Physical pin number
gpio_pin_lower = 11

switch_bounce = 200     # ms


def callback_sensor_event(channel):
    logger.info('Channel Event: ' + str(channel))


def main():
    while (True):
        # Do something here

        time.sleep(0.001)

    logger.debug('Leaving main loop.')


if __name__ == '__main__':
    try:
        GPIO.setmode(pin_reference)

        #GPIO.setup(gpio_pin_upper, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup([gpio_pin_upper, gpio_pin_lower], GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Sensors actually driven low when activated, not high

        #GPIO.setup(gpio_pin_lower, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(gpio_pin_upper,
                              GPIO.BOTH,
                              callback=callback_sensor_event,
                              bouncetime=switch_bounce)

        GPIO.add_event_detect(gpio_pin_lower,
                              GPIO.BOTH,
                              callback=callback_sensor_event,
                              bouncetime=switch_bounce)

        main()

    except Exception as e:
        logger.exception('Exception raised.')
        logger.exception(e)

    except KeyboardInterrupt:
        logger.info('Exit signal received.')

        sys.exit()
