"""
This module will execute the dt_misc helper demo.

Features ObjectHelper and StringHelper classes.

"""
from loguru import logger as LOGGER

import dt_tools.logger.logging_helper as lh
from dt_tools.misc.helpers import ObjectHelper, StringHelper

class _Stats():
    def __init__(self, age: int, height: str, weight:int):
        self.age = age
        self.height = height
        self.weight = weight

class _Person():
    def __init__(self, name: str, statistics: _Stats, occupation: str):
        self.name: str = name
        self.stats: _Stats = statistics
        self.occupation: str = occupation

_person_dict = {
    'name': "Alberto", "stats": {"age": 45, "height": "6'1\"", "weight": 175}, "occupation": "engineer"
    }

def demo():
    LOGGER.info('')
    LOGGER.info('-'*40)
    LOGGER.info('dt_misc_helper_demo')
    LOGGER.info('-'*40)
    LOGGER.info('')

    LOGGER.info("Object to Dictionary demo")
    LOGGER.info("-------------------------")
    LOGGER.info("class Stats():")
    LOGGER.info('    def __init__(self, age:int, height:str, weight: int):')
    LOGGER.info("        self.age = age")
    LOGGER.info("        self.height = height")
    LOGGER.info("        self.weight = weight")
    LOGGER.info("")
    LOGGER.info("class Person():")
    LOGGER.info("    def __init__(self, name: str, statistics: Stats, occupation: str):")
    LOGGER.info("        self.name = name")
    LOGGER.info("        self.stats = statistics")
    LOGGER.info("        self.occupation = occupation")
    LOGGER.info("")
    LOGGER.info("stat = Stats(20, '5\'7\"', 150)")
    LOGGER.info("person = Person('Joe', stat, 'Carpenter')")
    LOGGER.info("")
    LOGGER.warning("print(ObjectHelper.to_dict(person))")
    LOGGER.info("")
    LOGGER.info("Returns:")
    stat = _Stats(20, '5\'7"', 150)
    person = _Person('Joe', stat, 'Carpenter')
    LOGGER.success(f'  {ObjectHelper.to_dict(person)}')
    LOGGER.info("")
    input('Press Enter to continue')

    LOGGER.info("")
    LOGGER.info("Dictionary to Object demo")
    LOGGER.info('-------------------------')
    LOGGER.info("person_dict = {")
    LOGGER.info('  {"name": "Alberto", "stats": {"age": 45, "height": "6\'1\"", "weight": 175}, "occupation": "engineer"}')
    LOGGER.info("")
    LOGGER.info("person = (ObjectHelper.dict_to_obj(person_dict)")
    LOGGER.info("")
    LOGGER.warning("print(f'Person object: {person}')")
    LOGGER.warning("print(f'Name: {person.name}')")
    LOGGER.warning("print(f'Age : {person.stats.age}')")
    LOGGER.info("")
    LOGGER.info("Returns:")
    person = ObjectHelper.dict_to_obj(_person_dict)
    LOGGER.success(f"  Person object: {person}")
    LOGGER.success(f'  Name: {person.name}')
    LOGGER.success(f'  Age : {person.stats.age}')
    LOGGER.info("")
    input('Press Enter to continue')
    LOGGER.info("")
    LOGGER.info("String Helper demos")
    LOGGER.info("-------------------")
    LOGGER.info("")
    LOGGER.info("print(StringHelper.pad_l(text=' Pad Left', length=20, pad_char='*'))")
    LOGGER.success(StringHelper.pad_l(text=' Pad Left', length=20, pad_char='*'))

    LOGGER.info("print(StringHelper.pad_r(text='Pad Right ', length=20, pad_char='*'))")
    LOGGER.success(StringHelper.pad_r(text='Pad Right ', length=20, pad_char='*'))

    LOGGER.info("print(StringHelper.center(text=' center ', length=20, pad_char='*'))")
    LOGGER.success(StringHelper.center(text=' center ', length=20, pad_char='*'))

    LOGGER.info('')
    LOGGER.info('Demo commplete.')            
    input('\nPress Enter to continue... ')

if __name__ == "__main__":
    lh.configure_logger(log_format=lh.DEFAULT_CONSOLE_LOGFMT, log_level="INFO", brightness=False)
    demo()
