# current weather
# summary forecast
# detailed forecast
# alerts

# text
# speak
import json
import pathlib
import threading
from dataclasses import dataclass
from datetime import datetime as dt

import requests
from loguru import logger as LOGGER

import dt_tools.net.net_helper as nh
from dt_tools.misc.census_geoloc import GeoLocation, GeoLocationAddress
from dt_tools.misc.helpers import ApiTokenHelper
from dt_tools.misc.sound import Accent, Sound

"""
Air Quality Index
"""
AQI_DESC = {
    -1: 'Unknown',
    1: 'Good',
    2: 'Moderate',
    3: 'Degraded',
    4: 'Unhealthy',
    5: 'Very Unhealthy',
    6: 'Hazardous',
}
WIND_DIRECTION_DICT = {
    "N": "North",
    "S": "South",
    "E": "East",
    "W": "West",
}

class WEATHER_SETTINGS:
    API_KEY = ApiTokenHelper.get_api_token(ApiTokenHelper.API_WEATHERINFO)
    API_AVAILABLE = False if API_KEY is None else True
    BASE_URL = "http://api.weatherapi.com/v1" # 1 million calls per month
    CURRENT_URI = "current.json"
    FORECAST_URI = "forecast.json"
    SEARCH_URI = "search.json"

@dataclass
class WeatherLocation():
    latitude: float = 0.0
    longitude: float = 0.0
    location_name: str = None
    location_region: str = None

    def is_initialized(self) -> bool:
        return False if (self.latitude == 0.0 and self.longitude == 0.0) else True

@dataclass
class WeatherConditions():
    location: WeatherLocation = None
    condition: str = None
    _condition_icon: str = None
    temp: float = None
    feels_like: float = None
    wind_direction: str = None
    wind_speed_mph: float = None
    wind_gust_mph: float = None
    humidity_pct: int = None
    cloud_cover_pct: int = None
    visibility_mi: float = None
    precipitation: float = None
    last_update: dt = None
    aqi: int = None
    aqi_text: str = None
    _connect_retries: int = 0
    _speak_thread_id: int = None
    _speak_accent: Accent = Accent.UnitedStates
    _disabled: bool = True

    def __post_init__(self):
        # if self.lat == 0 or self.lon == 0:
        #     # Location not set, use (external) ip to set location
        #     external_ip = self._get_external_ip()
        #     if external_ip:
        #         self.lat, self.lon = self._get_lat_lon_from_ip(external_ip)
        #         LOGGER.warning(f'Location  not set, get via external IP [{external_ip}] - {self.lat_long}')
        # self.refresh_if_stale()
        pass

    def set_location_via_lat_lon(self, lat: float, lon: float) -> bool:
        if WEATHER_SETTINGS.API_AVAILABLE:
            self.location = WeatherLocation(lat, lon)
            self.refresh_if_stale()

    def set_location_via_census_address(self, street: str, city: str = None, state: str = None, zipcd: str = None) -> bool:
        if WEATHER_SETTINGS.API_AVAILABLE:
            geo_locs = GeoLocation.lookup_address(street=street, city=city, state=state, zipcd=zipcd)
            if len(geo_locs) > 0:
                loc = geo_locs[0]
                self.location = WeatherLocation(latitude=loc.latitude, longitude=loc.longitude, location_name=loc.address)
                return self.refresh_if_stale()
    
        return False
    
    def set_location_via_address(self, address: str) -> bool:
        from dt_tools.misc.geoloc import GeoLocation as GeoLoc
        if WEATHER_SETTINGS.API_AVAILABLE:
            geo = GeoLoc()
            if geo.get_location_via_address_string(address):
                self.location = WeatherLocation(latitude=geo.lat, longitude=geo.lon, location_name=geo.display_name)
                return self.refresh_if_stale()
    
        return False

    def set_location_via_ip(self, ip: str = None) -> bool:
        if WEATHER_SETTINGS.API_AVAILABLE:
            if ip is None:
                lat, lon = nh.get_lat_lon_for_ip(ip=nh.get_wan_ip()) # self._get_lat_lon_from_ip(nh.get_wan_ip())
            else:
                lat, lon = nh.get_lat_lon_for_ip(ip=ip) # self._get_lat_lon_from_ip(ip)

            self.location = WeatherLocation(lat, lon)
            return self.refresh_if_stale()
    
        return False

    @property
    def accent(self) -> Accent:
        return self._speak_accent
    
    @accent.setter
    def accent(self, id: str):
        try:
            speak_accent = Accent[id]
        except Exception:
            LOGGER.warning(f'Conditions() invalid accent id [{id}], defaulting to US.')
            speak_accent = Accent.UnitedStates

        LOGGER.warning(f'Conditions() setting accent to: {speak_accent}')
        self._speak_accent = speak_accent

    @property
    def disabled(self) -> bool:
        return self._disabled
    
    @property
    def condition_icon(self) -> str:
        return self._condition_icon
    
    @condition_icon.setter
    def condition_icon(self, value):
        LOGGER.trace(f'icon: {value}')

        icon_filenm_local = value.replace('//cdn.weatherapi.com','./files/icons')
        icon_file = pathlib.Path(icon_filenm_local).absolute()
        if icon_file.exists():
            self._condition_icon = str(icon_file)
        else:
            self._condition_icon = value

    @property
    def lat_long(self) -> str:

        return f'{self.location.latitude},{self.location.longitude}'

    def to_string(self) -> str:
        degree = chr(176)
        text: str = f'Current weather conditions for {self.loc_name} {self.loc_region}. [{self.lat_long}]\n\n'
        text += f'{self.condition}\n'    
        text += f'  Temperature {self.temp}{degree} feels like {self.feels_like}{degree}\n'    
        text += f'  Wind {self.wind_speed_mph} mph - {self.wind_direction}\n'    
        text += f'  Humidity {self.humidity_pct}%\n'    
        text += f'  Cloud Cover {self.cloud_cover_pct}%, visibility {self.visibility_mi} miles\n'    
        text += f'  Precipitation {self.precipitation} in.\n'    
        text += f'  Air Quality {self.aqi_text} [{self.aqi}]\n'    
        return text
    
    def refresh_if_stale(self, elapsed_mins: int = 15) -> bool:
        """
        Refresh weather data if stale.  Default is 15 monutes.
        """
        if self.location is None or not self.location.is_initialized():
            raise ValueError('ABORT - Weather location is NOT initialized.')
        
        elapsed = "UNKNOWN"
        if self.last_update is not None:
            elapsed = (dt.now() - self.last_update).total_seconds() / 60
            if elapsed < elapsed_mins:
                LOGGER.trace('Weather data NOT refreshed')
                return False
        try:
            # will fail if elapsed/last_update not set
            LOGGER.warning(f'- Weather being refreshed, last update {elapsed:.2f} minutes ago at {self.last_update}')            
        except Exception as ex:
            LOGGER.trace(f'no prior weather {ex}')
            LOGGER.warning('- Weather being refreshed, last update Unknown')

        target_url=f'{WEATHER_SETTINGS.BASE_URL}/{WEATHER_SETTINGS.CURRENT_URI}?key={WEATHER_SETTINGS.API_KEY}&q={self.lat_long}&aqi=yes'
        LOGGER.debug(f'WEATHER url: {target_url}')
        try:
            resp = requests.get(target_url)
            if resp.status_code == 200:
                LOGGER.debug(json.dumps(resp.json(), indent=2))
                self._load_current_conditions(resp.json())
                self._disabled = False
                return True
        except Exception as ex:
            LOGGER.warning('Unable to call weather api')
            LOGGER.warning(f'  URL   : {target_url}')
            LOGGER.warning(f'  ERROR : {repr(ex)}')
            self._connect_retries += 1
            if self._connect_retries > 3:
                LOGGER.error('Unable to reconnect to weather, disabled feature.')
                self._disabled = True
                # cfg.weather_enabled = False
            return False
                
        LOGGER.error(f'Request URL: {target_url}')
        LOGGER.error(f'Response status_code: {resp.status_code}')
        self._disabled = True
        return False

    def speak_current_conditions(self) -> int:
        if self._speak_thread_id is not None and self._speak_thread_id > 0:
            LOGGER.warning('Speak thread in process... Ignoring request.')
            return False
        
        t = threading.Thread(target=self._speak_current_conditions_thread)
        t.start()
        self._speak_thread_id = t.native_id

    def _speak_current_conditions_thread(self):
        wind_direction = self._speak_direction(self.wind_direction)
        # cloud_cover_pct = self._speak_normalize_number(weather.cloud_cover_pct)
        temp = self._speak_normalize_number(self.temp)
        feels_like = self._speak_normalize_number(self.feels_like)
        humidity_pct = self._speak_normalize_number(self.humidity_pct)
        # precipitation = self._speak_normalize_number(weather.precipitation)
        visibility_mi = self._speak_normalize_number(self.visibility_mi)
        wind_speed_mph = self._speak_normalize_number(self.wind_speed_mph)
        wind_gust_mph = self._speak_normalize_number(self.wind_gust_mph)        
        time_now = dt.now().strftime("%I:%M%p")
        text = f'Current weather conditions at {time_now}.  '
        text += f'{self.condition}.  Temperature {temp}, feels like {feels_like}.  '
        text += f'{humidity_pct}% humidity, air quality is {self.aqi_text}.  '
        text += f'Visibility {visibility_mi} miles.  '
        text += f'Wind {wind_direction} {wind_speed_mph} mph, gusts up to {wind_gust_mph} mph.'
        ret = Sound().speak(text, speed=1.25, accent=self.accent)
        LOGGER.success('Speak current weather conditions complete.')
        self._speak_thread_id = None
        return ret
    
    @property
    def speaking(self) -> bool:
        return False if self._speak_thread_id is None else True
    
    def _speak_normalize_number(self, token) -> str:
        try:
            num = float(token)
            frac = num % 1
            resp = str(token).split('.')[0] if frac == 0 else token
        except Exception as ex:
            print(ex)
            resp = token 
        
        return resp

    def _speak_direction(self, token: str) -> str:
        resp = ''
        for char in token:
            resp += f' {WIND_DIRECTION_DICT[char]}'
        return resp.lstrip()

    def _load_current_conditions(self, blob: dict):
        l_block: dict = blob['location']
        w_block: dict = blob['current']
        c_block: dict = w_block.get('condition',{})
        self.loc_name           = l_block.get('name', '')
        self.loc_region         = l_block.get('region', '')
        self.condition          = c_block.get('text','')  # w_block["condition"]["text"]
        self.condition_icon     = c_block.get('icon', '') # w_block["condition"]["icon"]
        self.temp               = float(w_block.get("temp_f", -1))
        self.feels_like         = float(w_block.get("feelslike_f", -1)) 
        self.wind_direction     = w_block.get("wind_dir", '')
        self.wind_speed_mph     = float(w_block.get("wind_mph", -1))
        self.wind_gust_mph      = float(w_block.get("gust_mph", -1))
        self.humidity_pct       = float(w_block.get("humidity", -1))
        self.cloud_cover_pct    = float(w_block.get("cloud", -1))
        self.visibility_mi      = float(w_block.get("vis_miles", -1))
        self.precipitation      = float(w_block.get("precip_in", -1))
        try:
            self.aqi                = int(w_block["air_quality"]['us-epa-index'])
        except Exception as ex:
            LOGGER.error(f'Unable to determine AQI: {repr(ex)}')
            self.aqi = -1
        self.aqi_text           = AQI_DESC[self.aqi]     
        self.last_update = dt.now()
        
    # def _get_external_ip(self) -> str:
    #     # resp = requests.get('http://ifcfg.me')
    #     resp = requests.get('https://api.ipify.org')
    #     external_ip = resp.text
    #     LOGGER.debug(f'External IP identified as: {external_ip}')
    #     return external_ip
    
    # def _get_lat_lon_from_ip(self, ip: str) -> Tuple[float, float]:
    #     lat: float = 0.0
    #     lon: float = 0.0
    #     url = f'https://ipapi.co/{ip}/latlong/'
    #     #headers = {'user-agent': 'ipapi.co/#ipapi-python-v1.0.4'} 
    #     headers = {'user-agent': 'ipapi.co/#custom'}               
    #     resp = requests.get(url, headers=headers)
    #     if resp.text.count(',') == 1:
    #         token = resp.text.split(',')
    #         lat = token[0]
    #         lon = token[1]
    #     LOGGER.warning(f'Lat/Lon identified - ip: {ip}  lat: {lat}  lon: {lon}')
    #     return lat, lon

    
if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    from time import sleep

    lh.configure_logger(log_level='INFO', log_format=lh.DEFAULT_CONSOLE_LOGFMT)

    weather = WeatherConditions()
    weather.set_location_via_address(address='4833 Nahane Way, Saint Johns, FL, 32259')
    LOGGER.info(f'Weather via address: {weather.loc_name}\n{weather.to_string()}')
    weather.speak_current_conditions()
    while weather.speaking:
        print('.', end='')
        sleep(.25)
    print('')

    weather = WeatherConditions()
    weather.set_location_via_census_address(street='4833 Nahane Way', city='St. Johns', state='FL')
    LOGGER.info(f'Weather via address: {weather.loc_name}\n{weather.to_string()}')
    
    weather = WeatherConditions()
    weather.set_location_via_ip()
    LOGGER.info(f'Weather via IP:\n{weather.to_string()}')

    weather = WeatherConditions()
    geo = GeoLocation.lookup_address(street='1812 Edgewood', city="Berkley", state='MI')
    weather.set_location_via_lat_lon(geo[0].latitude, geo[0].longitude)
    LOGGER.info(f'Weather via lat/lon:\n{weather.to_string()}')
    weather.speak_current_conditions()
    while weather.speaking:
        print('.', end='')
        sleep(.25)
    print('')

