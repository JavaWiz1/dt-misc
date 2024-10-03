"""
This module demonstrates the Weather module functionality.


"""

from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper

    
def demo():
    OSHelper.enable_ctrl_c_handler()
    LOGGER.info('-'*80)
    LOGGER.info('dt_misc_weather demo')
    LOGGER.info('-'*80)

    LOGGER.warning('TBD - Demo not ready...')

    LOGGER.info('')
    LOGGER.info('Demo complete.')

if __name__ == "__main__":
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, brightness=False)
    demo()
