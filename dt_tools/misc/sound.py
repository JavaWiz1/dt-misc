"""
Speak a string of text or speak the contents of a text file.

Currently, these routines expect VLC to be installed.

Example::
    from dt_tools.os.sound import Accent, Sound

    obj = Sound()
    obj.speak('This is a test')
    obj.speak('This is a test, with an australian accent.', accent=Accent.Australia)

ToDo:

    Update to be cross platform without relying on VLC

"""
import os
import pathlib
import tempfile
import textwrap
from enum import Enum
from time import sleep

from gtts import gTTS
from loguru import logger as LOGGER

from dt_tools.os.os_helper import OSHelper as helper


class Accent(Enum):
    """Accent codes for speaking"""
    Australia = "com.au"
    UnitedKingdom = "co.uk"
    UnitedStates = "us"
    Canada = "ca"
    India = "co.in"
    Ireland = "ie"
    SouthAfrica = "co.za"
    Nigeria = "com.ng"


class Sound():
    """
    Class to speak a string of text (or contents of a text file).

    This class relies on VLC being installed, it works on both Windows and Linux.

    Raises:
        FileNotFoundError: If file is not found.

    """
    _instance = None
    _is_speaking = False

    def __new__(cls):
        # Make this class a singleton
        if cls._instance is None:
            LOGGER.debug('creating sound class')
            cls._instance = super(Sound, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if helper.is_windows():
            start_path = pathlib.Path(os.environ['ProgramFiles'])
            exe = "vlc.exe"
        else:
            start_path = pathlib.Path('/usr/bin')
            exe = 'cvlc'
        
        self._VLC = self._file_location(start_path, exe)
        if self._VLC is None:
            raise FileNotFoundError('VLC is required to use this module.  Unable to locate VLC module')
    
    def speak(self, in_token: str, speed: float = 1.0, accent: Accent = Accent.UnitedStates, delete_mp3:bool = True) -> int:
        """
        Speak the text string or contents of the file

        Args:
            in_token (str): File or string of text to be spoken
            speed (float, optional): Speed (cadence) of voice. Higher numbers faster cadence. Defaults to 1.0.
            accent (Accent, optional): Accent of speaker. Defaults to Accent.UnitedStates.

        Returns:
            int: 0 if successful else non-zero
        """
        while self._is_speaking:
            LOGGER.trace('waiting..')   
            sleep(1)
        self._is_speaking = True
        check_file = pathlib.Path(in_token)
        try:
            is_file = check_file.is_file()
        except OSError:
            is_file = False
        text = check_file.read_text() if is_file else in_token
        t_file = tempfile.NamedTemporaryFile(mode='w+b',prefix='dt-', suffix='.mp3', delete=True)
        sound_file = t_file.name
        t_file.close()
        # tld top level domain for English
        # com.au (Australian), co.uk (United Kingdom), us (United States),    ca (Canada), 
        # co.in (India),       ie (Ireland),           co.za (South Africa),  com.ng (Nigeria)
        tts_obj = gTTS(text=text, lang='en', tld=accent.value, slow=False)
        tts_obj.save(sound_file)
        
        display_text = textwrap.wrap(text=text, width=100, initial_indent='- Speak: ', subsequent_indent='         ')
        for line in display_text:
            LOGGER.trace(line)
        ret = self._play(sound_file, speed)
        try:
            pathlib.Path(sound_file).unlink()
        except Exception as ex:
            LOGGER.error(f'Unable to delete sound file [{sound_file}] - {repr(ex)}')
        self._is_speaking = False

        return ret

    def play(self, sound_file: str, speed: float = 1.0) -> int:
        """
        Play a sound file.

        Args:
            sound_file (str): Filename
            speed (float, optional): Speed (cadence) of voice. Defaults to 1.0.

        Returns:
            int: 0 if successful else non-zero
        """
        while self._is_speaking:
            LOGGER.trace('waiting..')
            sleep(1)
        self._is_speaking = True
        result = self._play(sound_file, speed)
        self._is_speaking = False
        return result
    
    def _play(self, sound_file: str, speed: float = 1.0) -> int:
        '''Play the sound file'''
        check_file = pathlib.Path(sound_file)
        if not check_file.is_file():
            msg = f'Sorry, sound file {sound_file} does not exist.'
            LOGGER.warning(msg)
            return -1
        
        LOGGER.debug(f'Playing file: {self._VLC} --intf dummy --rate {speed} --play-and-exit {sound_file}')
        if helper.is_windows():
            ret = os.system(f'"{self._VLC}" --intf dummy --rate {speed} --play-and-exit {sound_file}')
        else:
            ret = os.system(f'{self._VLC} --rate {speed} --play-and-exit {sound_file}')

        return  ret
    
    def _file_location(self, search_path: str, target: str) -> str:
        vlc_loc: str = None
        for filepath in search_path.rglob(target):
            vlc_loc = filepath
            break

        return vlc_loc
    
if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    from dt_tools.cli.demos.dt_misc_sound_demo import demo

    lh.configure_logger(log_level="INFO")
    demo()
