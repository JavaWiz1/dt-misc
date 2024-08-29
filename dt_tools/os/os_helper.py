"""
Helper for OS functions.

Supports windows and linux

"""
import ctypes
import os
import pathlib
import platform
import signal
import sys
from typing import List

from loguru import logger as LOGGER


class OSHelper():
    """
    Helper class for OS functions.
    
    Supports windows and linux

    Features:
        - OS/hardware detection (Windows/Linux/RaspberryPI)
        - Process detection (running in fg/bg)
        - Is executable in the path?
        - Is process running with admin/root permisssions?
        
        Windowws:
        - is_admin
        - elevate to admin

        Linux:
        - is_root

    Raises:
        OSError: On un-supported OS

    Examples::
        from dt_tools.os.os_helper import OSHelper

        print(f'Is Windows: {OSHelper.is_windows()})
        print(f'Is Linux  : {OSHelper.is_linux()})
        print(f'Is RPi    : {OSHelper.is_raspberrypi()})
        
    """
    @staticmethod
    def is_windows() -> bool:
        """Return True if running in windows else False"""
        return platform.system() == "Windows"
    
    @staticmethod
    def is_linux() -> bool:
        """Return True if running in linux else False"""
        return platform.system() == "Linux"

    @staticmethod
    def os_version() -> str:
        return f'{platform.system()} {platform.version()}'
    
    @staticmethod
    def current_user() -> str:
        return os.getlogin()
    
    @staticmethod
    def is_running_in_foreground():
        """
        Check if process is running in foreground

        Returns:
            True if running in foreground else False
        """
        try:
            if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
                return True     # is foreground
            return False        # is background
        except AttributeError:
            # Fall back, looks like os.getpgrp() is not available
            return sys.stdout.isatty()
        except OSError:
            return True         # is as a daemon       

    @staticmethod
    def is_running_in_background():
        """
        Check if process is running in background (or as a daemon)

        Returns:
            True if running in background else False
        """
        # return not cls.is_running_in_foreground()
        return not OSHelper.is_running_in_foreground()

    @staticmethod
    def is_executable_available(name: str) -> str:
        """
        Is executable in system path?

        Arguments:
            name: Name of executable.

        Returns:
            Fully qualified executable path if found, else None
        """
        if OSHelper.is_windows():
            sep = ';'
        else:
            sep = ':'
        PATH = os.getenv('PATH')
        exe = None
        found = False
        for dir in PATH.split(sep):
            exe = pathlib.Path(dir) / name
            if exe.exists():
                found = True
                break
            if OSHelper.is_windows():
                exe = pathlib.Path(dir) / f'{name}.exe'
                if exe.exists():
                    found = True
                    break
                exe = pathlib.Path(dir) / f'{name}.com'
                if exe.exists():
                    found = True
                    break

        if found:
            return exe
        return None

    @staticmethod
    def is_windows_admin():
        """
        Is process running as Windows Admin

        Returns:
            True if Admin privileges in effect else False
        """
        if OSHelper.is_windows():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception as ex:
                LOGGER.warning(f'On Windows, but cant check Admin privileges: {repr(ex)}')
                return False            
        
        return False

    @staticmethod
    def is_linux_root():
        """
        Is process running as root?

        Returns:
            True if root else False
        """
        return os.geteuid() == 0
    
    @staticmethod
    def is_god():
        """
        Is process running elevated.

        For windows: admin permissions
        For linux:   root user
        
        Returns:
            True if admin/root else False
        """
        if OSHelper.is_windows:
            return OSHelper.is_windows_admin()
        return OSHelper.is_linux_root()
    
    @staticmethod
    def elevate_to_admin(executable: str = None, args: List[str] = None) -> bool:
        """
        Relaunch process with elevated privileges to Windows Admin.

        User will be presented with a prompt which must be ACK'd for elevation.

        Raises:
            OSError: If not running on Windows.

        Returns:
            bool: True if successful else False
        """
        if not OSHelper.is_windows():
            raise OSError('run_as_admin is ONLY available in Windows')

        if OSHelper.is_windows_admin():
            return True
        
        tgt_executable = sys.executable if executable is None else executable
        tgt_args = sys.argv if args is None else args

        # Re-run the program with admin rights
        LOGGER.debug(f'Run Elevated - executable: {tgt_executable}   args: {tgt_args}')
        hresult = ctypes.windll.shell32.ShellExecuteW(None, "runas", tgt_executable, " ".join(tgt_args), None, 1)
        LOGGER.debug(f'  returns {hresult}')
        return True if hresult > 32 else False


    # == Hardware info =============================================================================================
    @staticmethod
    def is_raspberrypi() -> bool:
        """
        Check if hardware is a Raspberry PI

        Returns:
            True if Raspberry PI else False
        """
        if not OSHelper.is_linux():
            return False
        buffer = []
        with open('/proc/cpuinfo','r') as fh:
            buffer = fh.readlines()
        token = [x for x in buffer if x.startswith('Hardware')]
        hw = token[0].split(":")[1].strip()
        if hw.startswith("BCM"):
            return True
        return False

    # -- ctrl-c Handler routines ===================================================================================
    @staticmethod
    def disable_ctrl_c_handler() -> bool:
        """
        Disable handler for Ctrl-C checking.

        Returns:
          True if successful, else False
        """
        success = True
        try:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        except:  # noqa: E722
            success = False
        return success

    @staticmethod
    def enable_ctrl_c_handler(handler_function: callable = None) -> bool:
        """
        Enable handler for Ctrl-C checking.
        
        If Ctrl-C occurs, and no handler function has been defined, user is prompted to continue or exit.

        Arguments:
            handler_function: Function to be called when ctrl-c is requested. (optional) 
              If supplied, the function should be defined as follows...
            
              Example::

                def handler_name(signum, frame):
                    code to execute when handler is called...  

        Returns:
            True if handler successfully enabled, else False.

        """
        success = True
        if handler_function is None:
            handler_function = OSHelper._interrupt_handler
            
        try:
            signal.signal(signal.SIGINT, handler_function)
        except:  # noqa: E722
            success = False
        return success

    @staticmethod
    def _interrupt_handler(signum, frame):
        resp = ''
        while resp not in ['c', 'e']:
            try:
                resp = input('\nCtrl-C, Continue or Exit (c,e)? ').lower()
            except RuntimeError:
                LOGGER.error('\nCtrl-C, program exiting...')
                resp = 'e'

            if resp == 'e':
                os._exit(1)

if __name__ == "__main__":
    import dt_tools.cli.dt_misc_os_demo as module
    # print(sys.executable)
    # print(sys.argv)
    # print(__file__)
    module.demo()