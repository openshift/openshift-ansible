#!/usr/bin/env python2
'''
 Unit tests for yedit
'''

import unittest
import os
import yaml

class YeditException(Exception):
    ''' Exception class for Yedit '''
    pass

class Yedit(object):
    ''' Class to modify yaml files '''

    def __init__(self, filename):
        self.filename = filename
        self.__yaml_dict = None
        self.get()

    @property
    def yaml_dict(self):
        ''' get property for yaml_dict '''
        return self.__yaml_dict

    @yaml_dict.setter
    def yaml_dict(self, value):
        ''' setter method for yaml_dict '''
        self.__yaml_dict = value

    @staticmethod
    def remove_entry(data, keys):
        ''' remove an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            keys = a.b
            item = c
        '''
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key in data.keys():
                Yedit.remove_entry(data[key], rest)
        else:
            del data[keys]

    @staticmethod
    def add_entry(data, keys, item):
        ''' Add an item to a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            keys = a.b
            item = c
        '''
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in data:
                data[key] = {}

            if not isinstance(data, dict):
                raise YeditException('Invalid add_entry called on data [%s].' % data)
            else:
                Yedit.add_entry(data[key], rest, item)

        else:
            data[keys] = item


    @staticmethod
    def get_entry(data, keys):
        ''' Get an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            keys = a.b
            return c
        '''
        if keys and "." in keys:
            key, rest = keys.split(".", 1)
            if not isinstance(data[key], dict):
                raise YeditException('Invalid get_entry called on a [%s] of type [%s].' % (data, type(data)))

            else:
                return Yedit.get_entry(data[key], rest)

        else:
            return data.get(keys, None)


    def write(self):
        ''' write to file '''
        with open(self.filename, 'w') as yfd:
            yfd.write(yaml.dump(self.yaml_dict, default_flow_style=False))

    def read(self):
        ''' write to file '''
        # check if it exists
        if not self.exists():
            return None

        contents = None
        with open(self.filename) as yfd:
            contents = yfd.read()

        return contents

    def exists(self):
        ''' return whether file exists '''
        if os.path.exists(self.filename):
            return True

        return False
    def get(self):
        ''' return yaml file '''
        contents = self.read()

        if not contents:
            return None

        # check if it is yaml
        try:
            self.yaml_dict = yaml.load(contents)
        except yaml.YAMLError as _:
            # Error loading yaml
            return None

        return self.yaml_dict

    def delete(self, key):
        ''' put key, value into a yaml file '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None
        if not entry:
            return  (False, self.yaml_dict)

        Yedit.remove_entry(self.yaml_dict, key)
        self.write()
        return (True, self.get())

    def put(self, key, value):
        ''' put key, value into a yaml file '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None

        if entry == value:
            return (False, self.yaml_dict)

        Yedit.add_entry(self.yaml_dict, key, value)
        self.write()
        return (True, self.get())

    def create(self, key, value):
        ''' create the file '''
        if not self.exists():
            self.yaml_dict = {key: value}
            self.write()
            return (True, self.get())

        return (False, self.get())



# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name
class YeditTest(unittest.TestCase):
    '''
     Test class for yedit
    '''
    data = {'a': 'a',
            'b': {'c': {'d': ['e', 'f', 'g']}},
           }

    filename = 'yedit_test.yml'

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        yed = Yedit(YeditTest.filename)
        yed.yaml_dict = YeditTest.data
        yed.write()

    def test_get(self):
        ''' Testing a get '''
        yed = Yedit('yedit_test.yml')

        self.assertEqual(yed.yaml_dict, self.data)

    def test_write(self):
        ''' Testing a simple write '''
        yed = Yedit('yedit_test.yml')
        yed.put('key1', 1)
        yed.write()
        yed.get()
        self.assertTrue(yed.yaml_dict.has_key('key1'))
        self.assertEqual(yed.yaml_dict['key1'], 1)

    def test_write_x_y_z(self):
        '''Testing a write of multilayer key'''
        yed = Yedit('yedit_test.yml')
        yed.put('x.y.z', 'modified')
        yed.write()
        self.assertEqual(Yedit.get_entry(yed.get(), 'x.y.z'), 'modified')

    def test_delete_a(self):
        '''Testing a simple delete '''
        yed = Yedit('yedit_test.yml')
        yed.delete('a')
        yed.write()
        yed.get()
        self.assertTrue(not yed.yaml_dict.has_key('a'))

    def test_delete_b_c(self):
        '''Testing delete of layered key '''
        yed = Yedit('yedit_test.yml')
        yed.delete('b.c')
        yed.write()
        yed.get()
        self.assertTrue(yed.yaml_dict.has_key('b'))
        self.assertFalse(yed.yaml_dict['b'].has_key('c'))

    def test_create(self):
        '''Testing a create '''
        os.unlink(YeditTest.filename)
        yed = Yedit('yedit_test.yml')
        yed.create('foo', 'bar')
        yed.write()
        yed.get()
        self.assertTrue(yed.yaml_dict.has_key('foo'))
        self.assertTrue(yed.yaml_dict['foo'], 'bar')

    def tearDown(self):
        '''TearDown method'''
        os.unlink(YeditTest.filename)

if __name__ == "__main__":
    unittest.main()
