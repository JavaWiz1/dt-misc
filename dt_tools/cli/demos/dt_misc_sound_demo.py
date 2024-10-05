"""
This module demonstrates the Sound class functionality.

- Speak with accents.
- Vary speech speed/cadence.
- Speak the contents of a text file.

"""
import pathlib
from datetime import datetime as dt

from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper
from dt_tools.os.project_helper import ProjectHelper
from dt_tools.misc.sound import Accent, Sound
import requests

DEMO_SPEED = 1.25

def _get_quote_of_the_day() -> str:
    url = "https://zenquotes.io/api/random"
    text = ''
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            resp_json = resp.json()
            quote = resp_json[0]['q']
            author = resp_json[0]['a']
            text = f'{quote}...\n  {author}...'
    except Exception as ex:
        LOGGER.error(repr(ex))
        text = ''
    return text

def _accent_demo():
    Sound().speak('Lets start out with an Accent demonstration.', speed=DEMO_SPEED)
    LOGGER.info('')
    LOGGER.info('Accents demo')
    LOGGER.info('------------')
    LOGGER.info('  Code')
    LOGGER.info('  ----------------------------------------------------------------------------------------------------')
    for accent in Accent:
        LOGGER.success(f'  Sound().speak(f"This is a test, with a {accent.name} accent.", accent={accent}, speed={DEMO_SPEED})')
        Sound().speak(f'This is a test, with a {accent.name} accent.', accent=accent, speed=DEMO_SPEED, wait=True)
    
    input('\nPress Enter to continue... ')

def _speed_demo():
    Sound().speak('Lets continue with a speach speed demonstration.', speed=DEMO_SPEED)
    LOGGER.info('')
    LOGGER.info('Speech speed (cadence) demo')
    LOGGER.info('----------------------------')
    LOGGER.info('  Code')
    LOGGER.info('  ----------------------------------------------------------------------------------------------------')
    for speed in [0.75, 1.0, 1.25, 1.5, 2.0]:
        LOGGER.success(f'  Sound().speak("This is a test with the speed set to {speed}.", speed={speed})')
        Sound().speak(f'This is a test, with the speed set to {speed}.', speed=speed, wait=True)
    
    input('\nPress Enter to continue... ')

def _file_demo():
    LOGGER.info('')
    LOGGER.info('Text file sound demo')
    LOGGER.info('--------------------')
    snd = Sound()
    snd.speak('This demo will create a text file and translate it into speech.', speed=DEMO_SPEED, wait=True)
    test_file = pathlib.Path(OSHelper().get_temp_filename(prefix='dt-', dotted_suffix='.txt', target_dir='.'))
    LOGGER.info(f'- Generate text file [{test_file}].')
    date = dt.strftime(dt.now(), "%A %B %d")
    time = dt.strftime(dt.now(), "%I:%M %p")
    text = f"Today is {date} at {time}.\n"
    text += f"The operating system is {OSHelper.os_version()}.\n"
    if OSHelper.is_god():
        text += f"The current user: {OSHelper.current_user()}, is running with elevated privileges.\n"
    else:
        text += f"The current user: {OSHelper.current_user()}, is NOT running with elevated privileges.\n"
    ver, src = ProjectHelper.determine_version('dt-misc', identify_src=True)
    text += f"Version {ver} of this demo is running.\n"
    text += f"The version was determined by {src}\n"
    quote = _get_quote_of_the_day()
    if len(quote) > 0:
        text += "Now for the quote of the day:\n"
        text += f'{quote}\n'

    LOGGER.info(f'- Writing to {test_file}...')
    test_file.write_text(text)
    LOGGER.info('- Contents of file:')
    for line in text.splitlines():
        print(f'    {line}')
    LOGGER.info('')
    LOGGER.info('- Reading and speaking the text in the file.')
    LOGGER.success(f'  Sound().speak("{test_file}", speed{DEMO_SPEED})')
    snd.speak(test_file, speed=DEMO_SPEED, wait=True)
    
    test_file.unlink()

def demo():
    OSHelper.enable_ctrl_c_handler()
    LOGGER.info('-'*80)
    LOGGER.info('dt_misc_sound_helper_demo')
    LOGGER.info('-'*80)

    _accent_demo()
    _speed_demo()
    _file_demo()

    LOGGER.info('')
    salutation = 'This concludes the sound demo...  Thanks for listening.'
    Sound().speak(salutation, speed=DEMO_SPEED, wait=False)
    LOGGER.info(salutation)

if __name__ == "__main__":
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, brightness=False)
    demo()
