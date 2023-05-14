#!/usr/bin/env python3
# coding: utf-8

import pytest
import sys, os
from .attrici import postprocess as pp

### TODO fix sys.path
#curr_path = "/mnt/c/Users/Anna/Documents/UNI/HiWi/IWRcourses_PY_ML_meetings/effective_software_testing/iwr-project-automated-testing-and-continuous-integration/"
#sys.path.insert(0, curr_path)
#sys.path.append("..") # search within parent dir of tests_folder


def test_mixedCoordList_rescale_aoi():
    """
    unit test for input variable of rescale_aoi()
    """
    coord_list = [44.20064, 44.09166666666664,44.190, 44.09166666666664, 44.20064, 44.09166666666664, 44.09166666666664]
    coord_list_shuffled = [-44.09166666666664, 44.190, 44.09166666666664, 44.20064, -44.20064]
    coord_list_negative = [-44.09166666666664, 44.190, -44.20064, -44.20064, -44.09166666666664]
    
    assert pp.rescale_aoi(coord_list) == [2, 0, 1, 0, 2, 0, 0]
    assert pp.rescale_aoi(coord_list_shuffled) == [1, 3, 2, 4, 0]
    assert pp.rescale_aoi(coord_list_negative) == [1, 2, 0, 0, 1]
