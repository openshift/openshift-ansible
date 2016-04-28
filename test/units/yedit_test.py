#!/usr/bin/env python2
'''
 Unit tests for yedit
'''

import unittest
import os

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name,no-name-in-module
from yedit import Yedit

class YeditTest(unittest.TestCase):
    '''
     Test class for yedit
    '''
    data = {'a': 'a',
            'b': {'c': {'d': [{'e': 'x'}, 'f', 'g']}},
           }

    filename = 'yedit_test.yml'

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        yed = Yedit(YeditTest.filename)
        yed.yaml_dict = YeditTest.data
        yed.write()

    def test_load(self):
        ''' Testing a get '''
        yed = Yedit('yedit_test.yml')
        self.assertEqual(yed.yaml_dict, self.data)

    def test_write(self):
        ''' Testing a simple write '''
        yed = Yedit('yedit_test.yml')
        yed.put('key1', 1)
        yed.write()
        self.assertTrue(yed.yaml_dict.has_key('key1'))
        self.assertEqual(yed.yaml_dict['key1'], 1)

    def test_write_x_y_z(self):
        '''Testing a write of multilayer key'''
        yed = Yedit('yedit_test.yml')
        yed.put('x.y.z', 'modified')
        yed.write()
        yed.load()
        self.assertEqual(yed.get('x.y.z'), 'modified')

    def test_delete_a(self):
        '''Testing a simple delete '''
        yed = Yedit('yedit_test.yml')
        yed.delete('a')
        yed.write()
        yed.load()
        self.assertTrue(not yed.yaml_dict.has_key('a'))

    def test_delete_b_c(self):
        '''Testing delete of layered key '''
        yed = Yedit('yedit_test.yml')
        yed.delete('b.c')
        yed.write()
        yed.load()
        self.assertTrue(yed.yaml_dict.has_key('b'))
        self.assertFalse(yed.yaml_dict['b'].has_key('c'))

    def test_create(self):
        '''Testing a create '''
        os.unlink(YeditTest.filename)
        yed = Yedit('yedit_test.yml')
        yed.create('foo', 'bar')
        yed.write()
        yed.load()
        self.assertTrue(yed.yaml_dict.has_key('foo'))
        self.assertTrue(yed.yaml_dict['foo'] == 'bar')

    def test_create_content(self):
        '''Testing a create with content '''
        content = {"foo": "bar"}
        yed = Yedit("yedit_test.yml", content)
        yed.write()
        yed.load()
        self.assertTrue(yed.yaml_dict.has_key('foo'))
        self.assertTrue(yed.yaml_dict['foo'], 'bar')

    def test_array_insert(self):
        '''Testing a create with content '''
        yed = Yedit("yedit_test.yml")
        yed.put('b.c.d[0]', 'inject')
        self.assertTrue(yed.get('b.c.d[0]') == 'inject')

    def test_array_insert_first_index(self):
        '''Testing a create with content '''
        yed = Yedit("yedit_test.yml")
        yed.put('b.c.d[0]', 'inject')
        self.assertTrue(yed.get('b.c.d[1]') == 'f')

    def test_array_insert_second_index(self):
        '''Testing a create with content '''
        yed = Yedit("yedit_test.yml")
        yed.put('b.c.d[0]', 'inject')
        self.assertTrue(yed.get('b.c.d[2]') == 'g')

    def test_dict_array_dict_access(self):
        '''Testing a create with content'''
        yed = Yedit("yedit_test.yml")
        yed.put('b.c.d[0]', [{'x': {'y': 'inject'}}])
        self.assertTrue(yed.get('b.c.d[0].[0].x.y') == 'inject')

    def test_dict_array_dict_replace(self):
        '''Testing multilevel delete'''
        yed = Yedit("yedit_test.yml")
        yed.put('b.c.d[0]', [{'x': {'y': 'inject'}}])
        yed.put('b.c.d[0].[0].x.y', 'testing')
        self.assertTrue(yed.yaml_dict.has_key('b'))
        self.assertTrue(yed.yaml_dict['b'].has_key('c'))
        self.assertTrue(yed.yaml_dict['b']['c'].has_key('d'))
        self.assertTrue(isinstance(yed.yaml_dict['b']['c']['d'], list))
        self.assertTrue(isinstance(yed.yaml_dict['b']['c']['d'][0], list))
        self.assertTrue(isinstance(yed.yaml_dict['b']['c']['d'][0][0], dict))
        self.assertTrue(yed.yaml_dict['b']['c']['d'][0][0]['x'].has_key('y'))
        self.assertTrue(yed.yaml_dict['b']['c']['d'][0][0]['x']['y'], 'testing')

    def test_dict_array_dict_remove(self):
        '''Testing multilevel delete'''
        yed = Yedit("yedit_test.yml")
        yed.put('b.c.d[0]', [{'x': {'y': 'inject'}}])
        yed.delete('b.c.d[0].[0].x.y')
        self.assertTrue(yed.yaml_dict.has_key('b'))
        self.assertTrue(yed.yaml_dict['b'].has_key('c'))
        self.assertTrue(yed.yaml_dict['b']['c'].has_key('d'))
        self.assertTrue(isinstance(yed.yaml_dict['b']['c']['d'], list))
        self.assertTrue(isinstance(yed.yaml_dict['b']['c']['d'][0], list))
        self.assertTrue(isinstance(yed.yaml_dict['b']['c']['d'][0][0], dict))
        self.assertFalse(yed.yaml_dict['b']['c']['d'][0][0]['x'].has_key('y'))

    def tearDown(self):
        '''TearDown method'''
        os.unlink(YeditTest.filename)

if __name__ == "__main__":
    unittest.main()
