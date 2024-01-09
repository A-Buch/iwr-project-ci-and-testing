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
from scipy.ndimage import minimum_filter


# remove_intermediate_files = False

def interpolation_parameters(parameter_filepath, landsea_mask_filepath):
    """
    params: 
    return: filepath to interpolated parameter file
    """


    ## generate binary mask of nth * nth cells
    x = np.arange(0, s.file_len)
    bmask = np.full(len(x) * s.file_len, np.nan).reshape(s.file_len, s.file_len)
    bmask[::3 , ::3] = np.int64(1)
    print("binary mask:\n", bmask)

    ## get support cells from binary mask and coastline
    parameter_file = xr.open_dataset(parameter_filepath)
    parameter_file_m = bmask * parameter_file
        
    coastmask = parameter_file.notnull()
    #m = minimum_filter(mask, size=2, mode='reflect')
    coastmask = minimum_filter(coastmask.weights_fc_trend, size=(0,3,3), mode='nearest')
    coastlines = parameter_file.where(~coastmask) # extract coast lines
    parameter_file_m= parameter_file_m.merge(coastlines, join="outer", compat="no_conflicts") ### add coastline as support cells 
    
    parameter_file_m = Path.joinpath(s.output_dir, Path(parameter_filepath).stem + "_m.nc4")
    parameter_file_m.to_netcdf(parameter_file_m, format="NETCDF4")
    parameter_file_m.close()

    ## fix: let cdo recognize nan values in masked parameters file
    print("set masked values of parameter file as nan")
    parameter_filepath_m_nan = Path.joinpath(s.output_dir, Path(parameter_file_m).stem + "_nan.nc4")

    cmd = "cdo -setmissval,nan " + str(parameter_filepath_m) + " " + str(parameter_filepath_m_nan)
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
    print("interpolating..")
    ## [setmisstodis, neighbors]: distance-weighted average of the nearest non missing values
    parameter_filepath_m_nan_n4 = Path.joinpath(s.output_dir, Path(parameter_filepath_m_nan).stem + "_nan_n4.nc4")

    cmd = "cdo -setmisstodis,4 " +  str(parameter_filepath_m_nan) + " " + str(parameter_filepath_m_nan_n4) 
    # parameter_filepath_m_nan=in , out=parameter_filepath_nan_m_nan_n4

    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        cmd = "module load cdo && " + cmd
        print(cmd)
        subprocess.check_call(cmd, shell=True)

    ## clip new interpolated parameter file with landsea_mask to remove interpolation from sea area
    #input_dir + "/" + dataset + "/" + testarea  + f'/landseamask_{file_len}_setmissval.nc'
    landsea_mask = xr.open_dataset(landsea_mask_filepath)
    parameter_m_nan_n4 = xr.open_dataset(parameter_filepath_m_nan_n4)
    parameter_filepath_m_nan_n4_clipped = Path.joinpath(s.output_dir, Path(parameter_filepath_m_nan_n4).stem + "_c.nc4")

    print(f"Generated interpolated parameters, stored in {parameter_filepath_m_nan_n4_clipped}")

    landsea_mask["mask"][0, :, :] = landsea_mask["mask"][0, :, :].transpose("lat", "lon") # reorder dimensions equal to shape of parameter file
    parameter_m_nan_n4_clipped = parameter_m_nan_n4 * landsea_mask["mask"][0, :, :]
    parameter_m_nan_n4_clipped.to_netcdf(parameter_filepath_m_nan_n4_clipped, format="NETCDF4")
    parameter_m_nan_n4_clipped.close()
    
    # cmd = "cdo -mul " + str(landsea_mask_filepath) + " " + str(parameter_filepath_m_nan_n4) + " " + str(parameter_filepath_m_nan_n4_clipped) 
    # try:
        # print(cmd)
        # subprocess.check_call(cmd, shell=True)
    # except subprocess.CalledProcessError:
        # cmd = "module load cdo && " + cmd
        # print(cmd)
        # subprocess.check_call(cmd, shell=True)


    # if remove_intermediate_files == True:
        # print(f"Removing: {parameter_filepath_nan_m, parameter_filepath_nan_m_nan}")
        # os.remove(parameter_filepath_nan)
        # os.remove(parameter_filepath_nan_m)
        # os.remove(parameter_filepath_nan_m_nan)
        
    return parameter_m_nan_n4_clipped




