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
        self.assertTrue(yed.yaml_dict['foo'] == 'bar')

    def test_create_content(self):
        '''Testing a create with content '''
        content = {"foo": "bar"}
        yed = Yedit("yedit_test.yml", content)
        yed.write()
        yed.get()
        self.assertTrue(yed.yaml_dict.has_key('foo'))
        self.assertTrue(yed.yaml_dict['foo'], 'bar')

    def tearDown(self):
        '''TearDown method'''
        os.unlink(YeditTest.filename)

if __name__ == "__main__":
    unittest.main()
