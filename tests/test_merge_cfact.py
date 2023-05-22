#!/usr/bin/env python3
# coding: utf-8

import sys, os
sys.path.append("..")  # search within parent dir of tests_folder
import pytest

from attrici import postprocess as pp


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
