"""
This module demonstrates the logging_helper modules features.

- Console logging
- File logging
- Log colorization

"""

import datetime
import random
import time

from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh

@lh.logger_wraps(level='INFO')
def demo_logger_wraps():
    LOGGER.info('Inside the demo_logger_wraps_function')
    time.sleep(1)

@lh.timer_wraps(level='INFO')
def demo_timer_wraps():
    LOGGER.info('Inside the demo_timer_wraps_function')
    delay = time.time() % 10
    time.sleep(delay)

def demo():
    test1_log = "./test1.log"
    test2_log = "./test2.log"
    rotation=datetime.timedelta(seconds=10)
    retention= 5

    l_handle = lh.configure_logger(log_level="TRACE")
    LOGGER.info('-'*40)
    LOGGER.info('dt_misc_logging_demo')
    LOGGER.info('-'*40)
    LOGGER.info('')
    LOGGER.info('log to console demo...')
    LOGGER.info('')

    lh.set_log_levels_brighness(True)
    LOGGER.info('')
    LOGGER.info('Log Levels BRIGHTNESS enabled')
    LOGGER.info('-----------------------------')
    lh._print_log_level_definitions()
    time.sleep(5)

    lh.set_log_levels_brighness(False)
    LOGGER.info('')
    LOGGER.info('Log Levels BRIGHTNESS disabled')
    LOGGER.info('------------------------------')
    lh._print_log_level_definitions()
    input('\nPress Enter to continue... ')

    LOGGER.info('')
    
    h_console = lh.configure_logger(log_level="TRACE", log_handle=l_handle, brightness=False)
    h_test1   = lh.configure_logger(log_target=test1_log, log_level="DEBUG")
    h_test2   = lh.configure_logger(log_target=test2_log, log_level="INFO",
                                    retention=retention, rotation=rotation)   
    LOGGER.info('Multiple logger test (console and 2 files)') 
    LOGGER.info('------------------------------------------')
    LOGGER.info('- 30 message with random log levels will be sent to the logger.')
    LOGGER.info('- Based on configuration, each message will be routed to the appropriate logger(s)')
    LOGGER.info('')
    LOGGER.info('Logger configuration:')
    LOGGER.info('  Console   : CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE')
    LOGGER.info('  Test1.log : CRITICAL, ERROR, WARNING, INFO, DEBUG')
    LOGGER.info('  Test2.log : CRITICAL, ERROR, WARNING, INFO')
    LOGGER.info('')
    LOGGER.info('NOTE: ')
    LOGGER.info('- The Console will receive ALL log messages')
    LOGGER.info(f'- The {test1_log} file will get DEBUG level and above.')
    LOGGER.info(f'- The {test2_log} file will get INFO level and above.')
    LOGGER.info(f'- The {test2_log} file is set to rotate every 10 seconds and have 5 total versions.')
    time.sleep(3)
    LOGGER.info('')
    LOGGER.trace('This TRACE message should ONLY print on Console')
    LOGGER.debug('This DEBUG message should print in test1.log and Console')
    LOGGER.info('This INFO message should print on ALL log outputs')
    print('')
    for i in range(31):
        log_level = random.choice(['TRACE','DEBUG','INFO','WARNING','ERROR','CRITICAL'])
        LOGGER.log(log_level, f'message {i:2} {log_level}')
        time.sleep(.25)

    print('Removing file handlers, resetting console to debug format.')
    LOGGER.remove(h_test1)
    LOGGER.remove(h_test2)
    # Reset console handler
    h_console = lh.configure_logger(log_level="INFO", log_format=lh.DEFAULT_DEBUG_LOGFMT, log_handle=h_console, brightness=False)
    LOGGER.info('')
    LOGGER.info('decorator: logger_wraps()')
    demo_logger_wraps()
    LOGGER.info('')
    LOGGER.info('decorator: timer_wraps()')
    demo_timer_wraps()
    h_console = lh.configure_logger(log_level="INFO", log_handle=h_console, brightness=False)
    LOGGER.info('')
    LOGGER.success('logging demo complete.')
    input('\nPress Enter to continue... ')
    LOGGER.remove(h_console)
    
if __name__ == "__main__":
    demo()
