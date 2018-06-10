from time import ctime, sleep, time
import os
import sys
from threading import Timer

import RPi.GPIO as GPIO

# ball_timer_2.py ---> 0.00001ms delay

#============================================
# USER CONFIGURATION
#============================================

SENSOR_CONFIG = {
	'EM'   : {'pi_gpio_pin':11,'active_hi_lo':"LO"}, # Machine on
	'EBDT' : {'pi_gpio_pin':12,'active_hi_lo':"LO"}, # Ball detect top
	'EBDB' : {'pi_gpio_pin':13,'active_hi_lo':"LO"}, # Ball detect bottom

	'OM'   : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
	'OBDT' : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
	'OBDB' : {'pi_gpio_pin':None,'active_hi_lo':"LO"}
}

# Add 200ms for switch bounce - Not sure if this is needed for our sensors
# This controls out quickly our GPIO respond to event changes
SWITCH_BOUNCE 		= 100 	# ms

#============================================
# Internal GLOBAL variables
#============================================

ACTIVE 					= True
INACTIVE 				= False
SENSOR_CURR_VALS		= {}

GPIO_EVENT_DETECTED 	= False

GROUNDED_TIMES = {
	'EBDT' : None,
	'EBDB' : None,
	'OBDT' : None,
	'OBDB' : None,
}

#==================================================
#
#==================================================
def info(msg):
	print("{} : {}".format(ctime(), msg))


def clear_curr_vals():
	global SENSOR_CONFIG
	global SENSOR_CURR_VALS

	for sensor_name in SENSOR_CONFIG:
		SENSOR_CURR_VALS[sensor_name] = 0


#==================================================
#
#==================================================
def real_sensor_val(sensor_name):
	'''
	Read the sensor value.  Takes into account configured active_hi_lo setting
	Return: ACTIVE|INACTIVE|None
	'''
	global SENSOR_CONFIG

	pi_gpio_pin 	= SENSOR_CONFIG[sensor_name]['pi_gpio_pin']
	active_hi_lo 	= SENSOR_CONFIG[sensor_name]['active_hi_lo'].upper()

	return_val = None

	if pi_gpio_pin == None:
		return_val = INACTIVE
	else:
		curr_val = GPIO.input(pi_gpio_pin)
		if active_hi_lo == "HI":
			if curr_val == GPIO.HIGH:
				return_val = ACTIVE
			else:
				return_val = INACTIVE
		elif active_hi_lo == "LO":
			if curr_val == GPIO.LOW:
				return_val = ACTIVE
			else:
				return_val = INACTIVE

	if SENSOR_CONFIG[sensor_name]['test_value']:
		return_val = SENSOR_CONFIG[sensor_name]['test_value']

	return return_val


def callback_sensor_event(pi_gpio_pin):
	'''
	This method gets called when there is a positive or negative edge on a sensor
	'''
	global GPIO_EVENT_DETECTED

	GPIO_EVENT_DETECTED = True


def init():
	clear_curr_vals()
	init_sensors()


def init_sensors():
	'''
	Initialize Pi GPIO based on SENSOR_CONFIG
	'''
	global SENSOR_CONFIG

	# This ensures we are using the Pi Board numbering
	# Other option here is GPIO.BCM - which will use the Broadcom chip numbering and is less portable
	GPIO.setmode(GPIO.BOARD)

	# Walk the sensors in the CONFIG variable
	for sensor_name in sorted(SENSOR_CONFIG):
		# Allow for us to mimic a test_value
		# Only used for debug
		if 'test_value' not in SENSOR_CONFIG[sensor_name]:
			SENSOR_CONFIG[sensor_name]['test_value'] = None

		# Get the Pi pin
		pi_gpio_pin = SENSOR_CONFIG[sensor_name]['pi_gpio_pin']

		if pi_gpio_pin == None:
			info("Sensor {} is not configured to a Pi GPIO pin".format(sensor_name))
		else:
			# Sensor is connected to a pin

			# Setup the Pi pin based on active HI/LO state
			active_hi_lo = SENSOR_CONFIG[sensor_name]['active_hi_lo'].upper()
			info("Configuring sensor [{}] Pi GPIO pin [{}] to be active [{}]".format(sensor_name, pi_gpio_pin, active_hi_lo))

			if active_hi_lo == "LO":
				# When sensor active it drives 0 -- Connected to ground
				GPIO.setup(pi_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			elif active_hi_lo == "HI":
				# When sensor active it drives HI -- Connected to VCC
				GPIO.setup(pi_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			else:
				sys.exit("Error - Sensor {} does not have a valid HI/LO active state".format(sensor_name))

			# Configure a callback method
			GPIO.add_event_detect(pi_gpio_pin, GPIO.BOTH, callback=callback_sensor_event, bouncetime=SWITCH_BOUNCE)


def calc_ball_speed():
	'''
	Get grounded times and calculate ball speed
	'''
	global SENSOR_CURR_VALS
	global GROUNDED_TIMES

	EM		= SENSOR_CURR_VALS['EM']
	EBDT	= SENSOR_CURR_VALS['EBDT']
	EBDB	= SENSOR_CURR_VALS['EBDB']

	OM		= SENSOR_CURR_VALS['OM']
	OBDT	= SENSOR_CURR_VALS['OBDT']
	OBDB	= SENSOR_CURR_VALS['OBDB']

	prt_curr_vals()		# Move to below timer functions?

	# Grounded timer for ball speed. Moved to top of loop for time priority.
	# Ball Grounded Timers
	curr_time = time()
	if EM:
		if EBDT:
			GROUNDED_TIMES['EBDT'] = curr_time

		else:
			if GROUNDED_TIMES['EBDT']:
				diff_time = curr_time - GROUNDED_TIMES['EBDT']

				GROUNDED_TIMES['EBDT'] = None

				velocity = (8.5 / diff_time) * (3600) / (63360)

				info_msg("EBDT: Time difference = {} | Velocity = {} mph".format(diff_time, velocity))

		if EBDB:
			GROUNDED_TIMES['EBDB'] = curr_time

		else:
			if GROUNDED_TIMES['EBDB']:
				diff_time = curr_time - GROUNDED_TIMES['EBDB']

				GROUNDED_TIMES['EBDB'] = None

				velocity = (8.5 / diff_time) * (3600) / (63360)

				info_msg("EBDB: Time difference = {} | Velocity = {} mph".format(diff_time, velocity))

	if OM:
		if OBDT:
			GROUNDED_TIMES['OBDT'] = curr_time

		else:
			if GROUNDED_TIMES['OBDT']:
				diff_time = curr_time - GROUNDED_TIMES['OBDT']

				GROUNDED_TIMES['OBDT'] = None

				velocity = (8.5 / diff_time) * (3600) / (63360)

				info_msg("OBDT: Time difference = {} | Velocity = {} mph".format(diff_time, velocity))

		if OBDB and not EM:
			GROUNDED_TIMES['OBDB'] = curr_time

		else:
			if GROUNDED_TIMES['OBDB']:
				diff_time = curr_time - GROUNDED_TIMES['OBDB']

				GROUNDED_TIMES['OBDB'] = None

				velocity = (8.5 / diff_time) * (3600) / (63360)

				info_msg("OBDB: Time difference = {} | Velocity = {} mph".format(diff_time, velocity))


def update_curr_vals():
	global SENSOR_CURR_VALS

	for sensor_name in SENSOR_CONFIG:
		SENSOR_CURR_VALS[sensor_name] = GET_SENSOR_VAL(sensor_name)


def prt_curr_vals():
	global SENSOR_CURR_VALS

	info("=========================================")
	info("EM[{}] EBDT[{}] EBDB[{}]".format(
			SENSOR_CURR_VALS['EM']*1
		,	SENSOR_CURR_VALS['EBDT']*1
		,	SENSOR_CURR_VALS['EBDB']*1
		))
	info("OM[{}] OBDT[{}] OBDB[{}]".format(
			SENSOR_CURR_VALS['OM']*1
		,	SENSOR_CURR_VALS['OBDT']*1
		,	SENSOR_CURR_VALS['OBDB']*1
		))


def run():
	'''
	Main loop that reacts to sensor events
	'''
	global SENSOR_CONFIG
	global SENSOR_CURR_VALS
	global GPIO_EVENT_DETECTED

	print('Waiting for ball to be thrown...')

	while True:
		try:
			# Wait for a GPIO event
			# Hopefully this becomes less CPU intense
			if GPIO_EVENT_DETECTED:
				# Turn event off to show that we recognize the new event
				GPIO_EVENT_DETECTED = False

				# Read all sensor values
				# SENSOR_CURR_VALS
				#	EM : ACTIVE|INACTIVE|None...
				update_curr_vals()

				# Calculate ball speed
				calc_ball_speed()

			# Added else to skip sleep if event detected, allowing immediate recheck
			else:
				sleep(0.00001)	# Added 0.00001ms (0.01us) TEST delay to reduce CPU load

		except Exception as e:
			print('Exception raised in run(): ', e)

		except KeyboardInterrupt:
			raise


#==================================================
# MAIN
#==================================================
if __name__ == "__main__":
	GET_SENSOR_VAL = real_sensor_val	# Create alias for sensor value function

	print('Initializing sensors.')

	init()

	print('Starting main program.')

	try:
		run()	# Run main program

	except Exception as e:
		print('Exception: ', e)

	except KeyboardInterrupt:
		print('Exit signal received.')

	finally:
		print('Cleaning-up GPIO pin states.')

		GPIO.cleanup()

		print('Done.')

		sys.exit()
