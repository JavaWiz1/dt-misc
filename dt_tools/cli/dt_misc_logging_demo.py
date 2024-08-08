import dt_tools.logger.logging_helper as lh
import datetime
import time
import random

LOGGER = lh.logger

def demo():
    test1_log = "./test1.log"
    test2_log = "./test2.log"
    rotation=datetime.timedelta(seconds=10)
    retention= 5

    lh.configure_logger()
    lh.configure_logger(log_target=test1_log, log_level="DEBUG")
    lh.configure_logger(log_target=test2_log, log_level="TRACE",
                                    retention=retention, rotation=rotation)
    LOGGER.info('Begin demo...')
    LOGGER.info('')
    LOGGER.info('30 message with varying log levels will be sent to the logger.')
    LOGGER.info('Depending on configuration, each message will be routed to the appropriate logger(s)')
    LOGGER.info('Logger configuration:')
    LOGGER.info('  Console   : CRITICAL, ERROR, WARNING, INFO')
    LOGGER.info('  Test1.log : CRITICAL, ERROR, WARNING, INFO, DEBUG')
    LOGGER.info('  Test2.log : CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE')
    LOGGER.info('')
    LOGGER.info(f'NOTE: The {test2_log} file is set to rotate every 10 seconds and have 5 total versions.')
    LOGGER.info('')
    LOGGER.trace('This TRACE message should ONLY print in test2.log')
    LOGGER.debug('This DEBUG message should print in test1.log and test2.log')
    LOGGER.info('This INFO message should print on console and test1/2 log files')
    for i in range(30):
        log_level = random.choice(['TRACE','DEBUG','INFO','WARNING','ERROR','CRITICAL'])
        LOGGER.log(log_level, f'{i} {log_level} message')
        time.sleep(1)
    LOGGER.info('all done.')

if __name__ == "__main__":
    demo()
