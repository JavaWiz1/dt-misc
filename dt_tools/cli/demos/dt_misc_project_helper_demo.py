"""
This module demonstrates the ProjectHelper class features.

- Determine distribion version.
- Determine version based on file/directory name within the call stack.
- List environment installed python packages

"""
from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.os.project_helper import ProjectHelper


def demo():
    LOGGER.info('-'*80)
    LOGGER.info('dt_misc_project_helper_demo')
    LOGGER.info('-'*80)
    LOGGER.info('')

    LOGGER.info('Determine versions')
    LOGGER.info('------------------')
    LOGGER.info(f'- Distribution dt-misc : {ProjectHelper.determine_version("dt-misc", identify_src=True)}')
    LOGGER.success('  ProjectHelper.determine_version("dt-misc", identify_src=True)')
    LOGGER.info('')
    LOGGER.info(f'- File: project_helper : {ProjectHelper.determine_version("project_helper", identify_src=True)}')
    LOGGER.success('  ProjectHelper.determine_version("project_helper", identify_src=True)')
    input('\nPress Enter to continue... ')

    LOGGER.info('')
    LOGGER.info('Installed Packages')
    LOGGER.info('------------------')
    LOGGER.info('')
    LOGGER.success('  ProjectHelper.installed_packages().items()')
    LOGGER.info('')
    LOGGER.info('  Package                        Version')
    LOGGER.info('  ------------------------------ ---------')
    for package, ver in ProjectHelper.installed_packages().items():
        print(f'  {package:30} {ver}')

    LOGGER.info('')
    LOGGER.info('Demo commplete.')            
    input('\nPress Enter to continue... ')

if __name__ == "__main__":
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, log_level="INFO")
    demo()
