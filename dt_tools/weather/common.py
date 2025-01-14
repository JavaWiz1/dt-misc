"""
Common weather constructs

"""
from dataclasses import dataclass
from enum import Enum

from loguru import logger as LOGGER


# =========================================================================================================    
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


# =========================================================================================================    
class Unknown():
    STR: str = "Unknown"
    INT: int = -1

# =========================================================================================================    
class ForecastType(Enum):
    DAY: int = 0
    NIGHT: int = 1

# =========================================================================================================    
class WeatherSymbols(Enum):
    degree = chr(176)
    N = "North"
    S = "South"
    E = "East"
    W = "West"

    def translate_compass_point(wind_dir: str) -> str:
        """
        Given the abbreviated wind direction, return full text


        Args:
            wind_dir (str): Wind direction (ie. N, S, E, W, NE, NW,...)

        Returns:
            str: Full text representation of direction (i.e. NW = North West)

        """
        resp = ''
        for char in wind_dir:
            resp += f' {WeatherSymbols[char].value}'
        return resp.lstrip()

# =========================================================================================================    
class States(Enum):
    """
    States enumeration (US and Territories)

    """
    AK = "Alaska"
    AL = "Alabama"
    AR = "Arkansas"
    AS = "American Somoa"
    AZ = "Arizonz"
    CA = "California"
    CO = "Colorado"
    CT = "Connecticut"
    DC = "District of Columbia"
    DE = "Delaware"
    FL = "Florida"
    GA = "Georgia"
    GU = "Guam"
    HI = "Hawaii"
    IA = "Idaho"
    ID = "Idaho"
    IL = "Illinois"
    IN = "Indiana"
    KS = "Kansas"
    KY = "Kentuky"
    LA = "Louisiana"
    MA = "Massachusetts"
    MD = "Maryland"
    ME = "Maine"
    MI = "Michigam"
    MN = "Minnesota"
    MO = "Missouri"
    MP = "Northern Marina Islands"
    MS = "Mississippi"
    MT = "Montana"
    NC = "North Carolina"
    ND = "North Dakota"
    NE = "Nebraska"
    NH = "New Hampshire"
    NJ = "New Jersey"
    NM = "New Mexico"
    NV = "Nevada"
    NY = "New York"
    OH = "Ohio"
    OK = "Oklahoma"
    OR = "Oregon"
    PA = "Pennsylvania"
    PR = "Puerto Rico"
    RI = "Rhode Island"
    SC = "South Carolina"
    SD = "South Dakota"
    TN = "Tenessee"
    TT = "Trust Territories"
    TX = "Texas"
    UT = "Utah"
    VA = "Virginia"
    VI = "Virgin Islands"
    VT = "Vermont"
    WA = "Washington"
    WI = "Wisconson"
    WV = "West Virgina"
    WY = "Wyoming"

    def translate_state_code(code: str) -> str:
        """
        Given the state code, return full state name

        Args:
            code (str): 2 character state code

        Returns:
            str: Full state name
        """
        try:
            state_name = States[code].value
        except Exception:
            LOGGER.debug(f'Invalid state code: {code}')
            state_name = code

        return state_name

# =========================================================================================================    
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

