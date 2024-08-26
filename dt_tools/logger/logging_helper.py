"""
Logging helper methods for loguru
"""
import functools
import logging
import sys

from loguru import logger

DEFAULT_FILE_LOGFMT = "<green>{time:MM/DD/YY HH:mm:ss}</green> |<level>{level: <8}</level>|<cyan>{name:10}</cyan>|<cyan>{line:3}</cyan>| <level>{message}</level>"
"""For file logging, format- timestamp \|level\|method name\|lineno\|message"""

DEFAULT_CONSOLE_LOGFMT = "<level>{message}</level>"
"""For console logging, format- message"""

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

if __name__ == "__main__":
    import dt_tools.cli.dt_misc_logging_demo as module
    module.demo()
