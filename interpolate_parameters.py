"""Functions to merge single parameter files into a global netcdf file,
reduce the number of parameters and interpolate missing parameters"""
import pickle
import re
import subprocess
from pathlib import Path

import numpy as np
import xarray as xr
from scipy.ndimage import minimum_filter

import settings as s


def get_float_from_string(file_name):
    """Returns a float if there is exactly one float in the string.
    Otherwise it throws a ValueError"""
    floats_in_string = re.findall(r"[-+]?(?:\d*\.*\d+)", file_name)
    if len(floats_in_string) != 1:
        raise ValueError("there is no ore more than one float in this string")
    return float(floats_in_string[0])


def merge_parameters(trace_dir, parameter_filepath):
    """Merge all files in trace_dir into a single netCDF4 file
    which is stored in parameter_filepath"""
    parameter_files = []
    for trace_file in trace_dir.glob("**/lon*"):
        print("trace_file", trace_file)
        lat = get_float_from_string(trace_file.parent.name)
        lon = get_float_from_string(trace_file.name)
        data_vars = []
        with open(trace_file, "rb") as trace:
            free_params = pickle.load(trace)
        for key in free_params.keys():
            try:
                dim_param = np.arange(len(free_params[key]))
            except TypeError as error:
                if str(error) == "len() of unsized object":
                    dim_param = np.arange(1)
                else:
                    raise error

            data_vars.append(
                xr.DataArray(
                    dims=["d", "lat", "lon"],
                    data=free_params[key].reshape((-1, 1, 1)),
                    coords={
                        "d": ("d", dim_param),
                        "lat": ("lat", [lat]),
                        "lon": ("lon", [lon]),
                    },
                    name=key,
                )
            )
        parameter_files.append(xr.merge(data_vars))

    merged_parameters = xr.merge(parameter_files)
    merged_parameters = merged_parameters.reindex(lat=merged_parameters.lat[::-1])  # curr. workaround: correction of upside-down
    merged_parameters.to_netcdf(parameter_filepath, format="NETCDF4")
    return merge_parameters


def reduce_parameters(parameter_file, bmask, parameter_filepath_m, support_filepath, support_gridded_filepath):
    """
    Use a (binary) mask file to reduce the number of parameters. This function is only for testing.
    In production we want to only compute parameters for the support cells
    (defined in the mask file)
    and interpolate the parameters in between using interpolate_parameters().
    This function should be used if the effects of interpolation are evaluated
    against computing parameters for all files
    """
    parameter_file_m = parameter_file * bmask.binary_mask[0, :, :]

    coastmask = parameter_file.notnull()
    coastmask = minimum_filter(
        coastmask.weights_fc_trend, size=(0, 3, 3), mode="nearest"
    )
    coastlines = parameter_file.where(~coastmask)  # extract coast lines
    parameter_file_m = parameter_file_m.merge(
        coastlines, join="outer", compat="no_conflicts"
    )  ###  every 3rd cell + cells from coastline are support cells

    parameter_file_m.to_netcdf(parameter_filepath_m, format="NETCDF4")
    parameter_file_m.close()

    ##  let cdo recognize nan values in masked parameters file
    print("set masked values of parameter file as nan")
    cmd = (
        "cdo setmissval,nan " + str(parameter_filepath_m) + " " + str(support_filepath)
    )

    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        cmd = "module load cdo && " + cmd
        print(cmd)
        subprocess.check_call(cmd, shell=True)


    ## convert to lonlat grid, needed for interpolation step
    print("convert grid of support file to lonlat, which is needed for interpolation step")
    cmd = (
        "cdo griddes " + str(support_filepath) +  " > params_grid "
            + '&& sed -i "s/generic/lonlat/g" params_grid '
            + "&& cdo setgrid,params_grid " + str(support_filepath) + " " + str(support_gridded_filepath)
    )
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        cmd = "module load cdo && " + cmd
        print(cmd)
        subprocess.check_call(cmd, shell=True)
 


def interpolate_parameters(support_gridded_filepath, interpolated_parameter_filepath):
    """interpolate missing values in paramters file"""
    print("interpolating..")
    ## [setmisstodis, neighbors]: distance-weighted average of the nearest non missing values
    cmd = (
        "cdo -setmisstodis,4 "
        + str(support_gridded_filepath)
        + " "
        + str(interpolated_parameter_filepath)
    )

    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        cmd = "module load cdo && " + cmd
        print(cmd)
        subprocess.check_call(cmd, shell=True)

    ## extract land area from interpolated file
    interpolated_parameters = xr.load_dataset(interpolated_parameter_filepath)
    lsmask_filepath = s.input_dir / s.dataset / s.testarea / s.landsea_file
    lsmask = xr.load_dataset(lsmask_filepath)
    
    lsmask = lsmask.assign_coords(lat=interpolated_parameters.lat,lon=interpolated_parameters.lon) # curr. workaround: align dims of both files for interpolation
    interpolated_parameters = interpolated_parameters * lsmask["mask"][0,:,:]
    interpolated_parameters.to_netcdf(interpolated_parameter_filepath, format="NETCDF4", mode='w')

    print(
        f"Generated interpolated parameters, stored in {interpolated_parameter_filepath}"
    )


def main():
    """All steps from single parameter files for each grid cell to a interpolated parameter file"""
    parameter_file = merge_parameters(
        trace_dir=s.output_dir / "traces" / s.variable,
        parameter_filepath=s.output_dir / s.trace_file,
    )

    ## load binary mask
    bmask_filepath = s.input_dir / s.dataset / s.testarea / s.bmask_file
    bmask = xr.load_dataset(bmask_filepath)
    print("binary mask:\n", bmask)

    parameter_filepath_m = Path.joinpath(s.output_dir, Path(s.trace_file).stem + "_m.nc4")
    support_filepath = Path.joinpath(
        s.output_dir, Path(parameter_filepath_m).stem + "_nan.nc4"
    )
    support_gridded_filepath = Path.joinpath(
        s.output_dir, Path(support_filepath).stem + "_g.nc4"
    )
    parameter_filepath = s.output_dir / s.trace_file
    parameter_file = xr.load_dataset(parameter_filepath)

    reduce_parameters(parameter_file, bmask, parameter_filepath_m, support_filepath, support_gridded_filepath)

    interpolate_parameters(
        support_gridded_filepath, 
        interpolated_parameter_filepath=s.output_dir/s.interpolated_trace_file
     )


if __name__ == "__main__":
    main()
