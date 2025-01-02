"""
weather.py - current, forecasts, alerts

This module leverages 3rd party service (weatherapi.com) to retrieve detailed weather
information based on GeloLocation (latitude, longitude).

Location information can be retrieved based on:
- GeoLocation (lat/lon)
- US address (string or components (street, city, state, zip))
- Internet IP address

"""
import datetime
import json
import pathlib
from dataclasses import dataclass
from datetime import datetime as dt

import requests
from loguru import logger as LOGGER

import dt_tools.net.net_helper as nh
from dt_tools.misc.census_geoloc import Census_GeoLocation
from dt_tools.misc.helpers import ApiTokenHelper
from dt_tools.misc.sun import Sun
from dt_tools.misc.weather.common import AQI_DESC, WeatherLocation, WeatherSymbols


class CURRENT_WEATHER_SETTINGS:
    API_KEY = ApiTokenHelper.get_api_token(ApiTokenHelper.API_WEATHER_INFO)
    API_AVAILABLE = False if API_KEY is None else True
    BASE_URL = "http://api.weatherapi.com/v1" # 1 million calls per month
    CURRENT_URI = "current.json"
    FORECAST_URI = "forecast.json"
    SEARCH_URI = "search.json"

@dataclass
class CurrentConditions():
    """
    Weather condition class

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
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
    sunrise: datetime.datetime = None
    sunset: datetime.datetime = None
    _connect_retries: int = 0
    _disabled: bool = True

    def __post_init__(self):
        if not CURRENT_WEATHER_SETTINGS.API_AVAILABLE:
            msg = f'No API Token set for {CURRENT_WEATHER_SETTINGS.BASE_URL}.\n'
            msg += 'Use "set_api_tokens" to cache FREE API token.'
            raise ConnectionError(msg)
 
    def set_location_via_lat_lon(self, lat: float, lon: float) -> bool:
        """
        Set weather location based on Geolocation

        Args:
            lat (float): Latitude
            lon (float): Longitude

        Returns:
            bool: True if location successfully set.
        """
        if CURRENT_WEATHER_SETTINGS.API_AVAILABLE:
            self.location = WeatherLocation(lat, lon)
            return self.refresh()
    
        return False
    
    def set_location_via_census_address(self, street: str, city: str = None, state: str = None, zipcd: str = None) -> bool:
        """
        Set location based on address: street, city, state or street, zipcd

        The GeoLocation will be derived based on the address.  NOTE: only US addresses are allowed.

        Args:
            street (str): House number and street name
            city (str, optional): City. Defaults to None.
            state (str, optional): State. Defaults to None.
            zipcd (str, optional): Zip code. Defaults to None.

        Returns:
            bool: True if address is resolved and GeoLocation identified, else False
        """
        # if CURRENT_WEATHER_SETTINGS.API_AVAILABLE:
        #     geo_locs = GeoLocation.lookup_address(street=street, city=city, state=state, zipcd=zipcd)
        #     if len(geo_locs) > 0:
        #         loc = geo_locs[0]
        #         self.location = WeatherLocation(latitude=loc.latitude, longitude=loc.longitude, location_name=loc.address)
        #         return self.refresh()
    
        geo_locs = Census_GeoLocation.lookup_address(street=street, city=city, state=state, zipcd=zipcd)
        if len(geo_locs) > 0:
            loc = geo_locs[0]
            self.location = WeatherLocation(latitude=loc.latitude, longitude=loc.longitude, location_name=loc.address)
            return self.refresh()
        return False
    
    def set_location_via_address(self, address: str) -> bool:
        """
        Set location based on address string

        GeoLocation will be derived based on the address. 

        Args:
            address (str): Address string - i.e. 123 somestree, somecity, somestate, some zip

        Returns:
            bool: True if address is resolved and GeoLocation identified, else False
        """
        from dt_tools.misc.geoloc import GeoLocation as GeoLoc
        if CURRENT_WEATHER_SETTINGS.API_AVAILABLE:
            geo = GeoLoc()
            if geo.get_location_via_address_string(address):
                self.location = WeatherLocation(latitude=geo.lat, longitude=geo.lon, location_name=address)
                return self.refresh()
    
        return False

    def set_location_via_ip(self, ip: str = None) -> bool:
        """
        Set location based on IP address

        The IP should be resolvable on the internet (i.e. local addresses won't work)

        Args:
            ip (str, optional): IP to resolve, if None, The device external address (i.e. from
                service provider will be used). Defaults to None.

        Returns:
            bool: True if IP is resovled to GeoLocation, else False
        """
        if CURRENT_WEATHER_SETTINGS.API_AVAILABLE:
            if ip is None:
                lat, lon = nh.get_lat_lon_for_ip(ip=nh.get_wan_ip()) # self._get_lat_lon_from_ip(nh.get_wan_ip())
            else:
                lat, lon = nh.get_lat_lon_for_ip(ip=ip) # self._get_lat_lon_from_ip(ip)

            self.location = WeatherLocation(lat, lon)
            return self.refresh()
    
        return False


    @property
    def loc_name(self) -> str:
        return '' if self.location is None else self.location.location_name
    
    @loc_name.setter
    def loc_name(self, val: str):
        if self.location is not None:
            self.location.location_name = val

    @property
    def loc_region(self) -> str:
        return '' if self.location is None else self.location.location_region
    
    @loc_region.setter
    def loc_region(self, val: str):
        if self.location is not None:
            self.location.location_region = val
            
 
    @property
    def disabled(self) -> bool:
        """
        Check if location defined, API and connection is available

        Returns:
            bool: False if connection is available, else False
        """
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
        return '' if self.location is None else f'{self.location.latitude},{self.location.longitude}'

    def to_string(self) -> str:
        """
        String representation of the current weather.

        Returns:
            str: _description_
        """
        degree = WeatherSymbols.degree.value
        text =  f'{self.condition}\n'    
        text += f'  Temperature {self.temp}{degree} feels like {self.feels_like}{degree}\n'    
        text += f'  Humidity {self.humidity_pct}%\n'    
        text += f'  Air Quality {self.aqi_text}\n'    
        text += f'  Precipitation {self.precipitation} in.\n'    
        text += f'  Cloud Cover {self.cloud_cover_pct}%, visibility {self.visibility_mi} miles\n'    
        text += f'  Wind {self.wind_speed_mph} mph - {self.wind_direction} with gusts up to {self.wind_gust_mph} mph\n'
        if self.sunrise:
            text += f'  Sunrise at {self.sunrise.strftime("%I:%M %p")} / Sunset at {self.sunset.strftime("%I:%M %p %Z")}'
        return text
    
    def refresh(self, ignore_cache: bool = False) -> bool:
        """
        Refresh current weather

        Args:
            ignore_cache (bool, optional): _description_. Defaults to False.

        Returns:
            bool: _description_
        """
        if ignore_cache:
            return self._refresh_if_stale(elapsed_mins=0)
        return self._refresh_if_stale()
    
    def _refresh_if_stale(self, elapsed_mins: int = 15) -> bool:
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
            LOGGER.debug(f'- Weather being refreshed, last update {elapsed:.2f} minutes ago at {self.last_update}')            
        except Exception as ex:
            LOGGER.trace(f'no prior weather {ex}')
            LOGGER.debug('- Weather being refreshed, last update Unknown')

        target_url=f'{CURRENT_WEATHER_SETTINGS.BASE_URL}/{CURRENT_WEATHER_SETTINGS.CURRENT_URI}?key={CURRENT_WEATHER_SETTINGS.API_KEY}&q={self.lat_long}&aqi=yes'
        LOGGER.debug(f'WEATHER url: {target_url}')
        try:
            resp = requests.get(target_url)
            if resp.status_code == 200:
                LOGGER.debug(json.dumps(resp.json(), indent=2))
                self._load_current_conditions(resp.json())
                self._disabled = False
                if self.sunrise is None:
                    sun = Sun(self.location.latitude, self.location.longitude)
                    try:
                        self.sunrise = sun.get_gps_sunrise()
                    except Exception as ex:
                        LOGGER.error(f'Unable to get sunrise: {ex}')
                    try:
                        self.sunset  = sun.get_gps_sunset()
                    except Exception as ex:
                        LOGGER.error(f'Unable to get sunset: {ex}')
                return True

        except Exception as ex:
            LOGGER.warning('Unable to call weather api')
            LOGGER.warning(f'  URL   : {target_url}')
            LOGGER.exception(f'  ERROR : {repr(ex)}')
            self._connect_retries += 1
            if self._connect_retries > 3:
                print('dt_tools.weather.weather: Unable to reconnect to weather, disabled feature.', file=sys.stderr)
                self._disabled = True
            return False
                
        LOGGER.error(f'Request URL: {target_url}')
        LOGGER.error(f'Response status_code: {resp.status_code}')
        print('dt_tools.weather.weather: Unable to connect to weather, disabled feature.', file=sys.stderr)
        self._disabled = True
        return False

    def _load_current_conditions(self, blob: dict):
        LOGGER.debug('_load_current_conditions()')
        l_block: dict = blob['location']
        w_block: dict = blob['current']
        c_block: dict = w_block.get('condition',{})
        if self.location.location_name is None:
            self.loc_name       = l_block.get('name', '')
        else:
            self.loc_name       = self.location.location_name
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
            self.aqi            = int(w_block["air_quality"]['us-epa-index'])
        except Exception as ex:
            LOGGER.error(f'Unable to determine AQI: {repr(ex)}')
            self.aqi = -1

        self.aqi_text    = AQI_DESC[self.aqi]     
        self.last_update = dt.now()
        
    
    
if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    import sys

    log_lvl = 'DEBUG' if '-v' in sys.argv else 'INFO'
    
    lh.configure_logger(log_level=log_lvl, log_format=lh.DEFAULT_DEBUG_LOGFMT, brightness=False)

    weather = CurrentConditions() # Must create new due to throttle timer
    geo = Census_GeoLocation.lookup_address(street='1812 Edgewood', city="Berkley", state='MI')
    weather.set_location_via_lat_lon(geo[0].latitude, geo[0].longitude)
    LOGGER.success(f'Weather via lat/lon: {weather.lat_long} - {weather.loc_name}')
    for line in weather.to_string().splitlines():
        LOGGER.info(f'  {line}')
    LOGGER.info('')

    addresses = [
        'Nahane Way, Saint Johns, FL, 32259',
        'Duluth, MN',
        'Denver, CO',
        'Portland, OR',
        'Matterhorn',
        'Bora Bora',
        'Puerto Williams, Chile',
        'Longyearbyen'
        ]
    
    for address in addresses:
        weather = CurrentConditions() # Must create new due to throttle timer
        weather.set_location_via_address(address=address)
        LOGGER.success(f'Weather via address: {weather.loc_name}')
        for line in weather.to_string().splitlines():
            LOGGER.info(f'  {line}')
        LOGGER.info('')

