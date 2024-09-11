"""
Logging helper methods for loguru. (https://github.com/Delgan/loguru)

Example::

    import dt_tools.logger.logging_helper as lh
    from loguru import logger as LOGGER

    log_file = './mylog.log'

    # File logger
    f_handle = lh.configure_logger(log_target=log_file, log_level="DEBUG")
    # Console logger
    c_handle - lh.configure_logger()

    LOGGER.debug('this should only show up in file logger')
    LOGGER.info('this should show up in file logger and console')

"""
import functools
import logging
import sys
import time

from loguru import logger

# Format variables:
# Variable    Description
# ----------- ------------------------------------------------------------
# elapsed     The time elapsed since the start of the program
# exception   The formatted exception if any, None otherwise
# extra       The dict of attributes bound by the user (see bind())
# file        The file where the logging call was made
# function    The function from which the logging call was made
# level       The severity used to log the message
# line        The line number in the source code
# message     The logged message (not yet formatted)
# module      The module where the logging call was made
# name        The __name__ where the logging call was made
# process     The process in which the logging call was made
# thread      The thread in which the logging call was made
# time        The aware local time when the logging call was made

DEFAULT_FILE_LOGFMT = "<green>{time:MM/DD/YY HH:mm:ss}</green> |<level>{level: <8}</level>|<cyan>{name:18}</cyan>|<cyan>{line:4}</cyan>| <level>{message}</level>"
"""For file logging, format- timestamp \|level\|method name\|lineno\|message"""

DEFAULT_CONSOLE_LOGFMT = "<level>{message}</level>"
"""For console logging, format- message"""

DEFAULT_DEBUG_LOGFMT =  "<green>{time:HH:mm:ss}</green> |<level>{level: <8}</level>|<cyan>{function:20}</cyan>|<cyan>{line:4}</cyan>| <level>{message}</level>"
"""For console/file logging, timestamp \|level\|method name\|lineno\|message"""

def configure_logger(log_target = sys.stderr, log_level: str = "INFO", log_format: str = None, brightness: bool = None, log_handle: int = 0, **kwargs) -> int:
    """
    Configure logger via loguru.

     - should be done once for each logger (console, file,..)
     - if reconfiguring a logger, pass the log_handle
    
    Parameters:
        log_target: defaults to stderr, but can supply filename as well (default console/stderr)
        log_level : TRACE|DEBUG|INFO(dflt)|ERROR|CRITICAL (default INFO)
        log_format: format for output log line (loguru default)
        brightness: console messages bright or dim (default True)
        log_handle: handle of log being re-initialized. (default 0)
        other     : keyword args related to loguru logger.add() function

    Example::

        import dt_tools.logger.logging_helper as lh
        from loguru import logger as LOGGER

        log_file = './mylog.log'

        f_handle = lh.configure_logger(log_target=log_file, log_level="DEBUG")
        c_handle - lh.configure_logger()

        LOGGER.debug('this should only show up in file logger')
        LOGGER.info('this should show up in file logger and console')

    Returns:
        logger_handle_id: integer representing logger handle
    """
    try:
        logger.remove(log_handle)
        # attempt to include all python loggers
        logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    except:  # noqa: E722
        pass
    
    if brightness is not None:
        set_log_levels_brighness(brightness)
        
    if not log_format:
        # Set format based on type of logger (file vs console)
        if isinstance(log_target, str):
            log_format = DEFAULT_FILE_LOGFMT
        else:
            log_format = DEFAULT_CONSOLE_LOGFMT

    hndl = logger.add(sink=log_target, level=log_level, format=log_format, **kwargs)

    return hndl


class _InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
        
def _print_log_level_definitions():
    for lvl in ['TRACE','DEBUG','INFO','SUCCESS','WARNING','ERROR','CRITICAL']:
        logger.log(lvl, logger.level(lvl))

def set_log_levels_brighness(on: bool = True):
    """
    Set brighness of console log messages

    Args:
        on (bool, optional): True messages are bold (bright), False messages are dimmer. Defaults to True.
    """
    for lvl in ['TRACE','DEBUG','INFO','SUCCESS','WARNING','ERROR','CRITICAL']:
        color = logger.level(lvl).color
        if on and '<bold>' not in color:
            color = f'{color}<bold>'
        elif not on:
            color = color.replace('<bold>', '')
        logger.level(lvl, color=color)

# == Logging Decorators =======================================================================
def logger_wraps(*, entry=True, exit=True, level="DEBUG"):
    """
    function decorator wrapper to log entry and exit

    When decorator enabled, messages will automatically be included in the the log:
    Example::    

        @logger_wraps()
        def foo(a, b, c):
            logger.info("Inside the function")
            return a * b * c 

    """
    def wrapper(func):
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger_ = logger.opt(depth=1)
            if entry:
                logger_.log(level, "Entering '{}' (args={}, kwargs={})", name, args, kwargs)
            result = func(*args, **kwargs)
            if exit:
                logger_.log(level, "Exiting '{}' (result={})", name, result)
            return result

        return wrapped

    return wrapper

def timer_wraps(*, level="DEBUG"):
    """
    function decorator wrapper to log function execution time

    Example::

        @timer_wraps(level='INFO')
        def foo(a,b,c):
          logger.info('inside the function')
          time.sleep(1)
          return a * b * c

    """
    def wrapper(func):
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            """time_wrapper's doc string"""
            start = time.perf_counter()
            result = func(*args, **kwargs)
            time_elapsed = time.perf_counter() - start
            logger.info(f"TIMER: Function: {name}, Time: {time_elapsed:.3f} seconds")
            return result
        return wrapped
    
    return wrapper


if __name__ == "__main__":
    import dt_tools.cli.demos.dt_misc_demo as module
    module.demo()
