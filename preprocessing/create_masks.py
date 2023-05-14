# #### AIM: 
# Create binary mask, which is later used to select every third cell from param.nc
# - Binary values:  nan and 1
# - mask.shape: (n*3)+1

import os, sys
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
import subprocess
#sys.path.append("../")

import settings as s


## TODO fix module imports from parent dir

remove_intermediate_files = True


#input_dir = "/p/tmp/annabu/attrici_interpolation/meteo_data"
#output_dir = "/p/tmp/annabu/attrici_interpolation/output_corr"
dataset = "ERA5"
testarea = "testarea_31"

# create landseamask file from meteo file by overwriting its variables
landseamask = str(s.input_dir) + "/" + s.dataset +  "/" + s.testarea + f'/landseamask_{s.file_len}_smv.nc'
meteo_clipped = s.input_dir / s.dataset / s.testarea / s.source_file

## assigne first all nan as missing value for CDO, so that they will remain sea in subsequent step
## converting Normal value to NaN value so that cdo interprets them as missing values during interpolation
cmd = f"cdo -setmissval,nan -seltimestep,1 -setrtoc,-1000,1000,1 -chname,{s.variable},mask {meteo_clipped} {landseamask}"  # set all values to 1 (except nan) and take 1 layer
try:
    print(cmd)
    subprocess.check_call(cmd, shell=True)
except subprocess.CalledProcessError:
    cmd = "module load cdo && " + cmd
    print(cmd)
    subprocess.check_call(cmd, shell=True)

## test if sea is NaN in outfile
# cmd = f"cdo -setctomiss,0 -seltimestep,1 -setrtoc,-1000,1000,1 -chname,{s.variable},mask {meteo_clipped} {landseamask_2}"  # set all values to 1 (except nan) and take 1 layer
# cmd = f"cdo seltimestep,1 setrtoc,-1000,1000,1 {inf} {outf}"  # set all values to 1 (except nan) and take 1 layer
# try:
    # print(cmd)
    # subprocess.check_call(cmd, shell=True)
# except subprocess.CalledProcessError:
    # cmd = "module load cdo && " + cmd
    # print(cmd)
    # subprocess.check_call(cmd, shell=True)


## generate binary mask of nth * nth cells
x = np.arange(0,s.file_len)
bmask = np.full(len(x)*s.file_len, np.nan).reshape(s.file_len, s.file_len)
bmask[::3 , ::3] = np.int64(1)
print("binary mask:", bmask)

## write out binary mask by using landseamask file as template
# b_mask_interim = input_dir + "/" + dataset + "/" + testarea  + f'/b_mask.nc'
b_mask_file = str(s.input_dir) + "/" + s.dataset + "/" + testarea  + f'/b_mask_{s.file_len}.nc'


## binary mask by overwritting current landseamask variable 
template = xr.open_dataset(landseamask)
template["binary_mask"] = template["mask"]
template['binary_mask'][:] = bmask
template = template.drop(['mask'])
print(template.variables["binary_mask"][0, :, :]) #t = t.to_array()

#plt.imshow(template.variables["binary_mask"][0, :, :])

template.to_netcdf(b_mask_file)#(b_mask_interim)
template.close()

## TODO: check if not needed, due that sea area is interpolated anyway and needs to be clipped later
## set sea area as missing value in binary mask 
#cmd = f"cdo -mul {landseamask_file} {b_mask_interim} {b_mask_file}"
#try:
#    print(cmd)
#    subprocess.check_call(cmd, shell=True)
#except subprocess.CalledProcessError:
#    cmd = "module load cdo && " + cmd
#    print(cmd)
#    subprocess.check_call(cmd, shell=True)


# if remove_intermediate_files == True:
    # print(f"Removing: {b_mask_interim}")
    # os.remove(b_mask_interim)

