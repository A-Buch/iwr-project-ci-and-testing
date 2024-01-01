
import sys, os
from pathlib import Path
import numpy as np
import xarray as xr
import logging

# import pytest
import unittest

sys.path.append("../")  # search within parent dir of tests_folder
import attrici.postprocess as pp
import settings as s
from sanity_check import estimation_quality_check as e
from sanity_check import count_replaced_values as c


## get logger
logger = s.init_logger('__test__')

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
        self.ts_dir = Path(f"{s.output_dir}/timeseries/{self.variable}")


    def test_number_files_equals_number_landcells(self):
        """
        test if enough land-cells were processed by comparing number of files with number of land cells
        """
        lsm_file = s.input_dir / f"landmask_{self.tile}_demo.nc"
        lsm = xr.load_dataset(lsm_file)
        nbr_landcells = lsm["area_European_01min"].count().values.tolist()
        print(f"Tile: {self.tile}, Variable: {self.variable, self.variable_hour}: {nbr_landcells} Land cells in lsm" )

        print("Searching in", self.ts_dir)
        nbr_files = e.count_files_in_directory(self.ts_dir, ".h5")

        self.assertEqual( 
            nbr_files, 
            nbr_landcells,
            f"{nbr_files} number of timeseries files <-> {nbr_landcells} number of land cells"   
        )


    def test_occurrence_empty_files(self):
        """
        test if empty temporary files were created
        """
        ## ckeck for empty trace or timeseries file, due that some folders were moved by "rsync" but with --partial flag
        ts_files = self.ts_dir.rglob(f"*.h5")
        assert all([os.stat(file).st_size != 0  for file in ts_files]),  f"empty files exists in {self.ts_dir}"
        
        trace_dir = self.ts_dir.parent / "traces"
        trace_files = trace_dir.rglob(f"lon*")

        self.assertTrue(
            all([os.stat(file).st_size != 0  for file in trace_files]), 
            f"empty file(s) exist in {trace_dir}"  
        )



    def test_number_failing_cells(self):
        """
        test if processing of cells failed 
        """
        ## check amount of failing cells
        failing_cells = self.ts_dir.parent.parent / "./failing_cells.log"
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