# #### AIM: 
# Create binary mask and land(sea)mask, which is later used to select every nth cell from parameter file

import os, sys
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
import subprocess
import settings as s



def create_landseamask(input_filepath, landseamask_filepath, variable=s.variable):
    """
    Create land(sea) mask from source file, in nc format

    param facutal_filepath (str): path to meteorological nc or nc4 file
    param landseamask_filepath (str): path to land(sea)-mask, nc or nc4 file
    """

    # assigne every value except nan to land area, assigne all nan as sea area
    cmd = f"cdo -setmissval,nan -seltimestep,1 -setrtoc,-1000,1000,1 -chname,{variable},mask {input_filepath} {landseamask_filepath}"
    cmd_2 = f"ncwa -a time -O {landseamask_filepath} {landseamask_filepath}" # make as a 2-dimensional mask
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        print(cmd_2)
        subprocess.check_call(cmd_2, shell=True)
    except subprocess.CalledProcessError:
        cmd = "module load cdo && " + cmd
        print(cmd)
        subprocess.check_call(cmd, shell=True)
        cmd_2 = "module load nco && " + cmd_2
        print(cmd_2)
        subprocess.check_call(cmd_2, shell=True)


def create_binarymask(landseamask_filepath, bmask_filepath, subset_length=s.file_len, nth_support_cell=3):
    """
    Create squared binary mask as nc file to clip parameters, keep every nth cell as support cell
    subset_length = (x * nth_support_cell) + 1

    param bmask_filepath (str): filepath where the binary mask should be stored
    param subset_length (int): vertical and horizontal extent of the subset, support cells should exist in each corner of the subset
    param nth_support_cell(int): keep every nth cell as support cell, shape as (x*3)+1
    """
    ## generate binary mask of nth * nth cells
    x = np.arange(0, s.file_len)
    bmask = np.full(len(x) * s.file_len, np.nan).reshape(s.file_len, s.file_len)  # squared mask
    bmask[::nth_support_cell , ::nth_support_cell] = np.int64(1)  # keep every third cell as support cell
    print("binary mask:", bmask)

    ## write out binary mask by using landseamask file as template
    template = xr.open_dataset(landseamask_filepath)
    template["binary_mask"] = template["mask"]
    template['binary_mask'][:] = bmask
    template = template.drop(['mask'])
    print("Generated binary mask: ", template.variables["binary_mask"][ :, :])

    template.to_netcdf(bmask_filepath)
    template.close()



def main():

    create_landseamask(
        input_filepath = s.input_dir / s.dataset / s.testarea / s.source_file, 
        landseamask_filepath = s.input_dir / s.dataset / s.testarea / s.landsea_file
    )

    create_binarymask(
        landseamask_filepath = s.input_dir / s.dataset / s.testarea / s.landsea_file, 
        bmask_filepath = s.input_dir / s.dataset / s.testarea / s.bmask_file
    )


if __name__ == "__main__":
    main()


