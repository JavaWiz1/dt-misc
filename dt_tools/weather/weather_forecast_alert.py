"""
weather_forecast_alert.py

Module which leverages The National Weather Service (NWS) API (api.weather.gov) to retrieve weather forecasts and alerts based on GeoLocation (latitude, longitude).

This is a free API provided by the US government

NOTE:

    - Endpoint only support US locations (including )

"""
import json
import textwrap
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Union

import requests
from loguru import logger as LOGGER

from dt_tools.misc.weather.common import ForecastType, States, Unknown, WeatherLocation
from dt_tools.console.console_helper import ConsoleHelper as ch
from dt_tools.console.console_helper import ColorFG

URL_BASE_TEMPLATE="https://api.weather.gov/points/{latitude},{longitude}"
URL_ALERT_TEMPLATE="https://api.weather.gov/alerts/active?point={latitude},{longitude}"


# =========================================================================================================    
@dataclass
class ForecastDay():

    def __init__(self, lat:float, lon:float, city:str, state: str, payload: dict):
        self.location = WeatherLocation(latitude=lat, longitude=lon)
        self.city = city
        self.state = state
        self.payload: dict = payload

    def to_string(self) -> str:
        text = f'{self.name}\n'
        text += f'  Location       : {self.city} {self.state} [{self.lat_lon}]\n'
        text += f'  Timeframe      : {self.timeframe}\n'
        text += f'  Temperature    : {self.temperature} {self.temperature_unit} {self.temperature_trend}\n'
        text += f'  Prob of Percip : {self.percipitation_pct} pct\n'
        text += f'  Wind Speed     : {self.wind_speed} {self.wind_direction}\n'
        text += f'  Icon           : {self.icon}\n'
        lines = textwrap.wrap(self.short_forecast, width=90, 
                              initial_indent='  Short Desc     : ',
                              subsequent_indent=' '*19)
        text += '\n'.join(lines) + '\n'
        # text += f'  Short Desc     : {self.short_forecast}\n'
        lines = textwrap.wrap(self.detailed_forecast, width=90, 
                              initial_indent='  Detailed Desc  : ',
                              subsequent_indent=' '*19)
        text += '\n'.join(lines) + '\n'
        # text += f'  Detailed Desc  : {self.detailed_forecast}\n'
        return text
    
    @property
    def state_full(self) -> str:
        return States.translate_state_code(self.state)
    
    @property
    def _valid_forecast_day(self) -> bool:
        if len(self.payload.keys()) > 0:
            return True
        return False
    
    @property
    def name(self) -> str:
        return self.payload.get('name', Unknown.STR)
    
    @ property
    def lat_lon(self) -> str:
        return f'{self.location.latitude}/{self.location.longitude}'
    
    @property
    def timeframe(self) -> str:
        if self._valid_forecast_day:
            tm_start = datetime.fromisoformat(self.payload.get('startTime'))
            tm_end   = datetime.fromisoformat(self.payload.get('endTime'))
            t_start = datetime.strftime(tm_start, "%a %I:%M %p")
            t_end   = datetime.strftime(tm_end, "%a %I:%M %p")
            return f'{t_start} thru {t_end}'
        return Unknown.STR
    
    @property
    def temperature(self) -> int:
        return self.payload.get('temperature', Unknown.INT)     
    @property
    def temperature_unit(self) -> str:
        return self.payload.get('temperatureUnit', Unknown.STR)
    @property
    def temperature_trend(self) -> str:
        return self.payload.get('temperatureTrend', Unknown.STR)
    @property
    def percipitation_pct(self) -> int:
        return self.payload.get('probabilityOfPrecipitation', {'value': Unknown.INT}).get('value', Unknown.INT)
    @property
    def wind_speed(self) -> str:
        return self.payload.get('windSpeed', Unknown.STR)
    @property
    def wind_direction(self) -> str:
        return self.payload.get('windDirection', Unknown.STR)
    @property
    def icon(self) -> str:
        return self.payload.get('icon', Unknown.STR)
    @property
    def short_forecast(self) -> str:
        return self.payload.get('shortForecast', Unknown.STR)
    @property
    def detailed_forecast(self) -> str:
        return self.payload.get('detailedForecast', Unknown.STR)
    


# =========================================================================================================    
class AbstractEndpoint(ABC):
    def __init__(self, lat: float, lon: float, friendly_name: str = ''):
        self.location = WeatherLocation(latitude=lat, longitude=lon)
        self._friendly_name: str = friendly_name
        self._city: str = None
        self._state: str = None
        self._json_error: dict = {}

        self._last_update: datetime = None
        self._valid_payload: bool = False
        
    @property
    def latitude(self) -> float:
        return float(self.location.latitude)
    
    @property
    def longitude(self) -> float:
        return float(self.location.longitude)
    
    @property
    def name(self):
        '''Friendly name (if exists) or location'''
        if self._friendly_name == '':
            return self.location
        return self._friendly_name
    
    @property
    def city(self) -> str:
        return self._city
    
    @property
    def state(self) -> str:
        # if self._state is None:
        return self._state
        
    @property
    def state_full(self) -> str:
        return self._translate_state(self._state)
    
    @property
    def city_state(self):
        if self._city is None and self._state is None:
            return None
        return f'{self._city},{self._state}'
    
    def _translate_state(self, state: str) -> str:
        return States.translate_state_code(state)
    
    def refresh_if_needed(self, force: bool = False) -> bool:
        '''Return true if refresh needed and successful else false'''
        if self._last_update is None or (datetime.now() - self._last_update).total_seconds() > 600.0:
            self._valid_payload = self._refresh()
            if self._valid_payload:
                self._last_update = datetime.now()
            return self._valid_payload
        return False
    
    @classmethod
    def _refresh(self) -> bool:
        LOGGER.error('Must implement _refresh() function in concrete class.')
        raise NotImplementedError('_refresh()')

    def _call_endpoint(self, URL: str) -> Tuple[int, dict]:
        LOGGER.debug(f'Calling: {URL}')
        resp = requests.get(URL)
        LOGGER.debug(f'  returns: {resp.status_code}')
        if resp.status_code != 200:
            self._json_error = resp.json()

        return resp.status_code, resp.json()
    

# =========================================================================================================    
class Forecast(AbstractEndpoint):
    """
    Class to interface for weather Forecast

    Populate ForecastDay class by calling one of: 
    - forecast_for_future_day()
    - forecast_for_today()
    - forecast_for_tomorrow()
    
    Example:

        weather_forecast = Forcast(30.0694,-81.5515) # Fruit Cove, Florida
        today: ForecastDay = weather_forecast.forecast_for_today(ForecastType.DAY)
        print(today.short_forecast)

    """
    def __init__(self, lat: float, lon: float, friendly_name: str = '', base_only: bool = False):
        super().__init__(lat, lon, friendly_name)
        self._url = URL_BASE_TEMPLATE.replace('{latitude}', str(lat)).replace('{longitude}', str(lon))

        self._json_base: dict = {}
        self._json_daily_forecast:   dict = {}
        self._json_hourly_forecast: dict = {}
        if self._refresh(base_only):
            self._valid_payload = True
            self._last_update = datetime.now()

            
    def _refresh(self, base_only: bool = False) -> bool:
        self._json_error = {}
        rc, payload =  self._call_endpoint(self._url)
        if rc == 200:
            self._json_base = payload
            self._json_daily_forecast = {}
            self._json_hourly_forecast = {}
            if self._city is None:
                self._city = self._json_base['properties']['relativeLocation']['properties']['city']
                self._state = self._json_base['properties']['relativeLocation']['properties']['state']
            if not base_only:
                forecast_url = payload['properties']['forecast']
                hourly_forecast_url = payload['properties']['forecastHourly']
                rc, payload = self._call_endpoint(forecast_url)
                if rc == 200:
                    self._json_daily_forecast = payload
                    rc, payload = self._call_endpoint(hourly_forecast_url)
                    if rc == 200:
                        self._json_hourly_forecast = payload

        return (rc == 200)
    
    def forecast_for_future_day(self, days_in_future: int, time_of_day: ForecastType = ForecastType.DAY) -> Union[ForecastDay, None]:
        """
        Get weather forecast for a future day/night

        Args:
            days_in_future (int): Number of days in future (0=Today)
            time_of_day (ForecastType, optional): Forecast.DAY or Forecast.NIGHT. Defaults to ForecastType.DAY.

        Returns:
            Union[ForecastDay, None]: Forecast for target day if found, else None
        """
        # NOTE: May be bug here if current time of day has passed day/night boundary
        #       Possible that entry 0 is night (not day)
        if self._valid_payload:
            idx = (days_in_future * 2) + time_of_day.value
            payload = self._json_daily_forecast['properties']['periods'][idx]
            return ForecastDay(self.latitude, self.longitude, self.city, self.state, payload)
        LOGGER.warning(f'ForecastFutureDay({days_in_future}, {time_of_day.name}) - Invalid payload!')
        return None
    
    def forecast_for_today(self, time_of_day: ForecastType = ForecastType.DAY) -> ForecastDay:
        """
        Get weather forecast for today (or tonight)

        Args:
            time_of_day (ForecastType, optional): Forecast.DAY or Forecast.NIGHT. Defaults to ForecastType.DAY.

        Returns:
            Union[ForecastDay, None]: Forecast for today/night if found, else None
        """
        return self.forecast_for_future_day(0, time_of_day)
    
    def forecast_for_tomorrow(self, time_of_day: ForecastType = ForecastType.DAY) -> ForecastDay:
        """
        Get weather forecast for tomorrow

        Args:
            time_of_day (ForecastType, optional): Forecast.DAY or Forecast.NIGHT. Defaults to ForecastType.DAY.

        Returns:
            Union[ForecastDay, None]: Forecast for tomorrow (day or night) if found, else None
        """
        return self.forecast_for_future_day(1, time_of_day)


# =========================================================================================================    
class LocationAlerts(AbstractEndpoint):
    def __init__(self, lat: float, lon: float, friendly_name: str = '', weather: Forecast = None):
        super().__init__(lat, lon, friendly_name)

        self.loc_id = f'{lat}|{lon}'
        self._weather: Forecast = weather if weather is not None else Forecast(lat, lon, base_only=True)
        self._url = URL_ALERT_TEMPLATE.replace('{latitude}', str(lat)).replace('{longitude}', str(lon))
        self._json_alert = {}
        self.refresh_if_needed(force=True)
        self._city = self._weather.city
        self._state = self._weather.state

        # self._speak_accent: ACCENT = ACCENT.UnitedStates

    def _refresh(self) -> bool:
        self._json_error = {}
        rc, payload =  self._call_endpoint(self._url)
        if rc == 200:
            self._json_alert = payload
    
        return (rc == 200)
    
    @property
    def alert_count(self) -> int:
        return len(self._json_alert.get('features',''))
    
    def alert_id(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'id')
    def effective(self, alert_num: int) -> datetime:
        return self._get_property(alert_num, 'effective')
    def expires(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'expires')
    def status(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'status')
    def message_type(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'messageType')
    def serverity(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'severity')
    def certainty(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'certainty')
    def urgency(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'urgency')
    def event(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'event')
    def headline(self, alert_num: int) -> str:
        token = self._get_property(alert_num, 'headline').split(' by ') 
        return token[0]
    def description(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'description')
    def instruction(self, alert_num: int) -> str:
        return self._get_property(alert_num, 'instruction')

    def get_alert_idx(self, id: str) -> int:
        idx = -1
        for cnt in range(0, len(self._json_alert['features'])):
            if id == self.alert_id(cnt):
                idx = cnt
                break
    
        return idx
    
    def to_string(self) -> str:
        output = 'ALERTS-\n'
        location = f'{self.city} {self.state} [{self.location.latitude}/{self.location.longitude}]'
        location = ch.cwrap(location, fg=ColorFG.GREEN2)
        output += f'num_alerts  : {self.alert_count}\n'
        # output += f'location    : {self.city} {self.state} [{self.location.latitude}/{self.location.longitude}]\n'
        output += f'location    : {location}\n'
        cnt = 0
        for cnt in range(0, self.alert_count):
            output += f'[{cnt+1}] Alert {self.alert_id(cnt)}\n'
            # output += f'    refid       : {self.reference_id(cnt)}\n'
            output += f'    effective   : {self.effective(cnt)} - {self._convert_date(self.effective(cnt), True)}\n'
            output += f'    expires     : {self.expires(cnt)} - {self._convert_date(self.expires(cnt))}\n'
            output += f'    type        : {self.message_type(cnt)}\n'
            output += f'    severity    : {self.serverity(cnt)}\n'
            output += f'    certainty   : {self.certainty(cnt)}\n'
            output += f'    urgency     : {self.urgency(cnt)}\n'
            output += f'    event       : {self.event(cnt)}\n'
            output += f'    headline    : {self.headline(cnt)}\n'
            if len(self.description(cnt)) < 80:
                output += f'    description : {self.description(cnt)}\n'
            else:
                output +=  '    description :\n'
                lines = textwrap.wrap(self.description(cnt), width=120, 
                                    initial_indent='       ',
                                    subsequent_indent=' '*7)
                output += '\n'.join(lines) + '\n'
            if len(self.instruction(cnt)) < 80:
                output += f'    instruction : {self.instruction(cnt)}\n'
            else:
                output +=  '    instruction :\n'
                lines = textwrap.wrap(self.instruction(cnt), width=120, 
                                    initial_indent='       ',
                                    subsequent_indent=' '*7)
                output += '\n'.join(lines) + '\n'

            output += '\n'
        return output
        
    def _convert_date(self, str_iso_date: str, inc_month: bool = False) -> str:
        token = str_iso_date
        if token is not None and token != Unknown.STR:
            date_val = datetime.fromisoformat(token) 
            date_fmt = "%B %d at %I:%M%p" if inc_month else "%I:%M%p"
            ret_date = date_val.strftime(date_fmt)
        return ret_date

    def _get_property(self, alert_num: int, key: str) -> str:
        val = Unknown.STR
        if alert_num < self.alert_count:
            props: dict = self._json_alert['features'][alert_num]['properties']
            val = props.get(key, Unknown.STR)
            if val is None:
                val = Unknown.STR
        return val
    


def main():
    lat, lon = (30.0694,-81.5515)       # Cimarrone
    # lat, lon = (40.6561391,-74.0035868)   # Brooklyn
    # lat, lon = (45.5537619,-122.7071236)  # Portland 
    weather_forecast = Forecast(lat, lon)
    # print(json.dumps(weather._json_base, indent=2))
    LOGGER.warning(f'Forecast for: {weather_forecast.city_state}')    
    today: ForecastDay = weather_forecast.forecast_for_today(ForecastType.DAY)
    if today is not None:
        LOGGER.debug(f'\n{today.to_string()}')
        LOGGER.success('today short forecast:')
        LOGGER.info(f'  {today.short_forecast}')
        LOGGER.success('today long forecast:')
        LOGGER.info(f'  {today.detailed_forecast}')
        LOGGER.info('')
    tonight: ForecastDay = weather_forecast.forecast_for_today(ForecastType.NIGHT)
    if tonight is not None:
        LOGGER.debug(f'\n{json.dumps(weather_forecast._json_base)}')
        LOGGER.success('tonight short forecast:')
        LOGGER.info(f'  {tonight.short_forecast}')
        LOGGER.success('tonight long forecast:')
        LOGGER.info(f'  {tonight.detailed_forecast}')
        LOGGER.info('')

    alert = LocationAlerts(lat, lon)
    LOGGER.info(f'\n{alert.to_string()}')
    for i in range(0, alert.alert_count):
        LOGGER.info(alert.headline(i))
        LOGGER.info(f'  {alert.description(i)}')
        LOGGER.info(f'  {alert.instruction(i)}')

if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    lh.configure_logger(log_level="INFO", log_format=lh.DEFAULT_DEBUG_LOGFMT, brightness=False)
    main()
