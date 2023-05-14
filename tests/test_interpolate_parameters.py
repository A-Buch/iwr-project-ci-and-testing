#!/usr/bin/env python3
# coding: utf-8

import sys, os


import interpolate_parameters    
import unittest 

class Test_TestIncrementDecrement(unittest.TestCase):
    def test_increment(self):
        self.assertEqual(inc_dec.increment(3), 4)

    # This test is designed to fail for demonstration purposes.
    def test_decrement(self):
        self.assertEqual(inc_dec.decrement(3), 4)

if __name__ == '__main__':
    unittest.main()


# Test if merging parameter files and writing them back into single parameter files is the identity function

for trace_file in trace_dir.glob("**/lon*"):
    lat = get_float_from_string(trace_file.parent.name)
    lon = get_float_from_string(trace_file.name)
    data_vars = []
    with open(trace_file, "rb") as trace:
        params_from_model = pickle.load(trace)
    with open(test_output / trace_file.parent.name / trace_file.name, "rb") as trace:
        params_from_meged_file = pickle.load(trace)
    np.testing.assert_equal(params_from_model, params_from_meged_file)

for trace_file in test_output.glob("**/lon*"):
    lat = get_float_from_string(trace_file.parent.name)
    lon = get_float_from_string(trace_file.name)
    data_vars = []
    with open(trace_dir  / trace_file.parent.name / trace_file.name, "rb") as trace:
        params_from_model = pickle.load(trace)
    with open(trace_file , "rb") as trace:
        params_from_meged_file = pickle.load(trace)
    np.testing.assert_equal(params_from_model, params_from_meged_file)

