"""
Get sunrise and sunset for specific GPS coordinate

Example:

    sun = Sun()
    print('Sunrise: {sun.sunrise}  Sunset: {sun.sunset}')
"""
import calendar
import datetime
import math

from dateutil import tz
from loguru import logger as LOGGER
from zoneinfo import ZoneInfo

from dt_tools.misc.geoloc import GeoLocation


GEO = GeoLocation()

class SunTimeException(Exception):
    def __init__(self, message):
        super(SunTimeException, self).__init__(message)

class Sun:
    """
    Approximated calculation of sunrise and sunset datetimes. Adapted from:
    https://stackoverflow.com/questions/19615350/calculate-sunrise-and-sunset-times-for-a-given-gps-coordinate-within-postgresql
    """
    def __init__(self, lat, lon):
        """
        Sun object located at lat, lon

        Args:
            lat (_type_): latitude
            lon (_type_): longitude
        """
        self._lat = float(lat)
        self._lon = float(lon)
        LOGGER.debug(f'Sun({lat},{lon})')

    def time_now_at(self) -> datetime.datetime:
        """
        Current local time at GPS Coordinates

        Returns:
            datetime.datetime: current date time in GPS coordinate local time.
        """
        # geo = GeoLocation()
        GEO.get_location_via_lat_lon(self._lat, self._lon)
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        gps_now = utc_now.astimezone(ZoneInfo(GEO.tz_name))
        return gps_now

    def get_sunrise_time(self, date:datetime.date=None) -> datetime.datetime:
        """
        Get sunrise time at GPS coordinates in UTC format

        Args:
            date (datetime.date, optional): Target date, if none, today. Defaults to None.

        Raises:
            SunTimeException: When the sun does not rise at this location on the specified date.

        Returns:
            _type_: UTC datetime
        """
        date = datetime.date.today() if date is None else date
        sr = self._calc_sun_time(date, True)
        if sr is None:
            raise SunTimeException(f"The sun never rises on this location (on the specified date) | {date} {self._lat}/{self._lon}")
        
        return sr

    def get_local_sunrise_time(self, date:datetime.date=None, local_time_zone=tz.tzlocal()) -> datetime.datetime:
        """
        Get sunrise time in local timezone format

        Args:
            date (datetime.date, optional): Target date, if none, today. Defaults to None.

        Raises:
            SunTimeException: When the sun does not rise at this location on the specified date.

        Returns:
            _type_: datetime - Local timezone datetime
        """
        date = datetime.date.today() if date is None else date
        sr = self._calc_sun_time(date, True)
        if sr is None:
            raise SunTimeException("The sun never rises on this location (on the specified date)")
        
        return sr.astimezone(local_time_zone)

    def get_sunset_time(self, date=None) -> datetime.datetime:
        """
        Get sunset time at GPS coordinates in UTC format

        Args:
            date (datetime.date, optional): Target date, if none, today. Defaults to None.

        Raises:
            SunTimeException: When the sun does not set at this location on the specified date.

        Returns:
            _type_: UTC datetime
        """
        date = datetime.date.today() if date is None else date
        ss = self._calc_sun_time(date, False)
        if ss is None:
            raise SunTimeException(f"The sun never sets on this location (on the specified date) | {date} {self._lat}/{self._lon}")
        
        return ss

    def get_local_sunset_time(self, date=None, local_time_zone=tz.tzlocal()) -> datetime.datetime:
        """
        Get sunset time in local timezone format

        Args:
            date (datetime.date, optional): Target date, if none, today. Defaults to None.

        Raises:
            SunTimeException: When the sun does not set at this location on the specified date.

        Returns:
            _type_: datetime - Local timezone datetime
        """
        date = datetime.date.today() if date is None else date
        ss = self._calc_sun_time(date, False)
        if ss is None:
            raise SunTimeException(f"The sun never sets on this location (on the specified date) | {date} {self._lat}/{self._lon}")
        
        return ss.astimezone(local_time_zone)

    def get_gps_sunrise(self, date=None) -> datetime.datetime:
        utc_sunrise = self.get_sunrise_time(date)
        LOGGER.trace(f'UTC: {utc_sunrise}')
        GEO.get_location_via_lat_lon(self._lat, self._lon)

        gps_sunrise = utc_sunrise.astimezone(ZoneInfo(GEO.tz_name))
        LOGGER.trace(f'GPS: {gps_sunrise} {GEO.tz_name}')
        return gps_sunrise
    
    def get_gps_sunset(self, date=None) -> datetime.datetime:
        utc_sunset = self.get_sunset_time(date)
        gps_sunset = utc_sunset.astimezone(ZoneInfo(GEO.tz_name))
        return gps_sunset


    def _calc_sun_time(self, date, isRiseTime=True, zenith=90.8) -> datetime.datetime:
        """
        Calculate sunrise or sunset date.
        :param date: Reference date
        :param isRiseTime: True if you want to calculate sunrise time.
        :param zenith: Sun reference zenith
        :return: UTC sunset or sunrise datetime
        :raises: SunTimeException when there is no sunrise and sunset on given location and date
        """
        # isRiseTime == False, returns sunsetTime
        day = date.day
        month = date.month
        year = date.year

        TO_RAD = math.pi / 180.0

        # 1. first calculate the day of the year
        N1 = math.floor(275 * month / 9)
        N2 = math.floor((month + 9) / 12)
        N3 = 1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3)
        day_of_the_year = N1 - (N2 * N3) + day - 30

        # 2. convert the longitude to hour value and calculate an approximate time
        longitude_hour = self._lon / 15

        if isRiseTime:
            t = day_of_the_year + ((6 - longitude_hour) / 24)
        else:  # sunset
            t = day_of_the_year + ((18 - longitude_hour) / 24)

        # 3. calculate the Sun's mean anomaly
        mean_anomaly = (0.9856 * t) - 3.289

        # 4. calculate the Sun's true longitude
        true_longitude = mean_anomaly + \
                        (1.916 * math.sin(TO_RAD * mean_anomaly)) + \
                        (0.020 * math.sin(TO_RAD * 2 * mean_anomaly)) + 282.634
        true_longitude = self._force_range(true_longitude, 360)  # NOTE: L adjusted into the range [0,360)

        # 5a. calculate the Sun's right ascension
        right_ascension = (1 / TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD * true_longitude))
        right_ascension = self._force_range(right_ascension, 360)  # NOTE: RA adjusted into the range [0,360)

        # 5b. right ascension value needs to be in the same quadrant as L
        l_quadrant = (math.floor(true_longitude / 90)) * 90
        right_ascension_quadrant = (math.floor(right_ascension / 90)) * 90
        right_ascension += (l_quadrant - right_ascension_quadrant)

        # 5c. right ascension value needs to be converted into hours
        right_ascension = right_ascension / 15

        # 6. calculate the Sun's declination
        sinDec = 0.39782 * math.sin(TO_RAD * true_longitude)
        cosDec = math.cos(math.asin(sinDec))

        # 7a. calculate the Sun's local hour angle
        cosH = (math.cos(TO_RAD * zenith) - (sinDec * math.sin(TO_RAD * self._lat))) / (
            cosDec * math.cos(TO_RAD * self._lat)
        )
        if cosH > 1:
            return None  # The sun never rises on this location (on the specified date)
        if cosH < -1:
            return None  # The sun never sets on this location (on the specified date)

        # 7b. finish calculating H and convert into hours
        if isRiseTime:
            hours = 360 - (1 / TO_RAD) * math.acos(cosH)
        else:  # setting
            hours = (1 / TO_RAD) * math.acos(cosH)

        hours = hours / 15

        # 8. calculate local mean time of rising/setting
        mean_time = hours + right_ascension - (0.06571 * t) - 6.622

        # 9. adjust back to UTC
        utc_time = mean_time - longitude_hour
        utc_time = self._force_range(utc_time, 24)  # UTC time in decimal format (e.g. 23.23)

        # 10. Return
        hr = self._force_range(int(utc_time), 24)
        min = round((utc_time - int(utc_time)) * 60, 0)
        if min == 60:
            hr += 1
            min = 0

        # 10. check corner case https://github.com/SatAgro/suntime/issues/1
        if hr == 24:
            hr = 0
            day += 1

            if day > calendar.monthrange(year, month)[1]:
                day = 1
                month += 1

                if month > 12:
                    month = 1
                    year += 1

        return datetime.datetime(year, month, day, hr, int(min), tzinfo=tz.tzutc())

    @staticmethod
    def _force_range(v, max):
        # force v to be >= 0 and < max
        if v < 0:
            return v + max
        elif v >= max:
            return v - max

        return v


def __display_sun_data(lat, lon, show_americas: bool = False):
    datetime_format="%a %m/%d %I:%M %p"

    # geo = GeoLocation()
    GEO.get_location_via_lat_lon(lat=lat,lon=lon)
    LOGGER.debug('== geo ===============================')
    for line in GEO.to_string().splitlines():
        LOGGER.debug(f'  {line}')

    sun = Sun(lat, lon)
    
    LOGGER.warning(f'Sunrise/Sunset for {GEO.display_name}')
    utc_sunrise = sun.get_sunrise_time()
    utc_sunset  = sun.get_sunset_time()

    local_sunrise = sun.get_local_sunrise_time()
    local_sunset  = sun.get_local_sunset_time()

    gps_sunrise = sun.get_gps_sunrise()
    gps_sunset  = sun.get_gps_sunset()

    LOGGER.info(f'  current time : {datetime.datetime.strftime(sun.time_now_at(), datetime_format)}  [{GEO.tz_name}]')
    LOGGER.info(f'      latitude : {lat}  longitude: {lon} ')
    LOGGER.info('')
    LOGGER.info('Sunrise                  Sunset                   Times at location')
    LOGGER.info('------------------------ ------------------------ ------------------------------------------')
    try:
        LOGGER.info(f"{local_sunrise.strftime(datetime_format):24} {local_sunset.strftime(datetime_format):24} Local [{local_sunrise.tzname()}]")
        LOGGER.info(f"{utc_sunrise.strftime(datetime_format):24} {utc_sunset.strftime(datetime_format):24} UTC")
        LOGGER.info(f"{gps_sunrise.strftime(datetime_format):24} {gps_sunset.strftime(datetime_format):24} {GEO.display_name}")

    except SunTimeException as e:
        print("Error: {0}".format(e))

    LOGGER.info('')

if __name__ == "__main__":
    """
    https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf
    https://geocoding.geo.census.gov/geocoder/locations/address?street=4833+nahane+way&zip=32259&benchmark=Public_AR_Current&format=html

    returntype=locations|geographies
    searchtype=onlineaddress|address|coordinates
    benchmark=Public_AR_Current
    address= or street  state zip
    format=json|html

    """

    import dt_tools.logger.logging_helper as lh

    lh.configure_logger(log_level="INFO", log_format=lh.DEFAULT_DEBUG_LOGFMT, brightness=False)
    geo = GeoLocation()

    # gps = (30.069344, -81.551315)
    # LOGGER.info(f'By Lat/Lon: {gps[0]}, {gps[1]}')
    # __display_sun_data(gps[0], gps[1])
    # LOGGER.info('')

    addr = '511 East Magnolia, Bellingham, WA'
    LOGGER.info(f'By Address: {addr}')
    if GEO.get_location_via_address_string(addr):
        __display_sun_data(GEO.lat, GEO.lon)
    else:
        LOGGER.warning('Invalid address...')
    LOGGER.info('')

    addr = 'West 3rd Street, Duluth, MN'
    LOGGER.info(f'By Address: {addr}')
    if GEO.get_location_via_address_string(addr):
        __display_sun_data(GEO.lat, GEO.lon)
    else:
        LOGGER.warning('Invalid address...')
    LOGGER.info('')

    # zip=95356
    # LOGGER.info(f'By zip: {zip}')
    # if GEO.get_location_via_zip(zip, 'US'):
    #     __display_sun_data(GEO.lat, GEO.lon)
    # else:
    #     LOGGER.warning('Invalid zip...')
    # LOGGER.info('')
    
