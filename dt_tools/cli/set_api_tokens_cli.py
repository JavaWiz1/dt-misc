"""
This module creates the token file and stores token(s) used for interface with dt_tools 3rd party entities.

To get your token, go to https:/ipinfo.io/missingauth

```
poetry run python -m dt_tools.cli.set_iphelper_token_cli
```

"""
import sys

import dt_tools.logger.logging_helper as lh
from dt_tools.misc.helpers import ObjectHelper as oh
from dt_tools.misc.helpers import ApiTokenHelper as api_helper
from typing import List
from loguru import logger as LOGGER

def get_input(text: str, valid_responses: List=None) -> str:
    resp = input(text)
    if valid_responses is not None:
        while resp not in valid_responses:
            resp = input(text)
    return resp

def select_api() -> str:

    LOGGER.info('API Services available')
    LOGGER.info('')
    num_services = len(api_helper._API_DICT)
    idx = 0
    for key, val in api_helper._API_DICT.items():
        entry = oh.dict_to_obj(val)
        has_token = api_helper.get_api_token(key) is not None
        if has_token:
            LOGGER.success(f'{idx:1} {key} - {entry.desc}')
            LOGGER.success(f'  Has Token : {has_token}')
        else:
            LOGGER.warning(f'{idx:1} {key} - {entry.desc}')
            LOGGER.warning(f'  Has Token : {has_token}')
        LOGGER.info(f'  Token URL : {entry.token_url}')
        LOGGER.info(f'  dt_module : {entry.module}')
        LOGGER.info('')
        idx += 1

    choices = []
    for i in range(num_services):
        choices.append(str(i))
    choices.append('99')

    resp = int(get_input(f'What service to set API for? (0-{num_services-1} or 99 to exit) > ', valid_responses=choices))
    key = None
    if resp != 99:
        key = list(api_helper._API_DICT.keys())[resp]

    return key

def manage_token(api_key: str) -> str:
    rc = 0
    entry = api_helper.get_api_service_definition(api_key)
    if entry is None:
        raise ValueError(f'Unknown API service: {api_key}')
    LOGGER.info('')
    LOGGER.info('-'*90)
    LOGGER.info('')
    LOGGER.info(f'Service  : {api_key} - {entry["desc"]}')
    LOGGER.info(f'Token URL: {entry["token_url"]}')
    LOGGER.info('')
    LOGGER.info('To enable the dt_tools and packages for a specific service, a one-time process is necessary to acquire')
    LOGGER.info('an API token.  Once aquired, this process will save it locally for future use.')
    LOGGER.info('')
    LOGGER.info(f'If you already have a token, but forget what it is, you may log back into {api_key}')
    LOGGER.info('and retrieve your token.')
    LOGGER.info('')
    LOGGER.warning('NOTE:')
    LOGGER.info(f'  The token is stored locally in {api_helper._DT_TOOLS_TOKENS_LOCATION}.')
    LOGGER.info(f'         format: {{"{api_key}": "xxxxxxxxxxxxxx"}}')
    LOGGER.info('')

    old_token = api_helper.get_api_token(api_key) 
    if old_token is None:
        prompt = 'Continue (y/n) > '
    else:
        prompt = 'Token exists, overwrite? > '

    if get_input(prompt, ['y', 'n']) == 'y':
        token = get_input('Token > ')
        if len(token.strip()) == 0:
            LOGGER.warning('  Empty token, did not save.')
            rc = 2
        else:
            if api_helper.save_api_token(api_key, token):
                if api_helper.can_validate(api_key):
                    if api_helper.validate_token(api_key):
                        LOGGER.success('Token saved.')
                    else:
                        if old_token is None:
                            api_helper.save_api_token(api_key, None)
                            rc = 3
                        else:
                            api_helper.save_api_token(api_key, old_token)
                            rc = 4
                        LOGGER.warning(f'Token not valid, not saved. ({rc})')
        LOGGER.info('')
    
    return rc

def main() -> int:
    rc = 0
    LOGGER.info('')
    LOGGER.info('-'*90)
    LOGGER.info(' dt_tools Token Manager')
    LOGGER.info('-'*90)
    LOGGER.info('')
    api_key = select_api()
    if api_key is None:
        LOGGER.warning('  No API selected.')
        rc = 1
    else:
        rc = manage_token(api_key)

    return rc


if __name__ == "__main__":
    if '-v' in sys.argv:
        LOG_LVL = 'DEBUG'
    else:
        LOG_LVL = "INFO"
    lh.configure_logger(log_level=LOG_LVL, brightness=False)
    sys.exit(main())
    # manage_token()
