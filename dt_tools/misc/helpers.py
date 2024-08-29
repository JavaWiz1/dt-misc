from types import SimpleNamespace
import json

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
# =================================================================================================
class _DictObj:
    def __init__(self, in_dict:dict):
        assert isinstance(in_dict, dict)
        for key, val in in_dict.items():
            print(f'key: {key}, val: {val}, val_type: {type(val)}')
            if isinstance(val, (list, tuple)):
               setattr(self, key, [_DictObj(x) if isinstance(x, dict) else x for x in val])
            else:
               setattr(self, key, _DictObj(val) if isinstance(val, dict) else val)

    def get(self, field: str):
        val = getattr(self, field, None)
        if isinstance(val, _DictObj):
            return str(val)
        else:
            return val
        
def _DictObj2(d):
     
    # checking whether object d is a
    # instance of class list
    if isinstance(d, list):
           d = [_DictObj2(x) for x in d] 
 
    # if d is not a instance of dict then
    # directly object is returned
    if not isinstance(d, dict):
           return d
  
    # declaring a class
    class C:
        pass
  
    # constructor of the class passed to obj
    obj = C()
  
    for k in d:
        obj.__dict__[k] = _DictObj2(d[k])
  
    return obj

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
        # return _DictObj(in_dict)
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
    
class MyClass():
    def __init__(self):
        self.var1 = 'abc'
        self.var2 = 123

    def print_something(self):
        print(f'var1: {self.var1}')
        print(f'var2: {self.var2}')


if __name__ == "__main__":
    # m_class = MyClass()
    # my_dict = ObjectHelper.to_dict(m_class)
    # print(f'my_dict is: {my_dict}')
    test_dict: dict = {"field1": "valueField1", "field2": {"subfield2a": "valueSubField2a", "subfield2b": "valueSubField2b"}, "field3": "valueField3"}
    my_obj = ObjectHelper.dict_to_obj(test_dict)
    print(f'my_obj: {my_obj}')
    print(f'my_obj.field1: {my_obj.field1}')
    print(f'my_obj.field2: {my_obj.field2}')
    print(f'my_obj.field3: {my_obj.field3}')
    print(f'my_obj.field2.subfield2a: {my_obj.field2.subfield2a}')

    # print(StringHelper.pad_l(' pad_l', 20, '-'))
    # print(StringHelper.pad_r('pad_r ', 20, '-'))
    # print(StringHelper.center(' abc ', 10, '-'))
    # for length in range(20, len(' center ')-1, -2):
    #     print(StringHelper.center(' center ', length, '-'))
    
