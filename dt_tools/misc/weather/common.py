"""
Common weather constructs

"""
from dataclasses import dataclass


@dataclass
class WeatherLocation():
    """
    Weather Location class

    Used in WeatherConditions.
    """
    latitude: float = 0.0
    longitude: float = 0.0
    location_name: str = None
    location_region: str = None

    def is_initialized(self) -> bool:
        """
        Is this weather location initialized.

        Returns:
            bool: True if lat/lon has been populated else False
        """
        return False if (self.latitude == 0.0 and self.longitude == 0.0) else True

