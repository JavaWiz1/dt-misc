"""
Module to retrieve location data based on 
- GPS Coordinates
- Address
- Landmark name
- Zip code

NOTE:

Requires a FREE API Key from https://geocode.maps.co

See set_api_tokens.exe (dt-cli-tools) for caching the token.
"""
import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from time import sleep
from typing import Dict, Tuple

import requests
from loguru import logger as LOGGER
from timezonefinder import TimezoneFinder

import dt_tools.logger.logging_helper as lh
from dt_tools.misc.helpers import ApiTokenHelper as api_helper


# ============================================================================================
class _GeoLoc_Control:
    API_KEY = api_helper.get_api_token('geocode.maps.co')
    API_ENABLED = API_KEY is not None
    BASE_URL = 'https://geocode.maps.co'
    ADDRESS_URI = 'search'
    LAT_LON_URI = 'reverse'
    GEOLOC_CACHE_FILENM = pathlib.Path('~').expanduser().absolute() / ".IpHelper" / 'geoloc_cache.json'

# ============================================================================================
@dataclass
class LocationCache:
    cache: Dict[str, dict] = field(default_factory=dict)
    valid_cache: bool = True

    def __post_init__(self):
        if not _GeoLoc_Control.API_ENABLED:
            LOGGER.trace('GeoLoc API key not defined, cache lookup only.')

        self.load()
        if self.valid_cache:
            LOGGER.trace(f'Location cache loaded with {len(self.cache)} entries.')
        else:
            LOGGER.trace('Cache does not exist and could not be created.')

    def __del__(self):
        if self.valid_cache:
            self.save()
            LOGGER.debug(f'Location cache saved with {len(self.cache)} entries to {_GeoLoc_Control.GEOLOC_CACHE_FILENM}')

    def save(self):
        if self.valid_cache:
            cache_file = _GeoLoc_Control.GEOLOC_CACHE_FILENM
            cache_file.write_text(json.dumps(self.cache,indent=2), encoding='UTF-8')

    def load(self):
        cache_file = _GeoLoc_Control.GEOLOC_CACHE_FILENM
        if cache_file.exists():
            self.cache = json.loads(cache_file.read_text(encoding='UTF-8'))
        elif cache_file.parent.exists():
            self.cache = {}
        else:
            cache_file.parent.mkdir(parents=True)

    @lh.logger_wraps()
    def clear(self):
        cache_file = pathlib.Path(_GeoLoc_Control.GEOLOC_CACHE_FILENM)
        if cache_file.exists():
            LOGGER.warning(f'{len(self.cache)} GeoLoc cache entries cleared.')
            cache_file.unlink(missing_ok=True)
            self.cache = {}

    def exists(self, key) -> bool:
        return key in self.cache.keys()
    
    def get(self, key) -> dict:
        return self.cache.get(key, None)
    
    def add(self, key, data):
        if self.exists(key):
            LOGGER.error(f'{key} - ALREADY EXISTS IN CACHE')
        self.cache[key] = data

LOCATION_CACHE: LocationCache = LocationCache()

# ============================================================================================
class GeoLocation:
    """
    Class to represent GPS Location, with interfaces to populate via 
    - GPS Location (latitude, longitude)
    - Address (House, Street, City, State, Zip)
    - Address (formattet string)
    - Landmark (For example- Statue of Liberty or Mount Rushmore)
    - Zip 

    """
    lat: float = None
    lon: float = None
    display_name: str = None
    house: int = None
    street: str = None
    city: str = None
    county: str = None
    state: str = None
    zip: int = None
    ip: str = None
    tz_name: str = None

    _tf: TimezoneFinder = TimezoneFinder()
    _json_payload: dict = None
    _last_call: datetime = datetime.now()

    @property
    def address(self) -> str:
        if self.city is None and self.state is None:
            return ''
        address = ''
        if self.house:
            address += f'{self.house} '
        if self.street:
            address += f'{self.street}, '
        
        if self.city:
            address += f"{self.city}, "
        elif self.county:
            address += f'{self.county.replace("County","")}, '
        
        if self.state:
            address += f'{self.state}, '
        if self.zip:
            address += f'{self.zip}, '

        if self.country:
            address += f'{self.country.upper()}'

        return address
        
    @property
    def lat_lon(self) -> str:
        """Return latitude longitude as a comma seperated string"""
        if self.lat is None or self.lon is None:
            return ''
        return f'{float(self.lat):.7f},{float(self.lon):.7f}'

    @lh.logger_wraps()
    def _clear_location_data(self):
        self.lat = None
        self.lon = None
        self.display_name = None
        self.house = None
        self.street = None
        self.city = None
        self.county = None
        self.state = None
        self.zip = None
        self.country = None
        self.ip = None
        self.tz_name = None
        self._json_payload = None
        LOGGER.trace('Location data cleared.')

    @lh.logger_wraps()
    def _load_location_data_from_cache(self, key: str) -> bool:
        if LOCATION_CACHE.exists(key):        
            loc_dict = LOCATION_CACHE.get(key)
            self.lat = loc_dict.get('lat')
            self.lon = loc_dict.get('lon')
            self.display_name = loc_dict.get('display_name')
            self.house = loc_dict.get('house')
            self.street = loc_dict.get('street')
            self.city = loc_dict.get('city')
            self.county = loc_dict.get('county')
            self.state = loc_dict.get('state')
            self.zip = loc_dict.get('zip')
            self.country = loc_dict.get('country')
            self.ip = loc_dict.get('ip')
            self.tz_name = loc_dict.get('tz_name')
            LOGGER.debug(f'({self.lat_lon}) retrieved from cache')
            return True
        
        return False
    
    @lh.logger_wraps()
    def get_location_via_lat_lon(self, lat: float, lon: float) -> bool:
        """Retrieve address location based on lat/lon coordinates"""
        self._clear_location_data()
        self.lat = lat
        self.lon = lon
        loc_dict = None
        if self._load_location_data_from_cache(self.lat_lon):
            LOGGER.debug('-> Loaded from cache.')
        elif not _GeoLoc_Control.API_ENABLED:
            return False
        else:
            url = f"{_GeoLoc_Control.BASE_URL}/{_GeoLoc_Control.LAT_LON_URI}?api_key={_GeoLoc_Control.API_KEY}&lat={self.lat}&lon={self.lon}"
            LOGGER.trace(f'GEOLOC url: {url}')
            loc_dict = self._api_call(url)

        if loc_dict:
            addr_dict: dict = loc_dict.get('address', {})
            self.display_name = loc_dict['display_name']
            self.house = addr_dict.get('house_number', None)
            token = addr_dict.get('road', None)
            if token is None:
                token = addr_dict.get('street', None)
            self.street = token
            token = addr_dict.get('city', None)
            if token is None:
                token = addr_dict.get('own', None)
            if token is None:
                token = addr_dict.get('hamlet', None)
            self.city = token
            self.county = addr_dict.get('county', None)
            self.state = addr_dict.get('state', None)
            self.country = addr_dict.get('country_code', None)
            self.zip = addr_dict.get('postalcode', None)
            # amenity: xxxx,  residential: cimarrone, village: Spring Lake, municipality: Spring Lake Township, neighbourhood: south slope, suburb: brooklyn, city: new york, state: new york
            return True
        
        return False
    
    @lh.logger_wraps()
    def get_location_via_address_string(self, address: str, clear_existing: bool = True) -> bool:
        """
        Retrieve location based on street address

        Required:
            address : typically house street, city, state, zip

        Returns:
            bool: True if location identified, False if not found.
        """
        if not _GeoLoc_Control.API_ENABLED:
            return False

        if clear_existing:
            self._clear_location_data()
        url = f"{_GeoLoc_Control.BASE_URL}/{_GeoLoc_Control.ADDRESS_URI}?api_key={_GeoLoc_Control.API_KEY}&q={address}"
        LOGGER.trace(f'GEOLOC url: {url}')
        loc_dict = self._api_call(url)
        self._populate_via_payload(loc_dict)
        return loc_dict is not None # Found
        
    def get_location_via_landmark(self, landmark: str) -> bool:
        """
        Retrieve location based on landmark name.

        Required:
            landmark (str): Landmark name (ie. Statue of Liberty)

        Returns:
            bool: True if location identified, False if not found.
        """
        if not _GeoLoc_Control.API_ENABLED:
            return False
        
        return self.get_location_via_address_string(address=landmark)
        
    @lh.logger_wraps()
    def get_location_via_address(self, city: str, state: str, house: int=None, street: str=None, zip: int=None) -> bool:
        """
        Retrieve location based on street address
        
        Required:
            city, state

        Optional:
            house, street, zip

        Returns:
            bool: True if location identified, False if not found.
        """
        self._clear_location_data()
        if not _GeoLoc_Control.API_ENABLED:
            return False
        
        # Load fields so self.address populates
        self.house = house
        self.street = street
        self.city = city
        self.state = state
        self.zip = zip
        return self.get_location_via_address_string(self.address, clear_existing=False)
    
    
    @lh.logger_wraps()
    def get_location_via_zip(self, zip: str, country_cd: str = None) -> bool:
        """Retrieve location based on zip code"""
        self._clear_location_data()
        self.zip = zip
        if not _GeoLoc_Control.API_ENABLED:
            return False

        url = f"{_GeoLoc_Control.BASE_URL}/{_GeoLoc_Control.ADDRESS_URI}?api_key={_GeoLoc_Control.API_KEY}&postalcode={self.zip}"
        if country_cd is not None:
            url = f'{url}&country={country_cd}'
        loc_dict = self._api_call(url)
        if loc_dict:
            self._populate_via_payload(loc_dict)
            return True
        
        return False
    
    @lh.logger_wraps()
    def get_location_via_ip(self) -> bool:
        """Retrieve location info based on IP address"""
        self._clear_location_data()
        # Retrieve public IP address
        resp = requests.get('http://ip-api.com/json/')
        resp_json = resp.json()
        if resp_json.get('status') == "success":
            ip = resp_json.get('query')
            self.lat = resp_json.get('lat')
            self.lon = resp_json.get('lon')
            self.city = resp_json.get('city')
            self.country = resp_json.get('countryCode')
            self.state = resp_json.get('region')
            self.zip = resp_json.get('zip')
            self.ip = ip
            self.tz_name = resp_json.get('timezone')
            self._json_payload = resp_json
            LOGGER.debug(f'External IP identified as: {ip}')
            return True
        
        self.lat = 0.0
        self.lon = 0.0
        LOGGER.error('Unable to determine ip for location identification')
        return False

    # ---------------------------------------------------------------------------------
    @lh.logger_wraps()
    def _api_call(self, url) -> Dict:
        while (datetime.now() - self._last_call).total_seconds() < 1.1:
            LOGGER.trace('throttle.')
            sleep(.1)

        LOGGER.trace(f'GEOLOC url: {url}')
        loc_dict: dict = None
        throttle = True
        while throttle:
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    json_data = resp.json()                
                    LOGGER.trace(resp.json())
                    throttle = False
                    if isinstance(json_data, dict):
                        loc_dict = json_data
                    elif isinstance(json_data, list):
                        if len(json_data) > 0:
                            loc_dict = json_data[0]
                        else:
                            LOGGER.warning(f'GEOLOC not found for {url}')
                    else:
                        LOGGER.error(f'Unknown response: {url} - {json_data}')
                elif resp.status_code == 429:
                    LOGGER.debug('GEOLOC throttle...')
                    sleep(1.1)
                else:
                    throttle = False
                    LOGGER.warning(f'URL: {url}  RC: {resp.status_code} - {resp.text}')            

            except Exception as ex:
                LOGGER.exception(f'Unable to get geoloc: {url} - {repr(ex)}')

        if loc_dict:
            self._json_payload = loc_dict
            self.lat = float(loc_dict['lat'])
            self.lon = float(loc_dict['lon'])
            self.tz_name = self._tf.timezone_at(lat=self.lat, lng=self.lon)
            loc_dict['tz_name'] = self.tz_name
            if not LOCATION_CACHE.exists(self.lat_lon):
                LOCATION_CACHE.add(self.lat_lon, loc_dict)
                LOGGER.debug(f'({self.lat_lon}) added to cache, {len(LOCATION_CACHE.cache)} total entries.')
        
        return loc_dict

    @lh.logger_wraps()
    def _populate_via_payload(self, payload: dict):
        if payload is None:
            return

        self.display_name = payload.get('display_name') if self.display_name is None else self.display_name
        if self.display_name is not None:
            tokens = self.display_name.split(', ')
            tokens.reverse()
            self.country = tokens[0] if self.country is None else self.country
            if tokens[1].isnumeric():
                LOGGER.debug(f' display_name: {self.display_name}')
                LOGGER.debug(f' tokens      : {tokens}')
                self.zip = tokens[1] if self.zip is None else self.zip
                self.state = tokens[2] if self.state is None else self.state
                self.county = tokens[3] if self.county is None else self.county
                if len(tokens) > 4:
                    self.city = tokens[4] if self.city is None else self.city

            self.house = None
            self.street = None
            LOGGER.debug(self.to_string())


    def GPS_dms_to_dd(lat_dms:Tuple[float, float, float], lat_ref: str, lon_dms: Tuple[float, float, float], lon_ref: str) -> Tuple[float, float]:
        """
        Return Lat/Lon decimal degrees (dd) from Lat/Long Degree, Minute Seconds (dms) coordinates.

        Args:
            lat_dms: (degree, minute, sec)
            lat_ref: N or S
            lon_dmsL (degree, minute, sec)
            lon_ref: E or W

        Returns:
            lat_dd: decimal degree - latitude 
            lon_dd: decimal degree - longitude
            (0.0, 0.0) on ERROR
        """
        try:
            #          Degree   + (min/60)        + (seconds/3600)
            lat_dd = float(lat_dms[0]) + (float(lat_dms[1])/60) + (float(lat_dms[2])/3600)
            lon_dd = float(lon_dms[0]) + (float(lon_dms[1])/60) + (float(lon_dms[2])/3600)
            if lat_ref.lower() == "s":
                lat_dd *= -1
            if lon_ref.lower() == "w":
                lon_dd *= -1
        except Exception as ex:
            LOGGER.error(f'Lat/Lon: {repr(ex)}')
            lat_dd = 0.0
            lon_dd = 0.0

        lat_dd = float(f'{lat_dd:.4f}')
        lon_dd = float(f'{lon_dd:.4f}')
        
        return (lat_dd, lon_dd)

    def to_string(self) -> str:
        output = ''
        for attr in dir(self):
            value = getattr(self, attr)
            if value is not None and not callable(value) and not attr.startswith('_'):
                output += f'{attr:15} : {getattr(self, attr)}\n'
        
        return output

def _print_object(obj):
    for line in obj.to_string().splitlines():
        LOGGER.info(f'  {line}')
    payload = getattr(obj,'_json_payload')
    if payload is not None:
        LOGGER.info('  Payload-')
        for k, v in payload.items():
            LOGGER.info(f'    {k:15} {v}')

if __name__ == "__main__":
    import sys

    lh.configure_logger(log_level='INFO', brightness=False)
    if '-c' in sys.argv:
        LOCATION_CACHE.clear()
        
    helper = GeoLocation()

    print('')
    address = '4833 Nahane Way, Saint Johns, FL'
    LOGGER.warning(f'Address: {address}')
    helper.get_location_via_address_string(address)
    LOGGER.info('Returns:')
    _print_object(helper)

    print('')
    lat = 30.069157
    lon = -81.551387
    LOGGER.warning(f'Location for {lat},{lon}')
    helper.get_location_via_lat_lon(lat=lat, lon=lon)
    LOGGER.info('Returns:')
    _print_object(helper)

    print('')
    zip = 32259
    LOGGER.warning(f'Zip: {zip}')
    helper.get_location_via_zip(zip, "US")
    LOGGER.info('Returns:')
    _print_object(helper)

    print('')
    address = "Matterhorn"
    LOGGER.warning(f'Address: {address}')
    helper.get_location_via_address_string(address)
    LOGGER.info('Returns:')
    _print_object(helper)
