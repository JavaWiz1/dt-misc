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
from datetime import datetime as dt
from typing import List, Tuple

import psutil
from loguru import logger as LOGGER

from dt_tools.misc.helpers import ObjectHelper as ohelper


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
    
    @staticmethod
    def sysinfo(include_all: bool = False, include_cpu: bool = False, include_memory: bool = False, include_disk: bool = False) -> dict:
        # TODO:  gather stats
        # system    : name, ip, processor, OS, OSVersion, Manufacturer, uptime
        # cpu       : cores
        # memory    : Space (total, used, free), type
        # disk      : Space (Total,Used,Free), disks[]
        # io
        info = {}
        info['system'] = OSHelper._get_local_system_info()
        if include_all or include_cpu:
            info['cpu'] = OSHelper._get_cpu_info()
        if include_all or include_memory:
            info['memory'] = OSHelper._get_memory_info()
        if include_all or include_disk:
            info['disk'] = OSHelper._get_disk_info()

        return info
    
    @staticmethod
    def bytes_to_printformat(num_bytes: int) -> str:
        power = 2**10
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while num_bytes > power:
            num_bytes /= power
            n += 1
        return f"{num_bytes:.2f} {power_labels[n]}B"        
    
    @staticmethod
    def bytes_to_kb(num_bytes: int, num_decimals: int=0) -> float:
        kb =  num_bytes / 1024
        if num_decimals >= 0:
            return float(f'{kb:.{num_decimals}f}')
        return kb
    
    @staticmethod
    def bytes_to_mb(num_bytes: int, num_decimals: int=0) -> float:
        mb =  OSHelper.bytes_to_kb(num_bytes) / 1024
        if num_decimals >= 0:
            return float(f'{mb:.{num_decimals}f}')
        return mb
    
    @staticmethod
    def bytes_to_gb(num_bytes: int, num_decimals: int=0) -> float:
        gb = OSHelper.bytes_to_mb(num_bytes) / 1024
        if num_decimals >= 0:
            return float(f'{gb:.{num_decimals}f}')
        return gb

    @staticmethod
    def bytes_to_tb(num_bytes: int, num_decimals: int=0) -> float:
        tb =  OSHelper.bytes_to_gb(num_bytes) / 1024
        if num_decimals >= 0:
            return float(f'{tb:.{num_decimals}f}')
        return tb

    @staticmethod
    def elapsed_time(start_date: dt, end_date: dt) -> Tuple[int, int, int, int]:
        """
        Convert seconds into (days, hours, mins, sec)

        Args:
            seconds (int): number of seconds to convert

        Returns:
            Tuple[int, int, int, int]: Days, Hours, Minutes, Seconds
        """
        duration = end_date - start_date if start_date < end_date else start_date - end_date
        duration_secs = duration.total_seconds()

        days    = divmod(duration_secs, 86400)        # Get days (without [0]!)
        hours   = divmod(days[1], 3600)               # Use remainder of days to calc hours
        minutes = divmod(hours[1], 60)                # Use remainder of hours to calc minutes
        seconds = divmod(minutes[1], 1)         
        return (int(days[0]), int(hours[0]), int(minutes[0]), int(seconds[0]))

    @staticmethod
    def _get_local_system_info() -> dict:
        # uname system (os), node (name), release (osversion)
        import socket
        info = {}
        info['hostname'] = platform.node()
        info['host_fqdn'] = socket.getfqdn()
        info['ip'] = socket.gethostbyname(platform.node())  # validate this works on all platforms
        info['platform'] = platform.system()
        if OSHelper.is_linux():
            osr = platform.freedesktop_os_release()
            info['os'] = osr['NAME']
            info['os_ver'] = osr['VERSION']
        else:
            info['os'] = platform.system()
            info['os_ver'] = platform.platform()
        info['os_kernel'] = platform.uname().release
        info['machine_type'] = platform.uname().machine
        bt = psutil.boot_time()
        boot_time_str = dt.fromtimestamp(bt).strftime("%Y-%m-%d %H:%M:%S")
        boot_time = dt.strptime(boot_time_str, "%Y-%m-%d %H:%M:%S")
        days, hours, minutes, seconds = OSHelper.elapsed_time(boot_time, dt.now())
        info['last_boot_time'] = boot_time_str
        if days > 0:
            info['uptime'] = f"{days}d:{hours}h:{minutes}m:{seconds}s"
        elif hours > 0:
            info['uptime'] = f"{hours}h:{minutes}m:{seconds}s"
        elif minutes > 0:
            info['uptime'] = f"{minutes}m:{seconds}s"
        else:
            info['uptime'] = f"{seconds} secs"

        # TODO: BIOS 
        #       windows -  wmic bios get xxxxx,xxxx
        #       linux~  - /sys/class/dmi/id/ (many bios files)
        #       raspi   - no bios, but lots of info here: https://www.geeksforgeeks.org/how-to-find-all-the-hardware-information-in-raspberry-pi-os/
        return info

    @staticmethod
    def _get_cpu_info() -> dict:
        info = {}
        info['processor'] = platform.processor()
        info['cores_physical'] = psutil.cpu_count(logical=False)
        info['cores_logical'] = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        info['freq_min'] = cpu_freq.min
        info['freq_max'] = cpu_freq.max
        cpu_pct = psutil.cpu_times_percent(interval=1.0)
        info['pct_user'] = cpu_pct.user
        info['pct_system'] = cpu_pct.system
        info['pct_idle'] = cpu_pct.idle
        info['pct_interrupt'] = cpu_pct.interrupt

        return info

    @staticmethod
    def _get_memory_info() -> dict:
        info = {}
        info['swap_total'] = psutil.swap_memory().total
        info['swap_used'] = psutil.swap_memory().used
        info['swap_free'] = psutil.swap_memory().free
        info['swap_pct_used'] = psutil.swap_memory().percent

        info['virtual_total'] = psutil.virtual_memory().total
        info['virtual_used'] = psutil.virtual_memory().used
        info['virtual_free'] = psutil.virtual_memory().free
        info['virtual_pct_used'] = psutil.virtual_memory().percent
        
        return info

    @staticmethod
    def _get_disk_info() -> dict:
        info = {}
        disk_list = []
        for partition in psutil.disk_partitions():
            entry = {}
            entry['device'] = partition.device
            entry['mountpoint'] = partition.mountpoint
            entry['fstype'] = partition.fstype
            entry['mount_opts'] = partition.opts
            try:
                du = psutil.disk_usage(partition.device)
                entry['total'] = du.total
                entry['used'] = du.used
                entry['free'] = du.free
                entry['used_pct'] = du.percent
            except OSError:
                pass
            # disk_dict[partition.device] = entry
            disk_list.append(entry)
        info['partitions'] = disk_list
        
        io = psutil.disk_io_counters()
        info['io_read_bytes'] = io.read_bytes
        info['io_write_bytes'] = io.write_bytes
        info['io_read_cnt'] = io.read_count
        info['io_write_cnt'] = io.write_count
        info['io_read_ms'] = io.read_time
        info['io_write_ms'] = io.write_time
        return info
    
    @staticmethod
    def _get_io_info() -> dict:
        info = {}
        return info

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
    import json
    
    print(json.dumps(OSHelper.sysinfo(include_cpu=False, include_disk=True, include_memory=False), indent=2))
    info = OSHelper.sysinfo(include_disk=True)
    info_obj = ohelper.dict_to_obj(info)
    print(info_obj.disk)
    print('Device       Type            Total      Used       Free    % Used')
    print('------------ ---------- ---------- ---------- ---------- --------')
    for de in info_obj.disk.partitions:
        # print(de)
        total = '-'
        used = '-'
        free = '-'
        used_pct = '-'
        type = de.fstype if len(de.fstype) > 0 else de.mount_opts
        if hasattr(de, 'total'):
            total = OSHelper.bytes_to_printformat(de.total)
            used = OSHelper.bytes_to_printformat(de.used)
            free = OSHelper.bytes_to_printformat(de.free)
            used_pct = f'{de.used_pct}%'
        print(f'{de.device:12} {type:10} {total:>10} {used:>10} {free:>10} {used_pct:>8}')
    # print(OSHelper.bytes_to_kb(num_bytes, 2))
    # print(OSHelper.bytes_to_mb(num_bytes, 3))
    # print(OSHelper.bytes_to_gb(num_bytes, 1))
    # print(OSHelper.bytes_to_tb(num_bytes, 0))
    # module.demo()