from time import sleep, ctime
import os
import sys
from threading import Timer

#============================================
# USER CONFIGURATION
#============================================

SENSOR_CONFIG = {
	'EM'   : {'pi_gpio_pin':11,'active_hi_lo':"LO"}, # Machine on
	'EBDT' : {'pi_gpio_pin':12,'active_hi_lo':"LO"}, # Ball detect top
	'EBDB' : {'pi_gpio_pin':13,'active_hi_lo':"LO"}, # Ball detect bottom
	'ESDI' : {'pi_gpio_pin':15,'active_hi_lo':"LO"}, # Sweep down and in
	'ESDU' : {'pi_gpio_pin':16,'active_hi_lo':"LO"}, # Sweep coming out and up

	'OM'   : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
	'OBDT' : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
	'OBDB' : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
	'OSDI' : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
	'OSDU' : {'pi_gpio_pin':None,'active_hi_lo':"LO"},
}

TIMEOUTS				= {
	'ESDI'			: 2	 ,	# seconds
	'ESDU'			: 4  ,	# seconds
	'OSDI'			: 2  ,  # seconds
	'OSDU'			: 4  ,  # seconds
	'BALL_RETURN'	: 5	 ,	# 5 seconds
}

MYSQL_INFO = {
	'host' 		: 'localhost',
	'database'	: 'sensors'  ,
	'user'		: 'pi'		 ,
	'password'	: 'raspberry',
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

ERROR_MSGS				= []

ESDI_TIMER				= None
ESDU_TIMER				= None
EBALL_TIMER				= None
OSDI_TIMER				= None
OSDU_TIMER				= None
OBALL_TIMER				= None

TIMERS					= {
	'ESDI'			: [],
	'ESDU'  		: [],
	'OSDI'			: [],
	'OSDU'  		: [],
	'BALL_RETURN'	: [],
}

ERRORS					= {
	'ESDI'  		: False,
	'ESDU'			: False,
	'OSDI'			: False,
	'OSDU'			: False,
	'BALL_RETURN'	: False,
}

COUNTS					= {
	'BALL_COUNT'	: 0
}
BALL_RETURN_ERR_MODE	= False

MYSQL					= None

#==================================================
#
#==================================================

def info(msg):
	print("{} : {}".format(ctime(),msg))

def error_msg(msg):
	global ERROR_MSGS
	global ERRORS
	msg = "{} : ** ERROR ** {}".format(ctime(),msg)
	print(msg)
	ERROR_MSGS.append(msg)

def clear_counts(type=None):
	global COUNTS
	if type:
		COUNTS[type] = 0
	else:
		for name in COUNTS:
			COUNTS[name] = 0

def clear_curr_vals():
	global SENSOR_CONFIG
	global SENSOR_CURR_VALS

	for sensor_name in SENSOR_CONFIG:
		SENSOR_CURR_VALS[sensor_name] = 0

def clear_errors():
	global ERRORS
	for error in ERRORS:
		ERRORS[error] = False

def clear_timers():
	global TIMERS
	for type in TIMERS:
		TIMERS[type] = []

#==================================================
# Timeout methods
# Used for dealing with variable timeouts
#==================================================

def timeout_general(**kwargs):
	global ERRORS

	error_type = kwargs['error_type']
	msg		   = kwargs['error_msg']

	#info("** TIMEOUT ** [{}]".format(error_type))

	# Log the error message
	error_msg(msg)

	# Set the error flag
	ERRORS[error_type] = True

	# Print the errors
	info("ERROR_STATUS: {}".format(ERRORS))

	# Stop the timer
	_timer_stop(error_type)

def _timer_start(type=None,**kwargs):
	global TIMERS
	global TIMEOUTS

	# Check if user provided timeout in seconds
	timeout_sec = TIMEOUTS[type]
	if 'timeout_sec' in kwargs:
		timeout_sec = kwargs['timeout_sec']
		del kwargs['timeout_sec']

	# Information passed to timeout function
	args = {
		'error_type' : type,
		'error_msg'  : ""
	}

	for k in kwargs:
		args[k] = kwargs[k]

	# Create the timer and START it
	timer = Timer(timeout_sec,timeout_general,[],args)
	info("Starting {} timer {} for [{}] seconds".format(type,timer,timeout_sec))
	timer.start()

	# Add the timer to the appropriate list
	TIMERS[type].append(timer)
	return timer

def _timer_stop(type=None,**kwargs):
	global TIMERS
	global ERRORS

	# Default to stopping the first timer [0] unless told otherwise
	index = 0
	if 'index' in kwargs:
		index = kwargs['index']
		del kwargs['index']

	timer = None
	if TIMERS[type]:
		timer = TIMERS[type][index]
		if not ERRORS[type]:
			info("Canceling {} active timer {}".format(type,timer))

		timer.cancel()
		del TIMERS[type][index]

	return timer

def _timer_stop_all(type=None):
	global TIMERS

	while TIMERS[type]:
		_timer_stop(type)

def _has_timer(type=None):
	global TIMERS
	if type not in TIMERS:
		return False
	elif TIMERS[type]:
		return True
	else:
		return False

def _get_timer(type=None,index=0):
	global TIMERS
	timer = None
	if _has_timer(type):
		timer = TIMERS[index]
	return timer

#==================================================
#
#==================================================
def mysql_connect():
	global MYSQL
	global MYSQL_INFO

	info("Connecting to mysql [{}.{}]...".format(MYSQL_INFO['host'],MYSQL_INFO['database']))

	try:
		MYSQL = mysql.connector.connect(	user=MYSQL_INFO['user']
										, 	password=MYSQL_INFO['password']
										, 	database=MYSQL_INFO['database']
										,	host=MYSQL_INFO['host']
										)
		info("Connection established")
	except:
		info("Unable to establish connection to MYSQL server")
		MYSQL = None

def mysql_insert_msg(msg):
	global MYSQL

	if MYSQL == None:
		return

	cursor = MYSQL.cursor()

	add_msg = ("INSERT INTO msgs "
              "(msg) "
              "VALUES (\'{}\')".format(msg))

	cursor.execute(add_msg)
	MYSQL.commit()
	cursor.close()

def flush_errors():
	global ERROR_MSGS
	while ERROR_MSGS:
		msg = ERROR_MSGS.pop()
		mysql_insert_msg(msg)
	ERROR_MSGS = []

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
	clear_counts()
	clear_curr_vals()
	clear_errors()
	init_sensors()
	mysql_connect()

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
			SENSOR_CONFIG[sensor_name]['test_value']   = None

		# Get the Pi pin
		pi_gpio_pin = SENSOR_CONFIG[sensor_name]['pi_gpio_pin']

		if pi_gpio_pin == None:
			info("Sensor {} is not configured to a Pi GPIO pin".format(sensor_name))
		else:
			# Sensor is connected to a pin

			# Setup the Pi pin based on active HI/LO state
			active_hi_lo = SENSOR_CONFIG[sensor_name]['active_hi_lo'].upper()
			info("Configuring sensor [{}] Pi GPIO pin [{}] to be active [{}]".format(sensor_name,pi_gpio_pin,active_hi_lo))

			if active_hi_lo == "LO":
				# When sensor active it drives 0 -- Connected to ground
				GPIO.setup(pi_gpio_pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
			elif active_hi_lo == "HI":
				# When sensor active it drives HI -- Connected to VCC
				GPIO.setup(pi_gpio_pin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
			else:
				sys.exit("Error - Sensor {} does not have a valid HI/LO active state".format(sensor_name))

			# Configure a callback method
			GPIO.add_event_detect(pi_gpio_pin,GPIO.BOTH,callback=callback_sensor_event,bouncetime=SWITCH_BOUNCE)

def run_specification():
	'''
	Run error checks
	Run counter updates
	'''
	global SENSOR_CURR_VALS
	global ERROR_MSGS

	global COUNTS
	global TIMERS
	global TIMEOUTS
	global ERRORS

	EM 		= SENSOR_CURR_VALS['EM']
	ESDI 	= SENSOR_CURR_VALS['ESDI']
	ESDU	= SENSOR_CURR_VALS['ESDU']
	EBDT	= SENSOR_CURR_VALS['EBDT']
	EBDB	= SENSOR_CURR_VALS['EBDB']

	OM 		= SENSOR_CURR_VALS['OM']
	OSDI 	= SENSOR_CURR_VALS['OSDI']
	OSDU	= SENSOR_CURR_VALS['OSDU']
	OBDT	= SENSOR_CURR_VALS['OBDT']
	OBDB	= SENSOR_CURR_VALS['OBDB']

	prt_curr_vals()

	if ERRORS['BALL_RETURN']:
		COUNTS['BALL_COUNT'] = 0
		_timer_stop_all('BALL_RETURN')

	# Even side
	if EM:
		# Sweep down and in
		if ESDI:
			# Start a timer if we haven't already started one and we are not currently in error mode
			if not _has_timer('ESDI') and not ERRORS['ESDI']:
				_timer_start('ESDI',error_msg="E - Sweep Down")
		else:
			_timer_stop_all('ESDI')
			ERRORS['ESDI'] = False

		# Sweep out and up
		if ESDU:
			# Start a timer if we haven't already started one and we are not currently in error mode
			if not _has_timer('ESDU') and not ERRORS['ESDU']:
				_timer_start('ESDU',error_msg="E - Pin Jam")
		else:
			_timer_stop_all('ESDU')
			ERRORS['ESDU'] = False

		# Ball thrown
		if EBDT:

			if ESDI or ESDU:
				error_msg("E - Ball thrown at sweep - Dead ball")
			else:
				# Seems to be a valid ball
				# Count it
				# Start a Ball return timer
				_timer_start('BALL_RETURN',error_msg="Ball Return")
				ERRORS['BALL_RETURN'] = False
				COUNTS['BALL_COUNT'] += 1
	else:
		if EBDT:
			error_msg("E - Ball thrown down off lane")

		_timer_stop_all('ESDI')
		_timer_stop_all('ESDU')
		ERRORS['ESDI'] = False
		ERRORS['ESDU'] = False

	if OM:
		if OSDI:
			# Start a timer if we haven't already started one and we are not currently in error mode
			if not _has_timer('OSDI') and not ERRORS['OSDI']:
				_timer_start('OSDI',error_msg="O - Sweep Down")
		else:
			_timer_stop_all('OSDI')
			ERRORS['OSDI'] = False

		if OSDU:
			# Start a timer if we haven't already started one and we are not currently in error mode
			if not _has_timer('OSDU') and not ERRORS['OSDU']:
				_timer_start('OSDU',error_msg="O - Pin Jam")
		else:
			_timer_stop_all('OSDU')
			ERRORS['OSDU'] = False

		if OBDT:

			if OSDI or OSDU:
				error_msg("O - Ball thrown at sweep - Dead ball")
			else:
				_timer_start('BALL_RETURN',error_msg="Ball return")
				ERRORS['BALL_RETURN'] = False
				COUNTS['BALL_COUNT'] += 1
	else:
		if OBDT:
			error_msg("O - Ball thrown down off lane")

		_timer_stop_all('OSDI')
		_timer_stop_all('OSDU')
		ERRORS['OSDI'] = False
		ERRORS['OSDU'] = False

	# Ball return sensor is shared
	if (EBDB and OBDB) or EBDB or OBDB:
		# Stop any timer associated with ball return
		# This will only stop the first timer
		#   If there are multiple timers active they keep going
		_timer_stop('BALL_RETURN')

		# Decrement ball return if not in error state
		if not ERRORS['BALL_RETURN']:
			COUNTS['BALL_COUNT'] -= 1

	# Any negative counts
	if COUNTS['BALL_COUNT'] < 0:
		error_msg("Ball Return - Ball count < 0")
		ERRORS['BALL_RETURN'] = True

	# ?? - This just says we threw too many balls, does it need to be a BALL_RETURN error?
	# 		Don't we still expect to get the balls back?
	if EM and OM:
		if EBDT or OBDT:
			if COUNTS['BALL_COUNT'] > 2:
				error_msg("Ball Count > 2 - Too many balls thrown")
	elif EM and EBDT:
		if COUNTS['BALL_COUNT'] > 1:
			error_msg("E - Ball Count > 1 - Too many balls thrown")
	elif OM and OBDT:
		if COUNTS['BALL_COUNT'] > 1:
			error_msg("O - Ball Count > 1 - Too many balls thrown")

	if not EM and not OM:
		# No machines on
		clear_counts()
		clear_errors()
		clear_timers()

	info("COUNTS: {}".format(COUNTS))

def update_curr_vals():
	global SENSOR_CURR_VALS
	for sensor_name in SENSOR_CONFIG:
		SENSOR_CURR_VALS[sensor_name] = GET_SENSOR_VAL(sensor_name)

def prt_curr_vals():
	global SENSOR_CURR_VALS

	info("=========================================")
	info("EM[{}] EBDT[{}] EBDB[{}] ESDI[{}] ESDU[{}]".format(
			SENSOR_CURR_VALS['EM']*1
		,	SENSOR_CURR_VALS['EBDT']*1
		,	SENSOR_CURR_VALS['EBDB']*1
		,	SENSOR_CURR_VALS['ESDI']*1
		,	SENSOR_CURR_VALS['ESDU']*1
		))
	info("OM[{}] OBDT[{}] OBDB[{}] OSDI[{}] OSDU[{}]".format(
			SENSOR_CURR_VALS['OM']*1
		,	SENSOR_CURR_VALS['OBDT']*1
		,	SENSOR_CURR_VALS['OBDB']*1
		,	SENSOR_CURR_VALS['OSDI']*1
		,	SENSOR_CURR_VALS['OSDU']*1
		))

def run():
	'''
	This is the main loop
	'''
	global SENSOR_CONFIG
	global SENSOR_CURR_VALS
	global GPIO_EVENT_DETECTED
	global ERROR_MSGS

	while True:

		# Wait for a GPIO event
		# Hopefully this becomes less CPU intense
		if GPIO_EVENT_DETECTED:

			# Turn event off to show that we recognize the new event
			GPIO_EVENT_DETECTED = False

			# Read all sensor values
			# SENSOR_CURR_VALS
			#	EM : ACTIVE|INACTIVE|None...
			update_curr_vals()

			# Run error checks and counter updates
			run_specification()

		# Flush ERRORS
		flush_errors()

		sleep(0.0001)	# Added 0.1ms delay to reduce CPU load

#==================================================
# MAIN
#
#==================================================
if __name__ == "__main__":
	import RPi.GPIO as GPIO
	import mysql.connector

	GET_SENSOR_VAL = real_sensor_val	# Create alias for sensor value function

	init()	# Initialize everything

	run()	# Run main program
