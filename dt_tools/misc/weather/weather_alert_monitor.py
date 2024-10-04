import textwrap
from typing import Dict, List

from loguru import logger as LOGGER

import utils.cfg as cfg
from utils.weather.current import Conditions
from utils.weather.forecast import LocationAlerts
from utils.misc.sound import ACCENT


class AlertEntry():
    def __init__(self, id: str, new_alert: bool):
        self.id: str = id
        self.new_alert: bool = new_alert
        
class WeatherAlertMonitor():
    def __init__(self ):
        self._weather_locations: List[LocationAlerts] = None
        self._active_alert_dict: Dict[AlertEntry] = None
        self._local_weather: Conditions = None
        self._speak_accent: ACCENT = ACCENT.UnitedStates

    @property
    def accent(self) -> ACCENT:
        return self._speak_accent
    
    @accent.setter
    def accent(self, id: str):
        try:
            speak_accent = ACCENT[id]
        except Exception:
            LOGGER.warning(f'WeatherAlertsMonitor() invalid accent id [{id}], defaulting to US.')
            speak_accent = ACCENT.UnitedStates

        LOGGER.warning(f'WeatherAlertMonitor() setting accent to: {speak_accent}')
        self._speak_accent = speak_accent
    
    @property
    def local(self) -> Conditions:
        if self._local_weather is None:
            self._local_weather = Conditions(cfg.loc_lat, cfg.loc_lon)

        return self._local_weather
    
    @property
    def location_count(self):
        return 0 if self._weather_locations is None else len(self._weather_locations)

    @property
    def locations(self) -> List[LocationAlerts]:
        return self._weather_locations
        
    @property
    def alert_count(self):
        return len(self._active_alert_dict.keys())
    
    @property
    def new_alert_count(self):
        cnt = 0
        alert: AlertEntry
        for alert in self._active_alert_dict.values():
            if alert.new_alert:
                cnt += 1
        return cnt

    def load_local(self):
        self.local.refresh_if_stale()

    def add_alert_location(self, lat: float, lon: float, friendly_name: str = ''):
        if self._weather_locations is None:
            self._weather_locations = []
        self._weather_locations.append(LocationAlerts(lat, lon, friendly_name))

    def check_for_new_alerts(self, mark_as_seen: bool = False) -> bool:
        new_alerts = False
        if self._active_alert_dict is None or self._potential_updates():
            LOGGER.debug('potential updates..')
            new_alerts = self._load_new_alerts(mark_as_seen)

        return new_alerts
    
    def alerts_summary(self) -> List[Dict]:
        alert_list = []
        loc: LocationAlerts
        for loc in self._weather_locations:
            for i in range(0, loc.alert_count):
                alert_list.append({'id': loc.alert_id(i), "location": loc.city_state, "headline": loc.headline(i) })
        return alert_list
    
    def vocalize_alerts(self, only_new: bool = False) -> bool:
        if self._active_alert_dict is None:
            self.check_for_new_alerts()

        entry: AlertEntry
        alert_cnt = 1
        for loc in self.locations:
            for i in range(0, loc.alert_count):
                alert_id = loc.alert_id(i)
                entry = self._active_alert_dict[alert_id]
                if not only_new or (only_new and entry.new_alert):
                    loc.accent = self.accent
                    self.display_alert(alert_cnt, loc, i, detail=True)
                    loc.speak_alert(i)
                    alert_cnt += 1
                    if entry.new_alert:
                        entry.new_alert = False
                        self._active_alert_dict[alert_id] = entry
        if alert_cnt - 1 > 0:
            LOGGER.success('Speak weather alerts complete.')    
        return True
    
    def vocalize_alert(self, alert_id: str) -> bool:
        pass
    
    def display_alert(self, alert_cnt: int, loc: LocationAlerts, alert_id: str, detail: bool = False):
        alert_idx = loc.get_alert_idx(alert_id)
        LOGGER.info(f'{"-"*25} {"-"*70}')
        LOGGER.info(f'[{alert_cnt:2}] {loc.city_state:20} {loc.headline(alert_idx)}')
        buffer = loc.description(alert_idx).splitlines()
        for buff_line in buffer:
            lines = textwrap.wrap(buff_line, width=101, initial_indent=' '*26, subsequent_indent=' '*26)
            for line in lines:
                LOGGER.info(line)

    def _potential_updates(self) -> bool:
        potential_update_identified = False
        for loc in self._weather_locations:
            if loc.refresh_if_needed():
                potential_update_identified = True
        return potential_update_identified

    def _load_new_alerts(self, mark_as_seen: bool = False) -> bool:
        if self._active_alert_dict is None:
            self._active_alert_dict = {}

        new_alert_dict = {}
        at_least_one_new_alert = False
        for loc in self._weather_locations:
            for i in range(0, loc.alert_count):
                new_alert_id = loc.alert_id(i)
                if new_alert_id in self._active_alert_dict.keys():
                    # If already in dict, only count as new if it's not been updated
                    entry: AlertEntry = self._active_alert_dict[new_alert_id]
                    new_alert = entry.new_alert
                else:
                    # Not it dict, this is new
                    new_alert = not mark_as_seen

                if new_alert:
                    # LOGGER.warning('new alert')
                    at_least_one_new_alert = True
                # LOGGER.warning(f'{new_alert_id} | {new_alert}')    
                new_alert_dict[new_alert_id] = AlertEntry(new_alert_id, new_alert)
                    
        self._active_alert_dict = new_alert_dict
        return at_least_one_new_alert
            
