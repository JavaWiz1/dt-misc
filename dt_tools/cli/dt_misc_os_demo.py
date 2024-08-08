from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper


def demo():
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, log_level="DEBUG")
    LOGGER.info('Determine OS:')
    if OSHelper.is_raspberrypi():
        LOGGER.info('  Running on Raspberry Pi')
    if OSHelper.is_linux():
        LOGGER.info('  Running on Linux')
    if OSHelper.is_windows():
        LOGGER.info('  Running on Windows')

    LOGGER.info('')
    LOGGER.info('Check if Executable is available:')
    LOGGER.info(f'  gitx: {OSHelper.is_executable_available("gitx")}')
    LOGGER.info(f'  git:  {OSHelper.is_executable_available("git")}')
    if OSHelper.is_windows():
        LOGGER.info('')
        input('Press ENTER to Continue for Admin Check')
        LOGGER.info('')
        # LOGGER.info('Admin Check:')
        if OSHelper.is_windows_admin():
            LOGGER.info('  ****************************************')
            LOGGER.info('  ** Windows admin privileges in effect **')
            LOGGER.info('  ****************************************')
            LOGGER.info('')
            input('Press Enter to continue...')        
        else:
            LOGGER.info('  Not Admin, Elevate privileges')
            if OSHelper.elevate_to_admin():
                LOGGER.info('  - New prompt Shelled as admin')
            else:
                LOGGER.info('  - Unable to elevate.')
        LOGGER.info('')
        LOGGER.info('Demo commplete.')            

if __name__ == "__main__":
    demo()
