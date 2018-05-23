import logging
import os
import sys
import time

import RPi.GPIO as GPIO

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

switch_bounce = 200 # ms

gpio_event_detected = False

gpio_pin = 7    # Physical pin number


def callback_sensor_event(pi_gpio_pin):
    #global gpio_event_detected

    gpio_event_detected = True

    print('Event detected {0}'.format(pi_gpio_pin))

    #curr_val = GPIO.input(pi_gpio_pin)     # This is already handled by the event detection

    #print(' Value {0}'.format(curr_val))


def main():
    while True:
        # Wait for a GPIO event
        # 0.1s delay added to significantly reduce CPU load

        time.sleep(0.1)


if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.add_event_detect(gpio_pin, GPIO.RISING, callback=callback_sensor_event, bouncetime=switch_bounce)

    main()  # Better to use "main" than "run" due to potential conflicts

    #if GPIO.event_detected(gpio_pin):  # You already have a callback function defined
        #gpio_event_detected = False
