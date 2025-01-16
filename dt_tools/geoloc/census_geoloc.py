"""
Retrieve United States GPS Location data based on address.

Leverages census data API from https://geocoding.geo.census.gov/geocoder/

"""
from dataclasses import dataclass
from typing import List

import requests
from loguru import logger as LOGGER
import dt_tools.logger.logging_helper as lh

class GeoLocationException(Exception):
    def __init__(self, message):
        super(GeoLocationException, self).__init__(message)

@dataclass
class GeoLocationAddress():
    address: str
    latitude: float
    longitude: float
    _json_payload: dict

    def to_string(self) -> str:
        output = ''
        for attr in dir(self):
            value = getattr(self, attr)
            if value is not None and not callable(value) and not attr.startswith('_'):
                output += f'{attr:15} : {getattr(self, attr)}\n'
        
        return output

class Census_GeoLocation():
    """
    GeoLocation helper class to help identify lat, long for addresses
    uses geocoding.geo.census.gov restAPI
    """
    
    _TARGET_URL="https://geocoding.geo.census.gov/geocoder/locations/address?street={street}&city={city}{parms}&benchmark=Public_AR_Current&format=json"
    
    def __init__(self):
        pass

    @classmethod
    def _get_url(cls, street, city, state, zipcode) -> str:
        url = cls._TARGET_URL.replace("{street}", street)
        parms = ''
        if city is not None:
            parms += f'&city={city}&state={state}'
        if zipcode is not None:
            parms += f'&zip={zipcode}'
        url = url.replace("{parms}", parms)
        LOGGER.debug(f'URL: {url}')
        return url

    # {"result": {
    #     "input": {
    #         "address": {"address": "4600 Silver Hill Rd, Washington, DC 20233"},
    #         "benchmark": {
    #             "isDefault": true,
    #             "benchmarkDescription": "Public Address Ranges - Current Benchmark",
    #             "id": "4",
    #             "benchmarkName": "Public_AR_Current"
    #         }
    #     },
    #     "addressMatches": [{
    #         "tigerLine": {
    #             "side": "L", "tigerLineId": "76355984"
    #         },
    #         "coordinates": {
    #             "x": -76.92748724230096, "y": 38.84601622386617
    #         },
    #         "addressComponents": {
    #             "zip": "20233",
    #             "streetName": "SILVER HILL",
    #             "preType": "",
    #             "city": "WASHINGTON",
    #             "preDirection": "",
    #             "suffixDirection": "",
    #             "fromAddress": "4600",
    #             "state": "DC",
    #             "suffixType": "RD",
    #             "toAddress": "4700",
    #             "suffixQualifier": "",
    #             "preQualifier": ""
    #         },
    #         "matchedAddress": "4600 SILVER HILL RD, WASHINGTON, DC, 20233"
    #     }]
    # }}

    @classmethod
    def lookup_address(cls, street:str, city:str = None, state:str = None, zipcd:str = None) -> List[GeoLocationAddress]:
        valid_parameters = True if street is not None and (zipcd is not None or (city is not None and state is not None)) else False
        if not valid_parameters:
            raise ValueError('Must supply street and zip or street, city and state')
        url = cls._get_url(street, city, state, zipcd)
        resp = requests.get(url)
        if resp.status_code != 200:
            msg = f"url: {url}\nInvalid Geolocation response code: {resp.status_code}"
            LOGGER.error(msg)
            raise GeoLocationException(msg)

        LOGGER.debug("Result:\n{}\n".format(resp.json()))
        location_list = []
        addr_matches = resp.json()['result']['addressMatches']
        for fnd_address in addr_matches:
            addr = fnd_address['matchedAddress']
            latitude = float(fnd_address['coordinates']['y'])
            longitude = float(fnd_address['coordinates']['x'])
            location = GeoLocationAddress(address=addr, latitude=latitude, longitude=longitude, _json_payload=fnd_address)
            location_list.append(location)

        LOGGER.debug(f'{len(location_list)} addresses identified.')
        return location_list

if __name__ == "__main__":
    lh.configure_logger(log_level="INFO")
    geo = Census_GeoLocation()
    address = input("Street Address: ")
    while len(address) > 0:
        city = input("City   : ")
        state = input("State  : ")
        zipcd = input("Zip    : ")
        locations = geo.lookup_address(address, city, state, zipcd)
        for loc in locations:
            LOGGER.info(f'{loc.latitude:.4f}/{loc.longitude:.4f} - {loc.address}')
        address = input("Street Address (blank to quit): ")