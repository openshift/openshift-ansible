#!/usr/bin/env python2
'''
 Unit tests for MultiInventory
'''

import unittest
import multi_inventory

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name
class MultiInventoryTest(unittest.TestCase):
    '''
     Test class for multiInventory
    '''

#    def setUp(self):
#        '''setup method'''
#        pass

    def test_merge_simple_1(self):
        '''Testing a simple merge of 2 dictionaries'''
        a = {"key1" : 1}
        b = {"key1" : 2}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"key1": [1, 2]})

    def test_merge_b_empty(self):
        '''Testing a merge of an emtpy dictionary'''
        a = {"key1" : 1}
        b = {}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"key1": 1})

    def test_merge_a_empty(self):
        '''Testing a merge of an emtpy dictionary'''
        b = {"key1" : 1}
        a = {}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"key1": 1})

    def test_merge_hash_array(self):
        '''Testing a merge of a dictionary and a dictionary with an array'''
        a = {"key1" : {"hasha": 1}}
        b = {"key1" : [1, 2]}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"key1": [{"hasha": 1}, 1, 2]})

    def test_merge_array_hash(self):
        '''Testing a merge of a dictionary with an array and a dictionary with a hash'''
        a = {"key1" : [1, 2]}
        b = {"key1" : {"hasha": 1}}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"key1": [1, 2, {"hasha": 1}]})

    def test_merge_keys_1(self):
        '''Testing a merge on a dictionary for keys'''
        a = {"key1" : [1, 2], "key2" : {"hasha": 2}}
        b = {"key2" : {"hashb": 1}}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"key1": [1, 2], "key2": {"hasha": 2, "hashb": 1}})

    def test_merge_recursive_1(self):
        '''Testing a recursive merge'''
        a = {"a" : {"b": {"c": 1}}}
        b = {"a" : {"b": {"c": 2}}}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"a": {"b": {"c": [1, 2]}}})

    def test_merge_recursive_array_item(self):
        '''Testing a recursive merge for an array'''
        a = {"a" : {"b": {"c": [1]}}}
        b = {"a" : {"b": {"c": 2}}}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"a": {"b": {"c": [1, 2]}}})

    def test_merge_recursive_hash_item(self):
        '''Testing a recursive merge for a hash'''
        a = {"a" : {"b": {"c": {"d": 1}}}}
        b = {"a" : {"b": {"c": 2}}}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"a": {"b": {"c": [{"d": 1}, 2]}}})

    def test_merge_recursive_array_hash(self):
        '''Testing a recursive merge for an array and a hash'''
        a = {"a" : [{"b": {"c":  1}}]}
        b = {"a" : {"b": {"c": 1}}}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"a": [{"b": {"c": 1}}]})

    def test_merge_recursive_hash_array(self):
        '''Testing a recursive merge for an array and a hash'''
        a = {"a" : {"b": {"c": 1}}}
        b = {"a" : [{"b": {"c":  1}}]}
        result = {}
        _ = [multi_inventory.MultiInventory.merge_destructively(result, x) for x in [a, b]]
        self.assertEqual(result, {"a": [{"b": {"c": 1}}]})

#    def tearDown(self):
#        '''TearDown method'''
#        pass

if __name__ == "__main__":
    unittest.main()
