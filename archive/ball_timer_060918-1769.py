import logging
from multiprocessing import Process
import os
import sys
import time

import RPi.GPIO as GPIO

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pin_reference = GPIO.BOARD

gpio_pin_first = 7    # Physical pin number
gpio_pin_second = 11

switch_bounce = 200     # ms

timer_active = False

sensor_first_time = 0
sensor_second_time = 0


def callback_sensor_event(channel_event):
    global timer_active
    global sensor_first_time, sensor_second_time

    logger.debug('channel_event: ' + str(channel_event))

    if timer_active == False:
        if channel_event == gpio_pin_first:
            sensor_first_time = time.time()

            timer_active = True

        else:
            logger.error('Second sensor activated before first.')

    else:
        if channel_event == gpio_pin_second:
            sensor_second_time = time.time()

            timer_active = False

            travel_time = sensor_second_time - sensor_first_time
            logger.info('Ball Travel Time: ' + "{:.8f}".format(travel_time) + ' seconds.')

        else:
            logger.error('Expected second sesor to be activated. Resetting timer.')

            timer_active = False


def main():
    while (True):
        # Do somethine there

        time.sleep(0.001)

    logger.debug('Leaving main loop.')


if __name__ == '__main__':
    try:
        GPIO.setmode(pin_reference)

        #GPIO.setup(gpio_pin_first, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup([gpio_pin_first, gpio_pin_second], GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Sensors actually driven low when activated, not high

        #GPIO.setup(gpio_pin_second, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(gpio_pin_first,
                              GPIO.BOTH,
                              callback=callback_sensor_event,
                              bouncetime=switch_bounce)

        GPIO.add_event_detect(gpio_pin_second,
                              GPIO.BOTH,
                              callback=callback_sensor_event,
                              bouncetime=switch_bounce)

        #main()
        ball_timer = Process(target=main, args=(,))

        # Start the main loop
        ball_timer.start()

        # Join the main loop, keeping program running until it is complete
        ball_timer.join()

    except Exception as e:
        logger.exception('Exception raised.')
        logger.exception(e)

    except KeyboardInterrupt:
        logger.info('Exit signal received.')

        #sys.exit()

    finally:
        GPIO.cleanup([gpio_pin_first, gpio_pin_second])
