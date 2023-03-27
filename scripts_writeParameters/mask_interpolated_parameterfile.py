
#### AIM: mask every 1st and 2nd cell of parameters file with binary mask file and then interpolate missing cells 

import numpy as np
import netCDF4 as nc
import xarray as xr
import matplotlib.pylab as plt
import subprocess
import settings as s
from pathlib import Path



## set missval for parameters file (org)
parameter_filepath = s.output_dir / s.trace_file 
parameter_filepath_nan = Path.joinpath(s.output_dir, Path(s.trace_file).stem + "_nan.nc4") 

# set filling value "1.e+20" as nan
cmd = "cdo setctomiss,1.e+20 " +str(parameter_filepath) + " " + str(parameter_filepath_nan)
try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)


##  mask parameter.nc file with the binary mask file by multiplying them.
mask = s.input_dir / s.dataset / s.testarea / s.b_mask 
parameter_filepath_nan_m = Path.joinpath(s.output_dir, Path(parameter_filepath_nan).stem + "_m.nc4") 
print("parameter_filepath_nan_masked", parameter_filepath_nan_m)

cmd = "cdo mul " + str(mask) + " " + str(parameter_filepath_nan) + " " + str(parameter_filepath_nan_m)
try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)


## converting Normal value to NaN value so that cdo interprets them as missing values during interpolation
parameter_filepath_nan_m_i_n4 = Path.joinpath(s.output_dir, Path(parameter_filepath_nan_m).stem + "_n4.nc4")


## interpolate missing values in paramters file
## [setmisstodis, neighbors]: distance-weighted average of the nearest non missing values
cmd = "cdo setmisstodis,4 " +  str(parameter_filepath_nan_m) + " " + str(parameter_filepath_nan_m_i_n4) # still has nan

try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)






