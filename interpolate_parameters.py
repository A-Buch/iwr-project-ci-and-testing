import os
import numpy as np
import netCDF4 as nc
import xarray as xr
import matplotlib.pylab as plt
import subprocess
from pathlib import Path
from scipy.ndimage import minimum_filter
import pickle
import itertools as it

import settings as s
import attrici.datahandler as dh
import attrici.postprocess as pp


# remove_intermediate_files = False

# def interpolation_parameters(parameter_filepath, landsea_mask_filepath):
    # """
    # params: 
    # return: filepath to interpolated parameter file
    # """

## create parameter file from trace files

## create file to store parameters if not exists, otherwise interpolate existing file
input_file = s.input_dir / s.dataset / s.testarea / s.source_file.lower()
landsea_mask_filepath = s.input_dir /  s.dataset / s.testarea / s.landsea_file

obs_data = nc.Dataset(input_file, "r")
nct = obs_data.variables["time"]
lats = obs_data.variables["lat"][:]
lons = obs_data.variables["lon"][:]

parameter_filepath = s.output_dir / s.trace_file
if not os.path.exists(parameter_filepath):
    out = nc.Dataset(parameter_filepath, "w", format="NETCDF4") 
    pp.form_global_nc(out, nct[:8], lats, lons, None, nct.units)
    out.close()

parameter_file = nc.Dataset(parameter_filepath, "a", format="NETCDF4") 

### check which data is available
data_list = []
lat_indices = []
lon_indices = []
lat_float_l = []
lon_float_l = []

trace_dir = s.output_dir / "traces" / s.variable
for i in trace_dir.glob("**/lon*"):
    data_list.append(str(i))
    lat_float = float(str(i).split("lat")[-1].split("_")[-1].split("/")[0])
    lon_float = float(str(i).split("lon")[-1])
    lat_float_l.append(lat_float)
    lon_float_l.append(lon_float)

## get each coordinate index for regional AOI
## TODO: test with other lateral_sub
if s.lateral_sub == 1 :
    lat_indices.append( pp.rescale_aoi(lat_float_l))
    lon_indices.append( pp.rescale_aoi(lon_float_l))

# TODO: make this nicer
## remove double list
[lat_indices ] = lat_indices
[lon_indices ] = lon_indices


for (i, j, dfpath) in it.zip_longest(lat_indices, lon_indices, data_list):
#for outdir_for_cell in data_list:
    print(dfpath)
#    try:
    print("Writing parameters  from trace files to parameter file.")
    with open(dfpath, 'rb') as handle:
        free_params = pickle.load(handle) ## load from trace.h5 files

    # write the values of each parameter as single layers to nc file, i.e. one parameter can contain 1 to n layers
    param_names = list(free_params.keys())

    for param_name in param_names:
        values_per_parameter = np.atleast_1d(np.array(free_params[param_name])) # forcing 0-D arrays to 1-D
        ## ## create empty variable in netcdf if not exists
        if param_name in parameter_file.variables.keys():
            pass
        else:
            parameter_file.createVariable(param_name, "f4", ("time", "lat", "lon"), chunksizes=(nct[:8].shape[0], 1, 1), fill_value=1e20) 
        parameter_file.variables[param_name][ :, int(i), int(j)] = values_per_parameter
        #for n in range(len(values_per_parameter)):
            #out.variables[param_name][ n, int(lat_idx), int(lon_idx)] = values_per_parameter[n] #np.array(values_per_parameter[n])
    print(f"wrote all {len(param_names)} to cell position",  int(i), int(j))

parameter_file.close()



## load binary mask of nth * nth cells
bmask_filepath = s.input_dir / s.dataset / s.testarea / s.bmask_file
bmask = xr.open_dataset(bmask_filepath)
print("binary mask:\n", bmask)

## get support cells from binary mask and coastline
parameter_file = xr.open_dataset(parameter_filepath)
parameter_file_m = parameter_file * bmask.binary_mask[0,:,:] # every 3rd cell is support cell
    
coastmask = parameter_file.notnull()
#m = minimum_filter(mask, size=2, mode='reflect')
coastmask = minimum_filter(coastmask.weights_fc_trend, size=(0,3,3), mode='nearest')
coastlines = parameter_file.where(~coastmask) # extract coast lines
parameter_file_m = parameter_file_m.merge(coastlines, join="outer", compat="no_conflicts") ###  every 3rd cell + cells from coastline are support cells

parameter_filepath_m = Path.joinpath(s.output_dir, Path(parameter_filepath).stem + "_m.nc4")
parameter_file_m.to_netcdf(parameter_filepath_m, format="NETCDF4")
parameter_file_m.close()

##  let cdo recognize nan values in masked parameters file
print("set masked values of parameter file as nan")
parameter_filepath_m_nan = Path.joinpath(s.output_dir, Path(parameter_filepath_m).stem + "_nan.nc4")

cmd = "cdo setmissval,nan " + str(parameter_filepath_m) + " " + str(parameter_filepath_m_nan)
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
parameter_filepath_m_nan_n4 = Path.joinpath(s.output_dir, Path(parameter_filepath_m_nan).stem + "_n4.nc4")

cmd = "cdo -setmisstodis,4 " +  str(parameter_filepath_m_nan) + " " + str(parameter_filepath_m_nan_n4) 

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

## TODO: workaround to fix representation in python while dimensions of parameter file are the same as in landsea_mask
parameter_m_nan_n4_clipped = parameter_m_nan_n4 * np.array(landsea_mask["mask"][0, :, :].reindex(lat=landsea_mask.lat[::-1])) # landseamask.lat is flipped in relation to parameter file
parameter_m_nan_n4_clipped.to_netcdf(parameter_filepath_m_nan_n4_clipped, format="NETCDF4")
print(f"Generated interpolated parameters, stored in {parameter_filepath_m_nan_n4_clipped}")
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
    
# return parameter_m_nan_n4_clipped





