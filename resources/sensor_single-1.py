import os
import sys
import time

# Add 200ms for switch bounce - Not sure if this is needed for our sensors
# This controls out quickly our GPIO respond to event changes
SWITCH_BOUNCE 		= 200 	# ms

GPIO_EVENT_DETECTED = False

GPIO_PIN = 7

def callback_sensor_event(pi_gpio_pin):
	'''
	This method gets called when there is a positive or negative edge on a sensor
	'''
	global GPIO_EVENT_DETECTED
	GPIO_EVENT_DETECTED = True

	print("Event detected {} ".format(pi_gpio_pin))
	curr_val = GPIO.input(pi_gpio_pin)
	print(" Value {}".format(curr_val))

def run():
	'''
	This is the main loop
	'''
	global GPIO_EVENT_DETECTED
	global GPIO_PIN

	# This ensures we are using the Pi Board numbering
	# Other option here is GPIO.BCM - which will use the Broadcom chip numbering and is less portable
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(GPIO_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(GPIO_PIN,GPIO.RISING,callback=callback_sensor_event,bouncetime=SWITCH_BOUNCE)

	while True:
		# Wait for a GPIO event
		# Hopefully this becomes less CPU intense
		if GPIO_EVENT_DETECTED:

			# Turn event off to show that we recognize the new event
			GPIO_EVENT_DETECTED = False

			time.sleep(0.1)

#==================================================
# MAIN
#
#==================================================
if __name__ == "__main__":
	import RPi.GPIO as GPIO

	run()
