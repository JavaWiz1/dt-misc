"""
General Helper Routines

- ObjectHelper
- StringHelper

"""
# =================================================================================================
class ObjectHelper:
    @classmethod
    def to_dict(cls, obj, classkey=None):
        """Recursively translate object into dictionary format"""
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
    @classmethod
    def pad_r(cls, text: str, length: int, pad_char: str = ' ') -> str:
        """
        Pad input text with pad character, return left justified string of specified length.

        Example::
        
            text = pad_r('abc', 10, pad_char='X')
            print(text) 
            'abcXXXXXXXX'

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

    @classmethod
    def pad_l(cls, text: str, length: int, pad_char: str = ' ') -> str:
        """
        Pad input text with pad character, return right-justified string of specified length.

            Example::
        
                text = pad_l('abc', 10, pad_char='X')
                print(text) 
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
    
    @classmethod
    def center(cls, text: str, length: int, pad: str = ' ') -> str:
        pass