# #### AIM: 
# Create binary mask, which is later used to select every third cell from param.nc
# - Binary values:  nan and 1
# - mask.shape: (n*3)+1

import os
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
import subprocess
import settings as s


## TODO make functions


# define shape of binary mask file
file_len = 97 # 16

s.input_dir = "/mnt/c/Users/Anna/Documents/UNI/PIK/develop/test_input"
s.output_dir = "/mnt/c/Users/Anna/Documents/UNI/PIK/develop/test_output_correlation/testarea_97"
s.dataset = "ERA5"


## crop meteo infile to spatial subset (nedded as input for attrici and for landseamask) to nth x nth cells
file_len = 97
meteo_file = str(s.input_dir) + "/" + s.dataset + f"/tas12_era5_1950_2020_00023_ba_ncpdq_merged.nc4"
meteo_clipped_file = str(s.input_dir) + "/" + s.dataset + f"/tas12_era5_1950_2020_00023_ba_ncpdq_merged_{file_len}.nc4"

meteo = xr.open_dataset(meteo_file)
meteo_clipped = meteo.isel(lon=slice(0,file_len), lat=slice(0,file_len))  # select by index
print(meteo_clipped)
meteo_clipped.to_netcdf(meteo_clipped_file, format="NETCDF4")
meteo_clipped.close()
print("clipping by spatial index - done")



## crop meteo infile (nedded as input for attrici and for landseamask) to nth x nth cells
meteo_file = str(s.input_dir) + "/" + s.dataset + f"/tas12_era5_1950_2020_00023_ba_ncpdq_merged.nc4"
meteo_clipped_file = str(s.input_dir) + "/" + s.dataset + f"/tas12_era5_1950_2020_00023_ba_ncpdq_merged_{file_len}.nc4"

meteo = xr.open_dataset(meteo_file)
meteo_clipped = meteo.isel(lon=slice(0,file_len), lat=slice(0,file_len))  # select by index
print(meteo_clipped)
meteo_clipped.to_netcdf(meteo_clipped_file, format="NETCDF4")
meteo_clipped.close()


### create landseamask file from meteo file by overwriting its variables
#landseamask_interim = s.input_dir + "/" + s.dataset + f'/landseamask_{file_len}.nc'
landseamask = s.input_dir + "/" + s.dataset + f'/landseamask_{file_len}_setmissval.nc'
landseamask_2 = s.input_dir + "/" + s.dataset + f'/landseamask_{file_len}_setctomiss.nc'

## assigne first all nan as missing value for CDO, so that they will remain sea in subsequent step
## converting Normal value to NaN value so that cdo interprets them as missing values during interpolation
#cmd = f"cdo -setmissval,nan {inf} {landseamask_interim}"

cmd = f"cdo -setmissval,nan -seltimestep,1 -setrtoc,-1000,1000,1 -chname,{s.variable},mask {meteo_clipped_file} {landseamask}"  # set all values to 1 (except nan) and take 1 layer
try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)

## test ob sea = nan ist in outfile
cmd = f"cdo -setctomiss,0 -seltimestep,1 -setrtoc,-1000,1000,1 -chname,{s.variable},mask {meteo_clipped_file} {landseamask_2}"  # set all values to 1 (except nan) and take 1 layer
#cmd = f"cdo seltimestep,1 setrtoc,-1000,1000,1 {inf} {outf}"  # set all values to 1 (except nan) and take 1 layer
try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)



## generate binary mask of nth * nth cells
x = np.arange(0,file_len)
mask = np.full(len(x)*file_len, np.nan).reshape(file_len, file_len)
mask[::3 , ::3] = np.int64(1)
type(mask[0])
mask

## create binary mask file from before generated landseamask file by overwriting its variables
landseamask_file = s.input_dir + "/" + s.dataset + f'/landseamask_{file_len}_setmissval.nc'
b_mask_file = s.input_dir + "/" + s.dataset + f'/b_mask_{file_len}.nc'

landseamask = xr.open_dataset(landseamask_file)
# print(mask_file.variables)#"].shape
# # plt.imshow(mask_file.variables["binary_mask"][ :, :])

## binary mask by overwritting current landseamask variable 
landseamask["binary_mask"] = landseamask["mask"]
landseamask['binary_mask'][:] = mask
landseamask = landseamask.drop(['tas'])
print(landseamask.variables["binary_mask"][0, :, :]) #t = t.to_array()

plt.imshow(landseamask.variables["binary_mask"][0, :, :])

landseamask.to_netcdf(b_mask_file)
landseamask.close()



######################

# #  mask  parameter.nc file with the binary mask file by multiplying them simply.
# inf_param = s.output_dir + "/" + "tas_parameters_16.nc4"
# mask = s.input_dir + "/" + s.dataset + "/b_mask_for_interpolation_16.nc"
# cmd = f"cdo -mul {mask} {inf_param} {s.output_dir}/tas_trace_shape16_masked.nc4"
# print(cmd)
# subprocess.check_call(cmd, shell=True)

