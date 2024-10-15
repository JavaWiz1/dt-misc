"""
This module demonstrates the Geolocation module functionality.


"""

from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.os.os_helper import OSHelper
from dt_tools.misc.census_geoloc import Census_GeoLocation as CensusGeoLocation
from dt_tools.misc.census_geoloc import GeoLocationAddress
from dt_tools.misc.geoloc import GeoLocation


def _print_object(obj):
    for line in obj.to_string().splitlines():
        LOGGER.info(f'  {line}')
    payload = getattr(obj,'_json_payload')
    if payload is not None:
        LOGGER.info('  Payload-')
        for k, v in payload.items():
            LOGGER.info(f'    {k:15} {v}')

def _demo_census_geoloc():
    LOGGER.info('')
    LOGGER.info('Census Geolocation.')
    LOGGER.info('  Must supply street, city, state OR street, zip code')
    LOGGER.info('')

    geo = CensusGeoLocation()
    street = '87 Rockefeller Center'
    city = 'New York'
    state = 'NY'
    zip = None
    locations = geo.lookup_address('87 Rockefeller Center', 'New York', 'NY')
    loc: GeoLocationAddress = None
    LOGGER.info(f'Lookup  - street: {street}  city: {city}  state: {state}  zip: {zip}')
    for loc in locations:
        # LOGGER.success(f'Returns - lat: {loc.latitude:.4f}  lon: {loc.longitude:.4f}  address: {loc.address}')
        _print_object(loc)
    LOGGER.info('')

def _demo_geoloc():
    LOGGER.info('')
    LOGGER.warning('Geolocation (geocode.maps.co)')
    LOGGER.info('')

    geo = GeoLocation()
    LOGGER.warning('Retrieve via address string')
    address = 'Metlife Stadium, NJ'
    geo.get_location_via_address_string(address)
    LOGGER.info(f'  {address}')
    LOGGER.info('Returns -')
    _print_object(geo)
    LOGGER.info('')

    LOGGER.warning('Retrieve via address')
    address = '511 East Magnolia, Bellingham, WA 98225'
    geo.get_location_via_address(city='Bellingham', state='WA', house='511', street='East Magnolia', zip=98225)
    LOGGER.info("  city='Bellingham', state='WA', house='511', street='East Magnolia', zip=98225")
    LOGGER.info('Returns -')
    _print_object(geo)
    LOGGER.info('')

    LOGGER.warning('Retrieve via latitude/longitude')
    lat = geo.lat
    lon = geo.lon
    geo.get_location_via_lat_lon(lat, lon)
    LOGGER.info(f'  lat: {lat}  lon: {lon}')
    LOGGER.info('Returns -')
    _print_object(geo)
    LOGGER.info('')

    LOGGER.warning('Retrieve via IP')
    geo.get_location_via_ip()
    LOGGER.info(f'  IP resolved as {geo.ip}')
    LOGGER.info('Returns -')
    # for line in geo.to_string().splitlines():
    #     LOGGER.info(f'  {line}')
    _print_object(geo)
    LOGGER.info('')

def demo():
    OSHelper.enable_ctrl_c_handler()
    LOGGER.info('-'*80)
    LOGGER.info('dt_misc_geoloc demo')
    LOGGER.info('-'*80)

    _demo_census_geoloc()
    _demo_geoloc()

    LOGGER.info('')
    LOGGER.info('Demo complete.')

if __name__ == "__main__":
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, log_level='INFO', brightness=False)
    demo()
