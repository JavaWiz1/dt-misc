"""
General Helper Routines

- ObjectHelper
- StringHelper

ObjectHelper Examples::

    def MyClass():
        def __init__(self):
          self.var1 = 'abc'
          self.var2 = 123
        def print_something(self):
          print(f'var1: {self.var1}')
          print(f'var2: {self.var2}')
    
    m_class = MyClass()
    my_dict = ObjectHelper.to_dict(m_class)
    print(my_dict)

    output: {'var1': 'abc', 'var2': 123}           

StringHelper Examples::

    text = StringHelper.pad_r('abc', 10, pad_char='X')
    print(text) 
    outputs: 'abcXXXXXXXX'

    text = StringHelper.pad_l('abc', 10, pad_char='X')
    print(text) 
    outputs: 'XXXXXXXXabc'    

    text = StringHelper.center(' abc ', 10, pad_char='-')
    print(text)
    outputs: '-- abc ---'
"""

import json
import pathlib
from types import SimpleNamespace
from typing import Dict, List, Union

from loguru import logger as LOGGER
import requests

# =================================================================================================
class ObjectHelper:

    @classmethod
    def dict_to_obj(cls, in_dict: dict) -> Union[SimpleNamespace, Dict]:
        """
        Convert a dictionary to an object

        Args:
            in_dict (dict): Input dictionary

        Returns:
            dict or object: Object representation of dictionary, or Object if not a dictionary

        Raises:
            TypeError if in_dict is NOT a dictionary.            
        """
        obj = json.loads(json.dumps(in_dict), object_hook=lambda d: SimpleNamespace(**d))        
        return obj
    
    @classmethod
    def to_dict(cls, obj, classkey=None):
        """
        Recursively translate object into dictionary format
        
        Arguments:
            obj: object to translate

        Returns:
            A dictionary representation of the object
        """
        if isinstance(obj, dict):
            data = {}
            for (k, v) in obj.items():
                data[k] = cls.to_dict(v, classkey)
            return data
        elif hasattr(obj, "_ast"):
            return cls.to_dict(obj._ast())
        elif hasattr(obj, "__iter__") and not isinstance(obj, str):
            return [cls.to_dict(v, classkey) for v in obj]
        elif hasattr(obj, "__dict__"):
            data = dict([(key, cls.to_dict(value, classkey)) 
                for key, value in obj.__dict__.items() 
                if not callable(value) and not key.startswith('_')])
            if classkey is not None and hasattr(obj, "__class__"):
                data[classkey] = obj.__class__.__name__
            return data
        else:
            return obj

# =================================================================================================
class StringHelper:

    @staticmethod
    def pad_r(text: str, length: int, pad_char: str = ' ') -> str:
        """
        Pad input text with pad character, return left justified string of specified length.

        Example::
            ```
            text = pad_r('abc', 10, pad_char='X')
            print(text) 
            'abcXXXXXXXX'
            ```

        Arguments:
            text: Input string to pad.
            length: Length of resulting string.

        Keyword Arguments:
            pad_char: String padding character (default: {' '}).

        Raises:
            ValueError: Pad character MUST be of length 1.

        Returns:
            Left justified padded string.
        """
        if len(pad_char) > 1:
            raise ValueError('Padding character should only be 1 character in length')
        
        pad_len = length - len(text)
        if pad_len > 0:
            return f'{text}{pad_char*pad_len}'
        return text    

    @staticmethod
    def pad_l(text: str, length: int, pad_char: str = ' ') -> str:
        """
        Pad input text with pad character, return right-justified string of specified length.

            Example::
        
                text = pad_l('abc', 10, pad_char='X')
                print(text) 

                output:  
                'XXXXXXXXabc'

        Arguments:
            text: Input string to pad.
            length: Length of resulting string.

        Keyword Arguments:
            pad_char: String padding character [default: {' '}].

        Raises:
            ValueError: Pad character MUST be of length 1.

        Returns:
            Right justified padded string.
        """
        if len(pad_char) > 1:
            raise ValueError('Padding character should only be 1 character in length')
        
        pad_len = length - len(text)
        if pad_len > 0:
            return f'{pad_char*pad_len}{text}'
        return text    
    
    @staticmethod
    def center(text: str, length: int, pad_char: str = ' ') -> str:
        """
        Center text in a string of size length with padding pad.

        Args:
            text (str): text to be centered.
            length (int): length of resulting string.  If it is less
              than len(text), text will be returned.
            pad (str, optional): padding character (1). Defaults to ' '.

        Returns:
            str: text centered string
        """
        if len(pad_char) > 1:
            raise ValueError('Padding character should only be 1 character in length')
        
        new_str = text
        text_len = len(text)
        if text_len < length:
            pad_len = max(int((length - text_len) / 2) + text_len, text_len+1)
            new_str = StringHelper.pad_l(text=new_str, length=pad_len, pad_char=pad_char)
            new_str = StringHelper.pad_r(text=new_str, length=length, pad_char=pad_char)

        return new_str


class ApiTokenHelper():
    _DT_TOOLS_TOKENS_LOCATION=pathlib.Path('~').expanduser().absolute() / ".dt_tools" / "api_tokens.json"
    _API_DICT = {
        "ipinfo.io": {
            "desc": "IP Address information API",
            "module": "dt_tools.net.ip_helper",
            "token_url": "https://ipinfo.io/missingauth",
            "validate_url": "https://ipinfo.io/8.8.8.8?token={token}"
        },
        "weatherapi.com": {
            "desc": "Weather API (current, forecasts, alerts)",
            "module": "dt_tools.misc.weather",
            "token_url": "https://www.weatherapi.com/signup.aspx",
            "validate_url": "http://api.weatherapi.com/v1/ip.json?key={token}&q=auto:ip"
        },
        "geoloc": {
            "desc": "GeoLocation API (Lat, Lon, Address, ...)",
            "module": "dt_tools.misc.geoloc",
            "token_url": "https://",
            "validate_url": None
        }
    }

    
    @classmethod
    def _get_tokens_dictionary(cls) -> Dict[str, dict]:
        cls._DT_TOOLS_TOKENS_LOCATION.parent.mkdir(parents=True, exist_ok=True)
        token_dict = {}
        if cls._DT_TOOLS_TOKENS_LOCATION.exists():
            token_dict = json.loads(cls._DT_TOOLS_TOKENS_LOCATION.read_text())
        return token_dict
    
    @classmethod
    def get_api_token(cls, service: str) -> str:
        """
        Get token for API service

        Args:
            service (str): Service identifier (see get_api_services())

        Raises:
            NameError: If the service name is not valid.

        Returns:
            str: API token for target service or None if not in token cache.
        """
        if cls._API_DICT.get(service, None) == None:
            raise NameError(f'Not a valid service: {service}')
        
        t_dict = cls._get_tokens_dictionary()
        token = t_dict.get(service, None)
        return token

    @classmethod
    def save_api_token(cls, service: str, token: str) -> bool:
        saved = True
        t_dict = cls._get_tokens_dictionary()
        t_dict[service] = token
        token_str = json.dumps(t_dict)
        try:
            cls._DT_TOOLS_TOKENS_LOCATION.write_text(token_str)
        except Exception as ex:
            LOGGER.error(f'Unable to save token for {service} - {repr(ex)}')
            saved = False

        return saved
    
    @classmethod
    def get_api_services(cls) -> List[str]:
        t_dict = cls._get_tokens_dictionary()
        return list(t_dict.keys())

    @classmethod
    def get_api_service_definition(cls, api_key: str) -> Union[Dict, None]:
        return cls._API_DICT.get(api_key, None)
    
    @classmethod
    def can_validate(cls, service: str) -> bool:
        t_service:dict = cls._API_DICT.get(service, {})
        valid_service = t_service.get('validate_url', None) is not None
        if valid_service:
            LOGGER.debug(f'{service} is a valid service name')
            valid_service = cls.get_api_token(service) is not None
            if valid_service:
                LOGGER.debug(f'{service} has a token.')
            else:
                LOGGER.debug(f'{service} does NOT have a token.')
        else:
            LOGGER.debug(f'{service} is NOT a valid service name')

        return valid_service

    @classmethod
    def validate_token(cls, service: str) -> bool:
        valid_token = False
        if not cls.can_validate(service):
            LOGGER.debug(f'{service} is not valid.')
        else:
            entry = cls.get_api_service_definition(service)
            try:
                token = cls.get_api_token(service)
                url = entry['validate_url'].replace('{token}', token)
                resp = requests.get(url)
                LOGGER.debug(f'Validate: {url}  returns: {resp.status_code}')
                if resp.status_code == 200:
                    valid_token = True
            except Exception as ex:
                LOGGER.debug(f'Validate: {url}  Exception: {repr(ex)}')

        return valid_token
    
if __name__ == "__main__":
    import dt_tools.cli.demos.dt_misc_helper_demo as demo
    import dt_tools.logger.logging_helper as lh
    lh.configure_logger(log_level="INFO", brightness=False)
    
    demo()
