# %% [markdown]
# #### AIM: mask every 1st and 2nd cell of parameters file with binary mask file and then interpolate missing cells 

import os
import numpy as np
import netCDF4 as nc
import xarray as xr
import matplotlib.pylab as plt
import subprocess
import settings as s
from pathlib import Path


remove_intermediate_files = False


# # set missval for parameters file (org)
parameter_filepath = s.output_dir / s.trace_file 
# parameter_filepath_nan = Path.joinpath(s.output_dir, Path(s.trace_file).stem + "_nan.nc4") # "/p/tmp/annabu/attrici_interpolation/output_corr/tas__cfactual_shape31_org_0.nc4"

# # set 1.e+20 missing values  
# # TODO maybe not needed, due that setmissval NaN is later done shortly before interpolation
# cmd = "cdo -setmissval,1.e+20 " +str(parameter_filepath) + " " + str(parameter_filepath_nan)
# try:
    # print(cmd)
    # subprocess.check_call(cmd, shell=True)
# except subprocess.CalledProcessError:
    # cmd = "module load cdo && " + cmd
    # print(cmd)
    # subprocess.check_call(cmd, shell=True)


##  mask parameter.nc file with the binary mask file by multiplying them.
b_mask = s.input_dir / s.dataset / s.testarea / s.b_mask #"/p/tmp/annabu/meteo_data/b_mask_for_interpolation_16.nc"
## inf_param = s.output_dir / s.trace_file #"/p/tmp/annabu/output_corr/tas_trace_shape16.nc4"
#parameter_filepath_nan_m = Path.joinpath(s.output_dir, Path(parameter_filepath_nan).stem + "_ma.nc4") #"/p/tmp/annabu/output_corr/tas_trace_shape16_masked_v2.nc4"
parameter_filepath_m = Path.joinpath(s.output_dir, Path(parameter_filepath).stem + "_ma.nc4") #"/p/tmp/annabu/output_corr/tas_trace_shape16_masked_v2.nc4"

cmd = "cdo mul " + str(b_mask) + " " + str(parameter_filepath) + " " + str(parameter_filepath_m)
#cmd = "cdo mul " + str(b_mask) + " " + str(parameter_filepath_nan) + " " + str(parameter_filepath_nan_m)

try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)



## fix: let cdo recognize nan values in masked parameters file
print("set masked values of parameter file as nan")
parameter_filepath_nan_m_nan = Path.joinpath(s.output_dir, Path(parameter_filepath_m).stem + "_nan.nc4")

cmd = "cdo -setmissval,nan " + str(parameter_filepath_m) + " " + str(parameter_filepath_nan_m_nan)
#cmd = "cdo -setmissval,nan " + str(parameter_filepath_nan_m) + " " + str(parameter_filepath_nan_m_nan)

try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)


## converting Normal value to NaN value so that cdo interprets them as missing values during interpolation
#cmd = "cdo setmissval,nan " + masked_params_filepath + f" {outpath}/tas_trace_shape16_masked_setmissval_nan.nc4"

## interpolate missing values in paramters file
## [setmisstodis, neighbors]: distance-weighted average of the nearest non missing values
parameter_filepath_nan_m_nan_n4 = Path.joinpath(s.output_dir, Path(parameter_filepath_nan_m_nan).stem + "_n4.nc4")

cmd = "cdo -setmisstodis,4 " +  str(parameter_filepath_nan_m_nan) + " " + str(parameter_filepath_nan_m_nan_n4) 

try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)


## TODO: check if sea area has different missing values than for cells which should interpolated
## clip new interpolated parameter file with landsea_mask to remove interpolation from sea area
landseamask = Path.joinpath(s.input_dir, s.dataset, s.testarea, "landseamask_31_setmissval.nc") 
#input_dir + "/" + dataset + "/" + testarea  + f'/landseamask_{file_len}_setmissval.nc'
parameter_filepath_nan_m_nan_n4_clipped = Path.joinpath(s.output_dir, Path(parameter_filepath_nan_m_nan_n4).stem + "_c.nc4")

cmd = "cdo -mul " + str(landseamask) + " " + str(parameter_filepath_nan_m_nan_n4) + " " + str(parameter_filepath_nan_m_nan_n4_clipped) 

try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)



if remove_intermediate_files == True:
    print(f"Removing: {parameter_filepath_nan, parameter_filepath_nan_m, parameter_filepath_nan_m_nan}")
    os.remove(parameter_filepath_nan)
    os.remove(parameter_filepath_nan_m)
    os.remove(parameter_filepath_nan_m_nan)





