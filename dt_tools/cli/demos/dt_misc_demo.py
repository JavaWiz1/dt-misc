"""
This module will execute the dt_misc package demonstrations, which include:

- GeoLocation
- Weather (current, forecast, alerts)
- Sound (TTS - text to speech)

To Run:
    ``poetry run python -m dt_tools.cli.demos.dt_misc_demo``

"""
from loguru import logger as LOGGER
import dt_tools.cli.demos.dt_geoloc_demo as geoloc_demo
import dt_tools.cli.demos.dt_weather_demo as weather_demo
import dt_tools.cli.demos.dt_misc_sound_demo as sound_demo
import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper
from dt_tools.os.project_helper import ProjectHelper

def demo():
    DEMOS = {
        "GeoLocation Demo": geoloc_demo,
        "Weather demo": weather_demo,
        "Sound demo": sound_demo
    }
    l_handle = lh.configure_logger(log_level="INFO", brightness=False)  # noqa: F841
    LOGGER.info('='*80)
    version = f'v{ProjectHelper.determine_version("dt-misc")}'
    LOGGER.info(f'dt_misc_demo {version}', 80)
    LOGGER.info('='*80)
    LOGGER.info('')
    for name, demo_module in DEMOS.items():
        if input(f'Run {name} (y/n)? ').lower() == 'y':
            demo_module.demo()  
            LOGGER.info('') 

if __name__ == '__main__':
    OSHelper.enable_ctrl_c_handler()
    demo()
                                                      
    LOGGER.success("That's all folks!!")