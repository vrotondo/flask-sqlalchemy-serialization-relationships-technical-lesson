from models import *


class TestAnimal:
    '''Class Animal in models.py'''

    def test_converts_to_dict(self):
        '''can convert Animal objects to dictionaries.'''
        a = Animal()
        assert a.to_dict()
        assert isinstance(a.to_dict(), dict)


class TestEnclosure:
    '''Class Enclosure in models.py'''

    def test_converts_to_dict(self):
        '''can convert Enclosure objects to dictionaries.'''
        e = Enclosure()
        assert e.to_dict()
        assert isinstance(e.to_dict(), dict)


class TestZookeeper:
    '''Class Zookeeper in models.py'''

    def test_converts_to_dict(self):
        '''can convert Zookeeper objects to dictionaries.'''
        z = Zookeeper()
        assert z.to_dict()
        assert isinstance(z.to_dict(), dict)
