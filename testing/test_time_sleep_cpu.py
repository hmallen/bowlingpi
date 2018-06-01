import logging
import time

import psutil

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    test_delays = [0, 0.000001, 0.00001, 0.0001, 0.001]

    for test_time in test_delays:
        logger.debug('test_time: ' + str(test_time))

        start_time = time.time()
        print_start_time = start_time

        while (True):
            if (time.time() - print_start_time) > 1:
                logger.debug('CPU Usage: ' + str(psutil.cpu_percent()))

                print_start_time = time.time()

            if (time.time() - start_time) > 10:
                break

            time.sleep(test_time)
