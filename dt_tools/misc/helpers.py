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

from types import SimpleNamespace
import json
# =================================================================================================
class ObjectHelper:

    @classmethod
    def dict_to_obj(cls, in_dict: dict):
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
    
if __name__ == "__main__":
    import dt_tools.logger.logging_helper as lh
    from dt_tools.cli.dt_misc_helper_demo import demo

    lh.configure_logger(log_level="INFO", brightness=False)
    demo()
