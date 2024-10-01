"""
This module demonstrates the OSHelper features.

- OS Detection
- Elevated privilege detection and escalation

"""
from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper
from dt_tools.misc.helpers import ObjectHelper as oh
from types import SimpleNamespace
import json

def demo_simple_report(sysinfo: dict):
    for section, section_value in sysinfo.items():
        LOGGER.success(section)
        for k,v in section_value.items():
            if isinstance(v, list):
                instance_no = 0
                for l_entry in v:
                    LOGGER.success(f'  == {instance_no} ===')
                    instance_no += 1
                    for k2,v2 in l_entry.items():
                        LOGGER.info(f'    {k2:10} {v2}')
            else:
                LOGGER.info(f'  {k:18} : {v}')
        LOGGER.info('')

def demo_report(sysinfo: dict):
    obj = oh.dict_to_obj(sysinfo)
    LOGGER.debug(obj.system)
    LOGGER.info('')
    LOGGER.success('System Info:')
    LOGGER.info(f'  Host      : {obj.system.hostname} - {obj.system.host_fqdn}')
    LOGGER.info(f'              {obj.system.ip}')
    LOGGER.info(f'  Platform  : {obj.system.platform} - {obj.system.machine_type}')
    LOGGER.info(f'  OS        : {obj.system.os}')
    LOGGER.info(f'              {obj.system.os_ver}')
    LOGGER.info(f'  Kernel    : {obj.system.os_kernel}')
    LOGGER.info(f'  Boot Info : Last boot - {obj.system.last_boot_time}')
    LOGGER.info(f'              Up time   - {obj.system.uptime}')
    
    LOGGER.info('')
    LOGGER.debug(obj.cpu)
    LOGGER.success('CPU Info:')    
    LOGGER.info(f'  Processor : {obj.cpu.processor}')
    LOGGER.info(f'  Cores     : {obj.cpu.cores_physical:2} physical')
    LOGGER.info(f'              {obj.cpu.cores_logical:2} logical')
    LOGGER.info(f'  Frequency : {obj.cpu.freq_min} - {obj.cpu.freq_max} MHz')

    LOGGER.info('')
    LOGGER.debug(obj.memory)
    LOGGER.success('Memory Info:')
    LOGGER.info( '               Total       Used       Free  % Used')
    LOGGER.info( '           ---------  ---------  ---------  ------')
    total = OSHelper.bytes_to_printformat(obj.memory.virtual_total)
    used  = OSHelper.bytes_to_printformat(obj.memory.virtual_used)
    free  = OSHelper.bytes_to_printformat(obj.memory.virtual_free)
    pct_used = f'{obj.memory.virtual_pct_used}%'
    LOGGER.info(f'  Virtual  {total:>9}  {used:>9}  {free:>9}  {pct_used:>6}')
    total = OSHelper.bytes_to_printformat(obj.memory.swap_total)
    used  = OSHelper.bytes_to_printformat(obj.memory.swap_used)
    free  = OSHelper.bytes_to_printformat(obj.memory.swap_free)
    pct_used = f'{obj.memory.swap_pct_used}%'
    LOGGER.info(f'  Swap     {total:>9}  {used:>9}  {free:>9}  {pct_used:>6}')
    
    LOGGER.info('')
    LOGGER.success('Disk Info:')
    print('  Device       Type            Total      Used       Free    % Used')
    print('  ------------ ---------- ---------- ---------- ---------- --------')
    for de in obj.disk.partitions:
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
        print(f'  {de.device:12} {type:10} {total:>10} {used:>10} {free:>10} {used_pct:>8}')
    

def demo():
    LOGGER.info('')
    LOGGER.info('-'*40)
    LOGGER.info('dt_misc_sysinfo_demo')
    LOGGER.info('-'*40)
    sysinfo = OSHelper.sysinfo(include_all=True)

    LOGGER.info('')
    LOGGER.info('system_information (as dictionary):')
    print(json.dumps(sysinfo, indent=1))
    input('\nPress Enter to continue... ')

    LOGGER.info('')
    LOGGER.info('system_information (simple report):')
    demo_simple_report(sysinfo)
    LOGGER.info('')
    input('\nPress Enter to continue... ')

    LOGGER.info('')
    LOGGER.info('system_information (as object):')
    sysinfo_obj:SimpleNamespace  = oh.dict_to_obj(sysinfo)
    LOGGER.success('sysinfo_obj.system:')
    LOGGER.info(sysinfo_obj.system)
    LOGGER.success('sysinfo_obj.cpu:')
    LOGGER.info(sysinfo_obj.cpu)
    LOGGER.success('sysinfo_obj.memory:')
    LOGGER.info(sysinfo_obj.memory)
    LOGGER.success('sysinfo_obj.disk:')
    LOGGER.info(sysinfo_obj.disk)

    LOGGER.info('')
    LOGGER.info('system_information (as report):')
    demo_report(sysinfo)

    LOGGER.info('')
    LOGGER.info('Demo commplete.')            
    input('\nPress Enter to continue... ')

if __name__ == "__main__":
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, log_level="INFO", brightness=False)
    demo()
