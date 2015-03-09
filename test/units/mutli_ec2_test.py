#!/usr/bin/env python2

import unittest
import sys
import os
import sys
import multi_ec2

class MultiEc2Test(unittest.TestCase):

    def setUp(self):
        pass

    def test_merge_simple_1(self):
        a = {"key1" : 1}
        b = {"key1" : 2}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"key1": [1,2]})

    def test_merge_b_empty(self):
        a = {"key1" : 1}
        b = {}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"key1": 1})

    def test_merge_a_empty(self):
        b = {"key1" : 1}
        a = {}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"key1": 1})

    def test_merge_hash_array(self):
        a = {"key1" : {"hasha": 1}}
        b = {"key1" : [1,2]}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"key1": [{"hasha": 1}, 1,2]})

    def test_merge_array_hash(self):
        a = {"key1" : [1,2]}
        b = {"key1" : {"hasha": 1}}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"key1": [1,2, {"hasha": 1}]})

    def test_merge_keys_1(self):
        a = {"key1" : [1,2], "key2" : {"hasha": 2}}
        b = {"key2" : {"hashb": 1}}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"key1": [1,2], "key2": {"hasha": 2, "hashb": 1}})

    def test_merge_recursive_1(self):
        a = {"a" : {"b": {"c": 1}}}
        b = {"a" : {"b": {"c": 2}}}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"a": {"b": {"c": [1,2]}}})

    def test_merge_recursive_array_item(self):
        a = {"a" : {"b": {"c": [1]}}}
        b = {"a" : {"b": {"c": 2}}}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"a": {"b": {"c": [1,2]}}})

    def test_merge_recursive_hash_item(self):
        a = {"a" : {"b": {"c": {"d": 1}}}}
        b = {"a" : {"b": {"c": 2}}}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"a": {"b": {"c": [{"d": 1}, 2]}}})

    def test_merge_recursive_array_hash(self):
        a = {"a" : [{"b": {"c":  1}}]}
        b = {"a" : {"b": {"c": 1}}}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"a": [{"b": {"c": 1}}]})

    def test_merge_recursive_hash_array(self):
        a = {"a" : {"b": {"c": 1}}}
        b = {"a" : [{"b": {"c":  1}}]}
        result = {}
        [multi_ec2.MultiEc2.merge_destructively(result, x) for x in [a,b]]
        self.assertEqual(result, {"a": [{"b": {"c": 1}}]})

    def tearDown(self):
        pass

if __name__ == "__main__":
  unittest.main()
