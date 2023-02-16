# #### AIM: 
# Create binary mask, which is later used to select every third cell from param.nc
# - Binary values:  nan and 1
# - mask.shape: (n*3)+1


import numpy as np
import netCDF4 as nc
import xarray as xr
import matplotlib.pylab as plt
import subprocess
import settings as s

plt.rcParams["font.size"] = 10
plt.rcParams["figure.figsize"] = 12,8



## generate binary mask of 19*19 cells
x = np.arange(0,19)
mask = np.full(len(x)*19, np.nan).reshape(19,19)
mask[::3 , ::3] = np.int64(1)
type(mask[0])
mask


## crop existing landseamask file to 19x19 cells

inf = s.input_dir + "/landmask_for_testing.nc"
outf = s.input_dir + "/landmask_for_testing_19.nc"

cmd = f"cdo -f nc4c -z zip selindexbox,0,19,0,19  {inf} {outf}"
print(cmd)
subprocess.check_call(cmd, shell=True)

## open cropped landseamask file to overwrite its variable
mask_file = s.input_dir + "/" + s.dataset + '/landmask_for_testing_19.nc'
out = s.input_dir + "/" + s.dataset + '/b_mask.nc'

mask_file = xr.open_dataset(mask_file)
print(mask_file.variables)#"].shape

# plt.imshow(mask_file.variables["binary_mask"][ :, :])

## overwrite current landseamask variable 
mask_file['area_European_01min'][:] = mask
mask_file.variables["area_European_01min"] #t = t.to_array()

mask_file["binary_mask"] = mask_file["area_European_01min"]
mask_file = mask_file.drop(['area_European_01min'])
mask_file.variables["binary_mask"][:, :]


plt.imshow(mask_file.variables["binary_mask"][ :, :])


mask_file.to_netcdf(out)
out.close()

