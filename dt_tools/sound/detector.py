import argparse
import pathlib
import threading
from dataclasses import asdict, dataclass
from time import sleep, time
from typing import Dict, List, Union

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
    SOUND_THRESHOLD: int = 20 # if OSHelper.is_windows() else 70
    TRIGGER_CNT: int    = 3


@dataclass
class SoundDetector():
    def __init__(self, microphone_id: int = -1,
                       frame_count: int = SoundDefault.FRAME_COUNT, 
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
            microphone_id (int, optional):
                ID associated with the microphone device.  If -1, default microphone will be used.

            frame_count (int, optional): 
                Number of audio frames to capture when analyzing if a sound has been made.
                Basically a buffer size. Defaults to 1024.

            channels (int, optional): 
                Number of audio channels to capture. Defaults to 1.

            sample_rate (int, optional): 
                Number of frames captured per second . Defaults to 44100.

            snd_threshold (int, optional): 
                This threshold is a computed loudness value (range 0-140 db) of the data from the microphone.
                When loudness exeeds this threshold for trigger_cnt cycles, the sound_trigger_callback is executed. 
                Defaults to 20.

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
        self._device_id: int        = microphone_id if microphone_id >= 0 else self.default_microphone_id
        self._frame_count: int      = frame_count 
        self._channels: int         = channels
        self._sample_rate: int      = sample_rate
        self._sound_threshold: int  = sound_threshold
        self._trigger_count: int    = trigger_cnt
        
        self._sound_trigger_callback: callable   = sound_trigger_callback
        self._silence_trigger_callback: callable = silence_trigger_callback

        if sound_trigger_callback is None:
            self._sound_trigger_callback = self._callback_sound_stub
        if silence_trigger_callback is None:
            self._silence_trigger_callback = self._callback_silence_stub

        self._device_name: str         = None
        self._format: int              = pyaudio.paInt16
        self._listening: bool          = False
        self._pyaudio: pyaudio.PyAudio = None
        self._stream = pyaudio._Stream = None
        self._monitor_thread: threading.Thread = None
        self._sample_list: list        = [0.0]

        self._capture: bool              = False
        self._capture_path: pathlib.Path = None
        self._capture_file: pathlib.Path = None
        self._loudness: float            = 0
        self._start_time: float          = 0
        self._elapsed_secs: float        = 0
        self._name: str                  = None


    # -------------------------------------------------------------------------------------
    @property
    def default_microphone_id(self) -> int:
        """
        Default microphone id.

        Returns:
            str: Microphone id or None if no microphone exists.
        """        
        pa = pyaudio.PyAudio()
        mic_id = -1
        try:
            host_info = pa.get_default_host_api_info()
            mic_id = int(host_info.get('defaultInputDevice'))
        except IOError as ioe:
            LOGGER.debug(f'Unable to identify default microphone id. {ioe}')
        
        return mic_id

    @property
    def default_microphone_name(self) -> str:
        """
        Default microphone name.

        Returns:
            str: Microphone name or 'Unknown' if no microphone exists.
        """        
        default_device = self.default_input_device_info()
        if default_device is None:
            device_name = 'Unknown'
        else:
            device_name = default_device.get('name', 'Unknown')

        return device_name

    # -------------------------------------------------------------------------------------
    @property
    def microphone_id(self) -> int:
        """
        Currently selected microphone index.

        Returns:
            str: Microphone index or -1 if no microphone exists.
        """
        return self._device_id
    
    @property
    def microphone_name(self) -> str:
        """
        Currently selected microphone name.

        Returns:
            str: Microphone name or 'Unknown' if no microphone exists.
        """
        if self._device_name is None:
            try:
                dev_info = pyaudio.PyAudio().get_device_info_by_index(self.microphone_id)
                self._device_name = dev_info.get('name', 'Unknown')
            except Exception as ex:
                self._device_name = f'Unknown - {ex}'
    
        return self._device_name
    
    # -------------------------------------------------------------------------------------
    @property
    def default_host_api_info(self) -> Union[dict, None]:
        try:
            device = pyaudio.PyAudio().get_default_host_api_info()
        except IOError as ioe:
            LOGGER.warning(f'Audio Host Info: {ioe}')
            device = None
        return device

    @property
    def default_input_device_info(self) -> Union[dict, None]:
        """
        Default input device (microphone) info.

        Returns:
            Union[dict, None]: Dictionary of input device settings.  None if input device does not exist.
        """
        try:
            device = pyaudio.PyAudio().get_default_input_device_info()
        except IOError as ioe:
            LOGGER.warning(f'Audio Input Device: {ioe}')
            device = None
        return device
    
    @property
    def loudness(self) -> float:
        """
        Loudness in decibels (db)

        Returns:
            float: db value (0 to 140)
        """
        return self._loudness
    
    @property
    def is_listening(self) -> bool:
        """
        Is sound detection enabled

        Returns:
            bool: True if enabled, False if disabled.
        """
        return self._listening
    
    # -------------------------------------------------------------------------------------
    @property
    def capture_path(self) -> Union[str, None]:
        """
        Directory when capture file will be saved.

        Returns:
            Union[str, None]: None if not set otherwise capture path.
        """
        if self._capture_path is None:
            self._capture_path = pathlib.Path('.')
        return self._capture_path.absolute()
    
    @capture_path.setter
    def capture_path(self, val: str):
        """
        Set directory where capture file will be saved.

        Args:
            val (str): Valid directory path.
        """
        pth = pathlib.Path(val)
        if pth.is_dir:
            self._capture_path = pth
        else:
            LOGGER.warning(f'Unable to set capture path to {pth}')

    @property
    def capture_data(self) -> bool:
        """
        Capture data state

        Returns:
            bool: True - capture enabled, False - capture disabled.
        """
        return self._capture    

    @capture_data.setter
    def capture_data(self, enable_capture: bool):
        """
        Enable data capture.

        Write runtime data to csv file in below format:
        
        - Sound detected, threshold, loudness, sample loudness (threshold count items)

        Args:
            enable_capture (bool): True start capture, False end capture.
        """
        if self._capture:
            if enable_capture:
                LOGGER.warning('Already in capture mode')
            else:
            # Turn off
                LOGGER.info('Capture disabled.')
                self._capture = False
        else:
            if enable_capture:
                tgt_path = '.' if self.capture_path is None else self.capture_path
                c_filename = OSHelper.get_temp_filename(prefix='audioCapture',
                                                        dotted_suffix='.csv', 
                                                        target_dir=tgt_path,
                                                        keep=True)
                self._capture_file = pathlib.Path(c_filename)
                rng = [str(x) for x in list(range(self._trigger_count))]
                sample_headers = f"Sample{', Sample'.join(rng)}"                
                capture_line = f'sound_detected,threshold,loudness(db),{sample_headers}\n'
                with self._capture_file.open('a') as c_file:
                    c_file.write(capture_line)
                self._capture = True
                LOGGER.info(f'Capture enabled: {self._capture_file}')
            else:
                LOGGER.warning('Capture not enabled, cannot disable.')

    # -------------------------------------------------------------------------------------
    @property
    def elapsed_monitoring_seconds(self) -> float:
        """Number of seconds monitoring has been enabled"""
        if self._start_time > 0:
            return float(f"{(time() - self._start_time):7.2}")
        
        return self._elapsed_secs

    #----------------------------------------------------------------------------------------
    #-- Operate functions (Start/Stop) ------------------------------------------------------
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
                              input_device_index=self.microphone_id,
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

        if self.capture_data:
            self.capture_data = False

        self._listening = False
        try:
            self._monitor_thread.join()
            self._stream.close()
            self._pyaudio.terminate()

        except Exception as ex:
            LOGGER.error(f'stop(): {ex}')

        self._pyaudio = None
        
        return True

    # -------------------------------------------------------------------------------------
    #-- Set callback functions ------------------------------------------------------------
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


    # ====================================================================================
    #== Private Functions ================================================================
    def _callback_sound_stub(self):
        LOGGER.trace(f'Sound detected.  [Threshold: {self._sound_threshold}  Samples: {self._sample_list}]')

    def _callback_silence_stub(self):
        LOGGER.trace(f'Silence.         [Threshold: {self._sound_threshold}  Samples: {self._sample_list}]')


    def _calculate_loudness(self, signal: np.array, sample_rate: int):
        """Calculates loudness of a signal in decibels (db)"""

        loudness = 10 * np.log10(np.mean(np.abs(signal)**2))
        return loudness
        # # Perform FFT
        # fft_result = np.fft.fft(signal)

        # # Calculate magnitude spectrum
        # magnitude_spectrum = np.abs(fft_result)

        # # Calculate power spectrum
        # power_spectrum = magnitude_spectrum ** 2

        # # Integrate over the frequency range of interest
        # # For example, for perceived loudness, you might focus on the range 20 Hz - 20 kHz
        # freq = np.fft.fftfreq(len(signal), 1 / sample_rate)
        # # mask = (freq >= 20) & (freq <= 20000)
        # mask = (freq > 2000) & (freq <= 5000)
        # power_in_range = power_spectrum[mask]

        # # Calculate loudness metric (e.g., RMS power)
        # rms_power = np.sqrt(np.mean(power_in_range))

        # return rms_power

    
    def _output_settings(self):
        LOGGER.debug('Sound monitoring starting.')
        LOGGER.debug(f'- Microphone ID : {self.microphone_id}')
        LOGGER.debug(f'           name : {self.microphone_name}')
        LOGGER.debug(f'- Channels      : {self._channels}')
        LOGGER.debug(f'- Format        : {self._format}')
        LOGGER.debug(f'- Frame count   : {self._frame_count}')
        LOGGER.debug(f'- Sample rate   : {self._sample_rate}')
        LOGGER.debug(f'- Trigger cnt   : {self._trigger_count}')
        LOGGER.debug(f'- Snd Threshold : {self._sound_threshold}')
        LOGGER.debug(f'- Sound CB      : {self._sound_trigger_callback.__name__}')
        LOGGER.debug(f'- Silence CB    : {self._silence_trigger_callback.__name__}')

    def _monitor(self):
        self._output_settings()
        LOGGER.debug('Listening...')
        was_silent: bool = True
        sound_cnt: int  = -1
        silent_cnt: int = -1
        self._start_time = time()
        try:
            # Sound status changes when trigger_count samples either exceed or are less than the threshold
            # i.e. once sound is detected,   it takes 3 silence segments to trigger silence_detected.
            #      once silence is detected, it takes 3 sound segments to trigger sound_detected.
            while self.is_listening:
                raw_data = self._get_audio_stream_data()
                # Convert buffer to numpy array
                np_data  = np.frombuffer(raw_data, dtype=np.short)[-self._frame_count:]
                sound_detected = self._is_sound_detected2(np_data, self._sound_threshold)
                if sound_detected:
                    silent_cnt = 0
                    if was_silent:
                        sound_cnt += 1
                        if sound_cnt >= self._trigger_count:
                            if self._sound_trigger_callback is not None:
                                self._sound_trigger_callback()
                            was_silent = False
                            LOGGER.debug(f'Sound detected. [Threshold: {self._sound_threshold} | Samples: {self._sample_list}')

                else: # Currently identified as silent
                    sound_cnt = 0
                    if not was_silent:
                        silent_cnt += 1
                        if silent_cnt >= self._trigger_count:
                            if self._silence_trigger_callback is not None:
                                self._silence_trigger_callback()
                            was_silent = True
                            LOGGER.debug(f'Silence detected. [Threshold: {self._sound_threshold} | Samples: {self._sample_list}')

                if self.capture_data:
                    samples = [f'{x:.4f}' for x in self._sample_list]
                    capture_line = f'{not was_silent}, {self._sound_threshold}, {self.loudness:.4f}, {", ".join(samples)}\n'
                    with self._capture_file.open("a") as f:
                        f.write(capture_line)
        
        except Exception as ex:
            LOGGER.exception(f'Uh oh - {ex}')
            self.stop()
            
        self._elapsed_secs = float(f"{(time() - self._start_time):7.2}")
        self._start_time = 0

    def _get_audio_stream_data(self) -> bytes:
        # Loop while buffer fills
        while self._stream.get_read_available() < self._frame_count: 
            sleep(0.01)
        
        # Read buffer size number of frames
        num_frames = self._stream.get_read_available()
        frames = self._stream.read(num_frames, exception_on_overflow=False)
        
        return frames


    def _is_sound_detected2(self, signal_data: np.ndarray, threshold) -> bool:
        self._loudness = self._calculate_loudness(signal=signal_data, sample_rate=self._sample_rate)

        self._sample_list.append(float(f'{self._loudness:>4f}'))
        sound_detected = True if self._loudness > threshold else False
        if len(self._sample_list) > self._trigger_count:
            # Keep only _trigger_count entries in list
            self._sample_list = self._sample_list[-self._trigger_count:]
        return sound_detected


# -------------------------------------------------------------------------------------
# -- Test routines --------------------------------------------------------------------
def _output_audio_device_report():
    pa = pyaudio.PyAudio()
    default_host_api = pa.get_default_host_api_info().get('index')
    for h_idx in range(pa.get_host_api_count()):
        api_info = pa.get_host_api_info_by_index(h_idx)
        num_devices = api_info.get('deviceCount')
        dflt_i_idx = api_info.get('defaultInputDevice')
        dflt_o_idx = api_info.get('defaultOutputDevice')
        api_name   = api_info.get('name')
        LOGGER.info('='*93)
        if h_idx == default_host_api:
            LOGGER.success(f'Host API [{h_idx:1}] - {api_name} {" [DEFAULT]" if h_idx == default_host_api else ""}')
        else:
            LOGGER.info(f'Host API [{h_idx:1}] - {api_name} {" [DEFAULT]" if h_idx == default_host_api else ""}')
        LOGGER.info(f'devices: {num_devices:2}   default input device: {dflt_i_idx:2}   default output device: {dflt_o_idx:2}')
        LOGGER.info('-'*93)
        LOGGER.info('h / d  idx Name                           ic oc  li lat  lo lat  hi lat  ho lat  Sample Rate')
        LOGGER.info('------ --- ------------------------------ -- --  ------- ------- ------- ------- -----------')
        for d_idx in range(api_info.get('deviceCount')):
            device = pa.get_device_info_by_host_api_device_index(h_idx, d_idx)
            if device.get('index') in [dflt_i_idx, dflt_o_idx]:
                log_level = "SUCCESS"
            else:
                log_level = "INFO"
            dev_idx     = device.get('index')
            dev_name    = device.get('name')
            i_channels  = device.get('maxInputChannels')
            o_channels  = device.get('maxOutputChannels')
            li_latency  = device.get('defaultLowInputLatency')
            lo_latency  = device.get('defaultLowOutputLatency')
            hi_latency  = device.get('defaultHighInputLatency')
            ho_latency  = device.get('defaultHighOutputLatency')
            sample_rate = device.get('defaultSampleRate')
            LOGGER.log(log_level,f'[{h_idx:1},{d_idx:2}] {dev_idx:3} {dev_name[:30]:30} {i_channels:2} {o_channels:2}  {li_latency:7.5f} {lo_latency:7.5f} {hi_latency:7.5f} {ho_latency:7.5f} {sample_rate:12.0f}')

    LOGGER.info('')
    LOGGER.info('LEGEND - ic    : Max Input Channels          oc    : Max Output Channels)')
    LOGGER.info('         li lat: Default Low Input Latency   lo lat: Default Low Output Latency')
    LOGGER.info('         hi lat: Default High Input Latency  ho lat: Default High Output Latency')
    LOGGER.info('')

__STOP_REQUESTED = False
def __stop_handler(signum, frame):
    global __STOP_REQUESTED
    __STOP_REQUESTED = True


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
        log_format = lh.DEFAULT_DEBUG_LOGFMT2
    elif args.verbose == 1:
        log_level = "DEBUG"
        log_format = lh.DEFAULT_DEBUG_LOGFMT
    else:
        log_level = "INFO"
        log_format = lh.DEFAULT_CONSOLE_LOGFMT

    lh.configure_logger(log_level=log_level, log_format=log_format)
    LOGGER.debug(f'Log level set to {log_level}')

    OSHelper.enable_ctrl_c_handler(__stop_handler)
    snd_monitor = SoundDetector(frame_count=args.size,
                                sample_rate=args.rate,
                                sound_threshold=args.threshold,
                                trigger_cnt=args.count)
    
    _output_audio_device_report()
    # snd_monitor.capture_path = './docs'
    snd_monitor.capture_data = True
    snd_monitor.start()
    while not __STOP_REQUESTED:
        loudness = snd_monitor._loudness
        LOGGER.info(f'Loudness: {loudness:8.4f}')
        sleep(1)

    snd_monitor.stop()
    LOGGER.info("That's all folks!")
