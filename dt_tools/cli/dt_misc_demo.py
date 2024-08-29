from loguru import logger as LOGGER

import dt_tools.cli.dt_misc_logging_demo as logging_demo
import dt_tools.cli.dt_misc_os_demo as os_demo
import dt_tools.cli.dt_misc_os_helper_demo as os_helper_demo
import dt_tools.cli.dt_misc_project_helper_demo as project_helper_demo
import dt_tools.cli.dt_misc_sound_demo as sound_demo
import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper
from dt_tools.os.project_helper import ProjectHelper

if __name__ == '__main__':
    OSHelper.enable_ctrl_c_handler()
    DEMOS = {
        "Logging demo": logging_demo,
        "OS demo": os_demo,
        "OS Helper demo": os_helper_demo,
        "Project Helper demo": project_helper_demo,
        "Sound demo": sound_demo
    }
    l_handle = lh.configure_logger(log_level="INFO", brightness=False)
    LOGGER.info('='*80)
    version = f'v{ProjectHelper.determine_version("dt-misc")}'
    LOGGER.info(f'dt_misc_demo {version}', 80)
    LOGGER.info('='*80)
    LOGGER.info('')
    LOGGER.remove(l_handle)
    for name, demo_module in DEMOS.items():
        if input(f'Run {name} (y/n)? ').lower() == 'y':
            demo_module.demo()
            LOGGER.info('') 
                                                      
    LOGGER.success("That's all folks!!")