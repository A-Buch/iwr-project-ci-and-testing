#!/usr/bin/env python3
# coding: utf-8

import sys, os
import pytest
import unittest 
from pathlib import Path
import glob 
import numpy as np
import xarray as xr
import pickle
import re
import subprocess

sys.path.append("..")  # search within parent dir of tests_folder
import interpolate_parameters    
import settings as s    

## TODO:
## test simon interpolate.parameters.py here

## Unit test template
# class Test_TestIncrementDecrement(unittest.TestCase):
#     def test_increment(self):
#         self.assertEqual(inc_dec.increment(3), 4)

#     # This test is designed to fail for demonstration purposes.
#     def test_decrement(self):
#         self.assertEqual(inc_dec.decrement(3), 4)
# if __name__ == '__main__':
#     unittest.main()


## set paths
trace_dir = s.output_dir / "traces" / s.variable

test_output = Path("test_output/tas")
test_output.mkdir(exist_ok=True, parents=True)

# Test if merging parameter files and writing them back into single parameter files is the identity function

for trace_file in trace_dir.glob("**/lon*"):
    lat = get_float_from_string(trace_file.parent.name)
    lon = get_float_from_string(trace_file.name)
    data_vars = []
    with open(trace_file, "rb") as trace:
        params_from_model = pickle.load(trace)
    with open(test_output / trace_file.parent.name / trace_file.name, "rb") as trace:
        params_from_merged_file = pickle.load(trace)
    np.testing.assert_equal(params_from_model, params_from_merged_file)

for trace_file in test_output.glob("**/lon*"):
    lat = get_float_from_string(trace_file.parent.name)
    lon = get_float_from_string(trace_file.name)
    data_vars = []
    with open(trace_dir  / trace_file.parent.name / trace_file.name, "rb") as trace:
        params_from_model = pickle.load(trace)
    with open(trace_file , "rb") as trace:
        params_from_meged_file = pickle.load(trace)
    np.testing.assert_equal(params_from_model, params_from_meged_file)



