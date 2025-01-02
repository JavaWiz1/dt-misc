"""
Speak a string of text or speak the contents of a text file.

Currently, these routines expect VLC to be installed.

Example::
    from dt_tools.misc.sound import Accent, Sound

    obj = Sound()
    obj.speak('This is a test')
    obj.speak('This is a test, with an australian accent.', accent=Accent.Australia)

ToDo:

    Update to be cross platform without relying on VLC

"""
import os
import pathlib
import textwrap
import threading
from enum import Enum
from time import sleep

from dt_tools.os.os_helper import OSHelper as helper
from gtts import gTTS
from loguru import logger as LOGGER


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


class Sound(object):
    """
    Class to speak a string of text (or contents of a text file).

    This class relies on VLC being installed, it works on both Windows and Linux.

    Raises:
        FileNotFoundError: If file is not found.

    """
    _locked: bool = False
    _speak_thread_id: int = None
    _VLC: str = None

    def __new__(cls):
        # Make this class a singleton
        if not hasattr(cls, '_instance'):
            cls._instance = super(Sound, cls).__new__(cls)

        if not cls._is_VLC_installed():
            raise FileNotFoundError('VLC is required to use this module.  Unable to locate VLC module')
        return cls._instance


    # -- Public Functions -------------------------------------------------------------------------------------------
    @classmethod
    def speak(cls, in_token: str, speed: float = 1.0, accent: Accent = Accent.UnitedStates, ignore_in_progress: bool = False, wait: bool = True, delete_mp3:bool = True) -> bool:
        """
        Speak the text string or contents of the file

        NOTE: Speech will block until done if already speaking.

        Args:
            in_token (str): File or string of text to be spoken
            speed (float, optional): Speed (cadence) of voice. Higher numbers faster cadence. Defaults to 1.0.
            accent (Accent, optional): Accent of speaker. Defaults to Accent.UnitedStates.
            ignore_in_progress: (bool, optional): Ignore request if speech is already in progress. Defaults to False
            wait: (bool, optional): Wait for speech to finish before returning. Defaults to True.
            delete_mp3 (bool, optional): Remove generate mp3 file. Defaults to True

        Returns:
            bool: True if successful else False
        """
        if cls.is_speaking() and ignore_in_progress:
            LOGGER.warning(f'Speak thread [{cls._speak_thread_id}] in process... Ignoring request.')
            return False
        
        if cls.is_speaking():
            LOGGER.debug(f'Waiting to speak... {in_token}')
            while cls.is_speaking():
                sleep(.25)

        cls._locked = True
        text = pathlib.Path(in_token).read_text() if cls._is_file(in_token) else in_token

        kwargs = {'text': text, 'speed': speed, 'accent': accent, 'delete_mp3': delete_mp3}
        t = threading.Thread(target=cls._speak, kwargs=kwargs)
        t.start()
        cls._speak_thread_id = t.native_id
        
        if wait:
            while cls.is_speaking():
                sleep(.25)

    @classmethod
    def is_speaking(cls) -> bool:
        """
        Is speech in progress...

        Returns:
            bool: True if speech is occuring, else False
        """
        return True if cls._speak_thread_id is not None or cls._locked else False
    
    @classmethod
    def play(cls, sound_file: str, speed: float = 1.0) -> int:
        """
        Play a sound file.

        Args:
            sound_file (str): Filename
            speed (float, optional): Speed (cadence) of voice. Defaults to 1.0.

        Returns:
            int: 0 if successful else non-zero
        """
        while cls.is_speaking():
            LOGGER.trace('waiting..')
            sleep(1)
        cls._locked = True
        result = cls._play(sound_file, speed)
        cls._locked = False
        return result
    
    # -- Private Functions -------------------------------------------------------------------------------------------
    @classmethod
    def _speak(cls, text: str, speed: float, accent: Accent, delete_mp3) -> int:
        sound_file = helper.get_temp_filename(prefix='dt-', dotted_suffix='.mp3')
        LOGGER.debug(f'Speak thread {cls._speak_thread_id} started.')
        # tld top level domain for English
        # com.au (Australian), co.uk (United Kingdom), us (United States),    ca (Canada), 
        # co.in (India),       ie (Ireland),           co.za (South Africa),  com.ng (Nigeria)
        tts_obj = gTTS(text=text, lang='en', tld=accent.value, slow=False)
        LOGGER.debug(f'save {sound_file}')
        tts_obj.save(sound_file)
        
        display_text = textwrap.wrap(text=text, width=100, initial_indent='- Speak: ', subsequent_indent='         ')
        for line in display_text:
            LOGGER.trace(line)
        ret = cls._play(sound_file, speed)
        try:
            pathlib.Path(sound_file).unlink()
        except Exception as ex:
            LOGGER.error(f'Unable to delete sound file [{sound_file}] - {repr(ex)}')

        LOGGER.debug(f'Speak thread {cls._speak_thread_id} ended.')
        cls._speak_thread_id = None
        cls._locked = False
        return ret

    @classmethod
    def _play(cls, sound_file: str, speed: float = 1.0) -> int:
        '''Play the sound file'''
        check_file = pathlib.Path(sound_file)
        if not check_file.is_file():
            msg = f'Sorry, sound file {sound_file} does not exist.'
            LOGGER.warning(msg)
            return -1
        
        LOGGER.debug(f'Playing file: {cls._VLC} --intf dummy --rate {speed} --play-and-exit {sound_file}')
        if helper.is_windows():
            ret = os.system(f'"{cls._VLC}" --intf dummy --rate {speed} --play-and-exit {sound_file}')
        else:
            ret = os.system(f'{cls._VLC} --rate {speed} --play-and-exit {sound_file}')

        return  ret

    @classmethod
    def _is_VLC_installed(cls) -> bool:

        if helper.is_windows():
            cls._VLC = cls.__chk_vlc_windows()
        else:
            cls._VLC = cls.__chk_vlc_linux()

        return cls._VLC is not None

    @classmethod
    def __chk_vlc_windows(cls) -> str:
        exe = 'vlc.exe'
        start_path = pathlib.Path(os.environ['ProgramFiles'])
        LOGGER.debug(f'- Searching for {exe} starting at {start_path}')
        target = helper.find_file(filenm=exe, search_path=start_path)
        if target is None:
            start_path = pathlib.Path(os.environ['ProgramFiles(x86)'])
            LOGGER.debug(f'- Searching for {exe} starting at {start_path}')
            target = helper.find_file(filenm=exe, search_path=start_path)
    
        return target
    
    @classmethod
    def __chk_vlc_linux(cls) -> str:
        start_path = pathlib.Path('/usr/bin')
        LOGGER.debug(f'- Searching for "cvlc" starting at {start_path}')
        return helper.find_file(filenm='cvlc', search_path=start_path)

    @classmethod
    def _is_file(cls, token: str) -> bool:
        check_file = pathlib.Path(token)
        try:
            is_file = check_file.is_file()
        except OSError:
            is_file = False
        return is_file
    
if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    from dt_tools.cli.demos.dt_misc_sound_demo import demo
    
    LOGGER.enable('dt_tools.misc')
    lh.configure_logger(log_level="INFO")
    demo()
