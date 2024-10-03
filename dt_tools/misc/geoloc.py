import json
import pathlib
from dataclasses import dataclass, field
from pprint import pformat
from typing import Tuple, Dict

import requests
from loguru import logger as LOGGER
from dt_tools.misc.helpers import ApiTokenHelper as api_helper

class _GeoLoc_Control:
    # API_KEY = cfg._GEOLOC_API_KEY
    API_KEY = api_helper.get_api_token('geocode.maps.co')
    API_ENABLED = API_KEY is not None
    BASE_URL = 'https://geocode.maps.co'
    ADDRESS_URI = 'search'
    LAT_LON_URI = 'reverse'
    CACHE_FILENM = './files/geoloc_cache.json'

@dataclass
class LocationCache:
    cache: Dict[str, dict] = field(default_factory=dict)
    valid_cache: bool = True

    def __post_init__(self):
        # if not cfg.geoloc_enabled:
        if not _GeoLoc_Control.API_ENABLED:
            LOGGER.warning('GeoLoc API key not defined, cache lookup only.')

        self.load()
        if self.valid_cache:
            LOGGER.success(f'Location cache loaded with {len(self.cache)} entries.')
        else:
            LOGGER.warning('Cache does not exist and could not be created.')

    def __del__(self):
        if self.valid_cache:
            self.save()
            LOGGER.success(f'Location cache saved with {len(self.cache)} entries to {_GeoLoc_Control.CACHE_FILENM}')

    def save(self):
        if self.valid_cache:
            cache_file = pathlib.Path(_GeoLoc_Control.CACHE_FILENM)
            cache_file.write_text(json.dumps(self.cache,indent=2), encoding='UTF-8')

    def load(self):
        cache_file = pathlib.Path(_GeoLoc_Control.CACHE_FILENM)
        if cache_file.exists():
            self.cache = json.loads(cache_file.read_text(encoding='UTF-8'))
        elif cache_file.parent.exists():
            self.cache = {}
        else:
            self.valid_cache = False

    def exists(self, key) -> bool:
        return key in self.cache.keys()
    
    def get(self, key) -> dict:
        return self.cache.get(key, None)
    
    def add(self, key, data):
        if self.exists(key):
            LOGGER.error(f'{key} - ALREADY EXISTS IN CACHE')
        self.cache[key] = data

LOCATION_CACHE: LocationCache = LocationCache()

class GeoLocation:
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
    _json_payload: dict = None

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
        if self.country:
            address += f'{self.country.upper()}'

        return address
        
    @property
    def lat_lon(self) -> str:
        """Return latitude longitude as a comma seperated string"""
        if self.lat is None or self.lon is None:
            return ''
        return f'{float(self.lat):.5f},{float(self.lon):.5f}'
    
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
        self._json_payload = None
        LOGGER.debug('Location data cleared.')

    def get_location_via_lat_lon(self, lat: float, lon: float) -> bool:
        """Retrieve address location based on lat/lon coordinates"""
        self._clear_location_data()
        self.lat = lat
        self.lon = lon
        loc_dict = None
        if LOCATION_CACHE.exists(self.lat_lon):
            loc_dict = LOCATION_CACHE.get(self.lat_lon)
            LOGGER.info(f'({self.lat_lon}) retrieved from cache')
        elif not _GeoLoc_Control.API_ENABLED:
            return False
        else:
            url = f"{_GeoLoc_Control.BASE_URL}/{_GeoLoc_Control.LAT_LON_URI}?api_key={_GeoLoc_Control.API_KEY}&lat={self.lat}&lon={self.lon}"
            LOGGER.debug(f'GEOLOC url: {url}')
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    LOGGER.trace(resp.json())
                    loc_dict = resp.json()
                    LOCATION_CACHE.add(self.lat_lon, loc_dict)
                    LOGGER.success(f'({self.lat_lon}) added to cache, {len(LOCATION_CACHE.cache)} total entries.')
            except Exception as ex:
                LOGGER.exception(f'Unable to get geoloc: {repr(ex)}')
                return False

        if loc_dict:
            self._json_payload = loc_dict
            addr_dict: dict = loc_dict['address']
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
            self.zip = addr_dict.get('postcode', None)
            # amenity: xxxx,  residential: cimarrone, village: Spring Lake, municipality: Spring Lake Township, neighbourhood: south slope, suburb: brooklyn, city: new york, state: new york
            return True
        
        LOGGER.error(f'Request URL: {url}')        
        LOGGER.error(f'Response status code: {resp.status_code}')
        return False
    
    def get_location_via_address_string(self, address: str) -> bool:
        """
        Retrieve location based on street address
        Required:
            address : typically house street, city, state, zip
        """
        if not _GeoLoc_Control.API_ENABLED:
            return False

        self._clear_location_data()
        url = f"{_GeoLoc_Control.BASE_URL}/{_GeoLoc_Control.ADDRESS_URI}?api_key={_GeoLoc_Control.API_KEY}&q={address}"
        LOGGER.debug(f'GEOLOC url: {url}')
        found = False
        resp = requests.get(url)
        if resp.status_code == 200:
            found = True
            json_data = resp.json()
            LOGGER.trace(json_data)
            if isinstance(json_data, dict):         
                loc_dict = json_data
            elif isinstance(json_data, list):
                if len(json_data) > 0:
                    loc_dict = resp.json()[0]
                else:
                    LOGGER.debug(f'GEOLOC not found for {address}')
                    found = False
            else:
                # LOGGER.warning(resp.json())
                found = False
        else:
            LOGGER.error(f'Request URL: {url}')        
            LOGGER.error(f'Response status code: {resp.status_code}')

        if found:
            self._json_payload = loc_dict
            self.lat = loc_dict['lat']
            self.lon = loc_dict['lon']
            self.display_name = loc_dict['display_name']

        return found
        

    def get_location_via_address(self, city: str, state: str, house: int=None, street: str=None, zip: int=None) -> bool:
        """
        Retrieve location based on street address
        Required:
            city, state
        Optional:
            house, street, zip
        """
        self._clear_location_data()
        if not _GeoLoc_Control.API_ENABLED:
            return False
        self.house = house
        self.street = street
        self.city = city
        self.state = state
        self.zip = zip
        return self.get_location_via_address_string(self.address)
    
    
    def get_location_via_zip(self, zip: str) -> bool:
        """Retrieve location based on zip code"""
        self._clear_location_data()
        self.zip = zip
        if not _GeoLoc_Control.API_ENABLED:
            return False

        url = f"{_GeoLoc_Control.BASE_URL}/{_GeoLoc_Control.ADDRESS_URI}?api_key={_GeoLoc_Control.API_KEY}&postalcode={self.zip}"
        LOGGER.debug(f'GEOLOC url: {url}')
        resp = requests.get(url)
        if resp.status_code == 200:
            LOGGER.trace(pformat(resp.json()))            
            loc_dict: dict = resp.json()[0]
            self.lat = loc_dict['lat']
            self.lon = loc_dict['lon']
            self.display_name = loc_dict['display_name']
            self._json_payload = loc_dict
            return True
        
        LOGGER.error(f'Request URL: {url}')        
        LOGGER.error(f'Response status code: {resp.status_code}')
        return False
    
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
            self._json_payload = resp_json
            LOGGER.debug(f'External IP identified as: {ip}')
            return True
        
        self.lat = 0.0
        self.lon = 0.0
        LOGGER.error('Unable to determine ip for location identification')
        return False

    def GPS_dms_to_dd(lat_dms:Tuple[float, float, float], lat_ref: str, lon_dms: Tuple[float, float, float], lon_ref: str) -> Tuple[float, float]:
        """
        Return Lat/Lon decimal degrees (dd) from Lat/Long Degree, Minute Seconds (dms) coordinates
        Input:
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

def print_object(obj):
    for line in obj.to_string().splitlines():
        LOGGER.info(f'  {line}')
    payload = getattr(obj,'_json_payload')
    if payload is not None:
        LOGGER.info('  Payload-')
        for k, v in payload.items():
            LOGGER.info(f'    {k:15} {v}')

if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    lh.configure_logger(log_level='INFO', brightness=False)
    helper = GeoLocation()
    address = '1812 Edgewood, Berkley, Mi,'
    helper.get_location_via_address_string(address)
    LOGGER.info(f'Address: {address}')
    LOGGER.info('Returns:')
    print_object(helper)

    print('')
    helper.get_location_via_ip()
    LOGGER.info(f'Location for {helper.ip}')
    LOGGER.info('Returns:')
    print_object(helper)