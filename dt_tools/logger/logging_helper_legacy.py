import functools
import logging
import logging.handlers
import pathlib
import sys


DEFAULT_FILE_LOGFMT = "%(asctime)s [%(module)-15s] [%(levelname)-8s] %(message)s"
"""For file logging, format- timestamp \|level\|method name\|lineno\|message"""

DEFAULT_CONSOLE_LOGFMT = "%(message)s"
"""For console logging, format- message"""

DEFAULT_DATETIMEFMT = " %Y/%m/%d %I:%M:%S"
"""Default Time Format"""

logging.TRACE = 5
logging._levelToName[logging.TRACE] = "TRACE"
logging._nameToLevel["TRACE"] = logging.TRACE
def trace(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'TRACE'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.trace("Houston, we have a %s", "interesting problem", exc_info=1)
    """
    if self.isEnabledFor(logging.TRACE):
        self._log(logging.TRACE, msg, args, **kwargs)

logging.Logger.trace = trace
# TODO:
#   - Loglevels - TRACE, DEBUG, INFO, ERROR, CRITICAL

def configure_logger(logger_name: str, log_target = sys.stderr, log_level: str = "INFO", log_format: str = None, **kwargs) -> logging.Logger:
    """
    Configure logger via python logging.

    Parameters:
        logger_name: Name of logger
        log_target: defaults to stderr, but can supply filename as well
        log_level : TRACE|DEBUG|INFO(dflt)|ERROR|CRITICAL
        log_format: format for output log line
        other     : keyword args related to loguru logger.add() function

    Returns:
        logger_handle: Logger object
    """
    logger = None
    log_file = None
    
    print(f'logger_name: {logger_name}')
    if isinstance(log_target, str):
        log_file = pathlib.Path(log_target)
        if not log_file.parent.exists():
            print(f'ERROR: cannot create log file: {log_file}')
            print('       Path does not exist.')
            log_file = None

    if not logging.getLogger().hasHandlers():
        # No ROOT logger setup, set basicConfig
        print('no root logger, set basicConfig')
        logging.basicConfig(format=log_format, datefmt=DEFAULT_DATETIMEFMT, level=logging.ERROR)      

    # Create a custom logger (either Console or File)
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    logger.setLevel(log_level)

    # Remove any existing handlers
    # if logger.hasHandlers():
    #     for handler in logger.handlers:
    #         logger.removeHandler(handler)

    if log_file is None:
        # Console
        print('creating console logger')
        l_handle = logging.StreamHandler()
        l_line_format = log_format if log_format is not None else DEFAULT_CONSOLE_LOGFMT
        l_handle.name = "console"
    else:
        # File logger
        print('creating file logger')
        l_handle = logging.FileHandler(log_file)
        l_line_format = log_format if log_format is not None else DEFAULT_FILE_LOGFMT
        l_handle.name = "file"

    l_handle.setLevel(log_level)
    l_format = logging.Formatter(fmt=l_line_format, datefmt=DEFAULT_DATETIMEFMT)
    l_handle.setFormatter(l_format)
    logger.addHandler(l_handle)
    print(f'returning {logger.name}')
    return logger



def logger_wraps(*, entry=True, exit=True, level="DEBUG"):
    """
    BROKEN!! function decorator wrapper to log entry and exit

    When decorator enabled, messages will automatically be included in the the log:
    Example::    

        @logger_wraps()
        def foo(a, b, c):
            logger.info("Inside the function")
            return a * b * c 

    Output:
    > 
    """
    def wrapper(func):
        # THIS DOES NOT WORK, needs to be re-addressed.
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # logger_ = logger.opt(depth=1)
            logger_ = logging.root
            log_level = level if isinstance(level, int) else logging._nameToLevel[level]
            if entry:
                logger_.log(log_level, "Entering '{}' (args={}, kwargs={})", name, args, kwargs)
            result = func(*args, **kwargs)
            if exit:
                logger_.log(log_level, "Exiting '{}' (result={})", name, result)
            return result

        return wrapped

    return wrapper


# def test(con_logger, file_logger):
#     for lvl in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
#         lvl_no = logging._nameToLevel[lvl]
#         con_logger.log(lvl_no, f"This is a console {lvl} message.")
#         file_logger.log(lvl_no, f"This is a file {lvl} message.")
#     con_logger.trace('This is a console test for trace method')
#     file_logger.trace('This is a File test for trace method')

if __name__ == "__main__":
    print('test')
    conLog = configure_logger(logger_name='consoleLog', log_level="TRACE")
    fileLog = configure_logger(logger_name='fileLog', log_target='./test.log', log_level="TRACE")
    for lvl in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        lvl_no = logging._nameToLevel[lvl]
        conLog.log(lvl_no, f"This is a console {lvl} message.")
        fileLog.log(lvl_no, f"This is a file {lvl} message.")
    conLog.trace('This is a console test for trace method')
    fileLog.trace('This is a File test for trace method')
