import argparse
import threading
from dataclasses import asdict, dataclass
from time import sleep, time
from typing import Dict, List

import numpy as np
import pyaudio
from loguru import logger as LOGGER

from dt_tools.os.os_helper import OSHelper


@dataclass
class SampleRate:
    LORES_Quality: int = 22050
    CD_Quality: int    = 44100
    DVD_Quality: int   = 48000
    HIRES_Quality: int = 88200

    @classmethod    
    def rate_values(cls) -> List[int]:
        return list(asdict(SampleRate()).values())
    @classmethod
    def rate_keys(cls) -> List[str]:
        return list(asdict(SampleRate()).keys())
    @classmethod
    def rate_dict(cls) -> Dict[str, int]:
        return asdict(SampleRate())
    

class SoundDefault:
    FRAME_COUNT: int    = 2048
    CHANNELS: int       = 1
    SAMPLE_RATE: int    = SampleRate.CD_Quality
    SOUND_THRESHOLD: int = 50 if OSHelper.is_windows() else 70
    TRIGGER_CNT: int    = 3


@dataclass
class SoundDetector():
    def __init__(self, frame_count: int = SoundDefault.FRAME_COUNT, 
                       channels: int = SoundDefault.CHANNELS, 
                       sample_rate: SampleRate = SoundDefault.SAMPLE_RATE,
                       sound_threshold: int = SoundDefault.SOUND_THRESHOLD, 
                       trigger_cnt: int = SoundDefault.TRIGGER_CNT,
                       sound_trigger_callback: callable = None,
                       silence_trigger_callback: callable = None):
        """
        Sound detector listens for sound via the microphone and signals either
        sound detected or silence (after sound stops).

        Args:
            frame_count (int, optional): 
                Number of audio frames to capture when analyzing if a sound has been made.
                Basically a buffer size. Defaults to 1024.

            channels (int, optional): 
                Number of audio channels to capture. Defaults to 1.

            sample_rate (int, optional): 
                Number of frames captured per second . Defaults to 44100.

            snd_threshold (int, optional): 
                This threshold is a computed value (rms) of the data from the microphone.
                When rms exeeds this threshold for trigger_cnt cycles, the sound_trigger_callback is executed. 
                Defaults to 70.

            trigger_cnt (int, optional): 
                The number of cycle that a sound needs to be either above or below the sample_threshold
                for either silence or sound. Defaults to 3.

            sound_trigger_callback (callable, optional): 
                The routine to be called when sound has been detected. If not supplied, a stub routine will be
                called and will print a debug message to the console.  Defaults to None.

            silence_trigger_callback (callable, optional): 
                The routine to be called when silence has been detected.  If not supplied, a stub routine will be
                called and will print a debug message to the console. Defaults to None.

        """
        self._frame_count: int      = frame_count 
        self._channels: int         = channels
        self._sample_rate: int      = sample_rate
        self._sound_threshold: int  = sound_threshold
        self._trigger_count: int    = trigger_cnt
        self._sound_trigger_callback: callable = sound_trigger_callback
        self._silence_trigger_callback: callable = silence_trigger_callback
        if sound_trigger_callback is None:
            self._sound_trigger_callback = self._callback_sound_stub
        if silence_trigger_callback is None:
            self._silence_trigger_callback = self._callback_silence_stub

        self._format: int           = pyaudio.paInt16
        self._listening: bool          = False
        self._pyaudio: pyaudio.PyAudio = None
        self._stream = pyaudio._Stream = None
        self._monitor_thread: threading.Thread = None
        self._sample_list: list = [0.0]

        self._current_audio_mean: int   = -1
        self._current_audio_rms: int    = -1
        self._start_time: float         = 0
        self._name: str                 = None
        # self._record_sample: bool = False

    def _callback_sound_stub(self):
        LOGGER.debug(f'Sound detected.  {self._sample_list}')

    def _callback_silence_stub(self):
        LOGGER.debug(f'Silence.         {self._sample_list}')

    @property
    def name(self) -> str:
        if self._name is None:
            pa = pyaudio.PyAudio() 
            self._name = pa.get_default_input_device_info().get('name', 'Unknown')
        return self._name
    
    @property
    def current_audio_mean(self) -> int:
        return self._current_audio_mean

    @property
    def current_audio_rms(self) -> int:
        return self._current_audio_rms

    @property
    def is_listening(self) -> bool:
        return self._listening
    
    @property
    def elapsed_monitoring_seconds(self) -> float:
        """Number of seconds monitoring has been enabled"""
        if self._start_time > 0:
            return float(f"{(time() - self._start_time):7.2}")
        
        return 0.0

    # def record_sample_sound(self):
    #     if not self.is_listening:
    #         LOGGER.warning('Not listening, unable to record.')
    #         self._record_sample = False
    #     self._record_sample = True

    #     return self._record_sample
    
    def set_sound_callback(self, func: callable):
        """
        Set the routine to be called when a sound occurs.

        Args:
            func (callable): the function name
        """
        self._sound_trigger_callback = func
    
    def set_silence_callback(self, func: callable):
        """
        Set the routine to be called when silence occurs.

        Args:
            func (callable): the function name
        """
        self._silence_trigger_callback = func


    def start(self) -> bool:
        """
        Open the audio stream and begin listening.

        Returns:
            bool: True if listening thread triggered, else False
        """
        if self.is_listening:
            LOGGER.warning('Already listening, Killing prior instance.')
            self.stop()
        self._pyaudio = pyaudio.PyAudio()
        self._stream = self._pyaudio.open(format=self._format,
                              channels=self._channels,
                              rate=self._sample_rate,
                              input=True,
                              # input_device_index=input_device,
                              frames_per_buffer=self._frame_count)
        self._listening = True
        self._monitor_thread = threading.Thread(target=self._monitor, name='snd_monitor')
        self._monitor_thread.start()
        return True

    def stop(self) -> bool:
        """
        Close the audio stream and stop listening.

        Returns:
            bool: True if thread is stopped, False if there was an error.
        """
        if not self.is_listening:
            LOGGER.warning('Not listening.')
            return True

        self._listening = False
        try:
            self._monitor_thread.join()
            self._stream.close()
            self._pyaudio.terminate()

        except Exception as ex:
            LOGGER.error(f'stop(): {ex}')

        self._pyaudio = None
        
        return True

    def _monitor(self):
        LOGGER.debug('Sound monitoring starting.')
        LOGGER.debug(f'- Channels      : {self._channels}')
        LOGGER.debug(f'- Format        : {self._format}')
        LOGGER.debug(f'- Frame count   : {self._frame_count}')
        LOGGER.debug(f'- Sample rate   : {self._sample_rate}')
        LOGGER.debug(f'- Trigger cnt   : {self._trigger_count}')
        LOGGER.debug(f'- Snd Threshold : {self._sound_threshold}')
        LOGGER.debug(f'- Sound CB      : {self._sound_trigger_callback.__name__}')
        LOGGER.debug(f'- Silence CB    : {self._silence_trigger_callback.__name__}')
        LOGGER.debug('Listening...')
        was_silent: bool = True
        sound_cnt: int  = -1
        silent_cnt: int = -1
        self._start_time = time()
        try:
            while self.is_listening:
                raw_data = self._get_audio_stream_data()
                # Convert buffer to numpy array
                np_data  = np.frombuffer(raw_data, dtype=np.short)[-self._frame_count:]
                audio_data_array = np.frombuffer(np_data, dtype=np.int16)
                sound_detected = self._is_sound_detected(audio_data_array, self._sound_threshold)
                if sound_detected:
                    silent_cnt = 0
                    if was_silent:
                        sound_cnt += 1
                        if sound_cnt >= self._trigger_count:
                            if self._sound_trigger_callback is not None:
                                self._sound_trigger_callback()
                            #     if self._record_sample:
                            #         self._save_audio_sample(raw_data)
                            #         self._record_sample = False
                            # else:
                            #     LOGGER.trace(f"Sound detected!  [{self._current_audio_rms:4.2f}] {self._current_audio_mean:7.2f}  {sound_cnt}/{silent_cnt}")
                            was_silent = False
                            sound_cnt = 0
                else: # Currently identified as silent
                    sound_cnt = 0
                    if not was_silent:
                        silent_cnt += 1
                        if silent_cnt >= self._trigger_count:
                            if self._silence_trigger_callback is not None:
                                self._silence_trigger_callback()
                            # else:
                            #     LOGGER.trace(f'Silence.         [{self._current_audio_rms:4.2f}] {self._current_audio_mean:7.2f}  {sound_cnt}/{silent_cnt}')
                            #     LOGGER.trace('')
                            was_silent = True
                            silent_cnt = 0
        
        except Exception as ex:
            LOGGER.exception(f'Uh oh - {ex}')
            self.stop()

        self._start_time = 0

    def _get_audio_stream_data(self) -> bytes:
        # Loop while buffer fills
        while self._stream.get_read_available() < self._frame_count: 
            sleep(0.01)
        
        # Read buffer size number of frames
        num_frames = self._stream.get_read_available()
        frames = self._stream.read(num_frames, exception_on_overflow=False)
        
        return frames
    
    def _is_sound_detected(self, audio_data: np.ndarray, threshold) -> bool:
        np_mean = np.mean(audio_data**2)
        rms = np.sqrt(np_mean) if np_mean >= 0 else np.float64(0.0)
        sound_detected = True if rms > threshold else False

        LOGGER.trace(f'          [{rms:4.2f}] {np_mean:7.2f} {sound_detected}')
        self._current_audio_mean = np_mean
        self._current_audio_rms  = rms

        self._sample_list.append(f'{self._current_audio_rms:5.2f}')
        if len(self._sample_list) > self._trigger_count:
            self._sample_list = self._sample_list[-self._trigger_count:]

        return sound_detected

    # def _save_audio_sample(self, raw_data: bytes):
    #     import wave
    #     import os
    #     import pathlib

    #     audio_file = OSHelper.get_temp_filename(prefix='sound_detector_', dotted_suffix='.wav', target_dir=os.curdir)
    #     LOGGER.debug(f'Save sample to {audio_file}')
    #     LOGGER.debug('- open')
    #     wf = wave.open(audio_file, "wb")
    #     LOGGER.debug('- setnchannels')
    #     wf.setnchannels(self._channels)
    #     LOGGER.debug('- setsamplewidth')
    #     wf.setsampwidth(self._pyaudio.get_sample_size(self._format))
    #     LOGGER.debug('- setframerate')
    #     wf.setframerate(self._sample_rate)
    #     LOGGER.debug('- writeframes')
    #     try:
    #         wf.writeframes(raw_data)
    #         saved = True
    #     except Exception as ex:
    #         LOGGER.error(f'- Unable to write {audio_file} - {ex}')
    #         saved = False
    #     finally:
    #         LOGGER.debug('- close')
    #         wf.close()
    #         if not saved:
    #             LOGGER.debug('- remove bad file.')
    #             pathlib.Path(audio_file).unlink(missing_ok=True)

    #     return saved
    



__STOP_REQUSTED = False
def __stop_handler(signum, frame):
    global __STOP_REQUSTED
    __STOP_REQUSTED = True

if __name__ == '__main__':
    import dt_tools.logger.logging_helper as lh
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size', type=int, default=SoundDefault.FRAME_COUNT, 
        help    =f'Sample buffer size.  Default {SoundDefault.FRAME_COUNT} bytes')
    parser.add_argument('-t', '--threshold', type=int, default=SoundDefault.SOUND_THRESHOLD,
        help = f'Sound threshold.  Default {SoundDefault.SOUND_THRESHOLD}.')
    parser.add_argument('-c', '--count', type=int, default=SoundDefault.TRIGGER_CNT,
        help=f'How many time threshold needs to be exceeded to count as sound.  Default {SoundDefault.TRIGGER_CNT}.')
    parser.add_argument('-r', '--rate', type=SampleRate, default=SoundDefault.SAMPLE_RATE,
        help=f'Freq/number of frames captured per second.  Default {SoundDefault.SAMPLE_RATE}.')
    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='Verbose logging (-v DEBUG, -vv TRACE)')
    args = parser.parse_args()

    if args.verbose > 1:
        log_level = "TRACE"
    elif args.verbose == 1:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    lh.configure_logger(log_level=log_level, log_format=lh.DEFAULT_DEBUG_LOGFMT)
    LOGGER.debug(f'Log level set to {log_level}')

    # p = pyaudio.PyAudio()
    # listen(p)
    OSHelper.enable_ctrl_c_handler(__stop_handler)
    snd_monitor = SoundDetector(frame_count=args.size,
                                sample_rate=args.rate,
                                sound_threshold=args.threshold,
                                trigger_cnt=args.count)
    snd_monitor.start()
    while not __STOP_REQUSTED:
        sleep(1)

    snd_monitor.stop()
    LOGGER.info("That's all folks!")
