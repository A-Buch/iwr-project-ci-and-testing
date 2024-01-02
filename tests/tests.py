#!/usr/bin/env python3
# coding: utf-8

import sys
import os
from pathlib import Path
import numpy as np
import xarray as xr
import unittest

sys.path.append("../") # search within parent dir of tests_folder
import attrici.postprocess as pp
import attrici.sanity_check.estimation_quality_check as e
import settings as s


## get logger
# logger = s.init_logger("__test__")  # TODO replace print statement by logger message

## NOTE run single unittest in cell of jupyter nb: unittest.main(argv=[''], verbosity=2, exit=False)


class TestPostprocess(unittest.TestCase):

    def test_rescale_aoi(self):
        """
        unit test for input variable of rescale_aoi()
        """
        coord_list = np.array([62.39166667, 62.375, 62.35833333])
        coord_list_shuffled =  np.array([ 62.375, 62.35833333, 62.39166667])
        coord_list_negative =  np.array([-62.39166667, -62.375, 62.35833333])

        assert pp.rescale_aoi(coord_list, 62.375) == [1]
        assert pp.rescale_aoi(coord_list_shuffled, 62.375) == [0]
        assert pp.rescale_aoi(coord_list_negative, -62.375) == [1]


class TestProcessing(unittest.TestCase):
    """
    test class for temporary output from run_estimation.py() and write_netcdf.py()
    """

    def setUp(self):
        self.tile = s.tile
        self.variable_hour = s.hour
        self.variable = s.variable
        # self.ts_dir = Path(f"{s.output_dir}/timeseries/{self.variable}")
        # self.trace_dir = Path(f"{s.output_dir}/traces/{self.variable}")
        self.ts_dir = Path(f"../demo_output/timeseries/{self.variable}")  # TODO fix workaround with outpaths to test unittests in CI
        self.trace_dir = Path(f"../demo_output/traces/{self.variable}") #self.ts_dir.parent / "traces" / f"{self.variable}"
        self.lsm_file = Path(f"../demo_input/ERA5/{self.tile}") / f"landmask_{self.tile}_demo.nc"


    def test_number_files_equals_number_landcells(self):
        """
        test if enough land-cells were processed by comparing number of files with number of land cells
        """
        lsm = xr.load_dataset(self.lsm_file)
        nbr_landcells = lsm["area_European_01min"].count().values.tolist()
        print(f"Tile: {self.tile}, Variable: {self.variable, self.variable_hour}: {nbr_landcells} Land cells in lsm")

        print("Searching in", self.trace_dir)
        nbr_files = e.count_files_in_directory(self.trace_dir, ".*")

        self.assertEqual(
            nbr_files,
            nbr_landcells,
            f"{nbr_files} number of timeseries files <-> {nbr_landcells} number of land cells"
        )

    ## TODO do monkeypatching or similar to imitate landmask, trace and timeseries files
    def test_occurrence_empty_files(self):
        """
        test if empty temporary files were created
        """
        ## ckeck for empty trace files
        trace_files = self.trace_dir.rglob("lon*")

        self.assertTrue(
            all([os.stat(file).st_size != 0  for file in trace_files]),
            f"empty file(s) exist in {self.trace_dir}"
        )
    

    # ## TODO do monkeypatching or similar 
    def test_number_failing_cells(self):
        """
        test if processing of cells failed
        """
        ## check amount of failing cells
        failing_cells = self.trace_dir.parent.parent / "./failing_cells.log"
        print(failing_cells)
        with open(failing_cells, "r") as f:
             nbr_failcells = sum(1 for _ in f)

        self.assertEqual(
            nbr_failcells,
            0,
            f"failing cells in tile: {self.tile}, variable: {self.variable, self.variable_hour}"
        )


if __name__ == "__main__":
    unittest.main()
    print("Run all tests")
