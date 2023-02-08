import shutil
import numpy as np
import pandas as pd
import subprocess
from datetime import datetime
import netCDF4 as nc
import math

def read_from_disk(data_path):

    if data_path.split(".")[-1] == "h5":
        df = pd.read_hdf(data_path)
    elif data_path.split(".")[-1] == "csv":
        df = pd.read_csv(data_path, index_col=0)
    else:
        raise NotImplementedError("choose storage format .h5 or csv.")

    return df


def form_global_nc(ds, time, lat, lon, vnames, torigin):

    # FIXME: can be deleted once merge_cfact is fully replaced by write_netcdf

    ds.createDimension("time", None)
    ds.createDimension("lat", lat.shape[0])
    ds.createDimension("lon", lon.shape[0])

    times = ds.createVariable("time", "f8", ("time",))
    longitudes = ds.createVariable("lon", "f8", ("lon",))
    latitudes = ds.createVariable("lat", "f8", ("lat",))
    for var in vnames:
        data = ds.createVariable(
            var,
            "f4",
            ("time", "lat", "lon"),
            chunksizes=(time.shape[0], 1, 1),
            fill_value=1e20,
        )
    times.units = torigin
    latitudes.units = "degree_north"
    latitudes.long_name = "latitude"
    latitudes.standard_name = "latitude"
    longitudes.units = "degree_east"
    longitudes.long_name = "longitude"
    longitudes.standard_name = "longitude"
    # FIXME: make flexible or implement loading from source data
    latitudes[:] = lat
    longitudes[:] = lon
    times[:] = time

def rechunk_netcdf(ncfile, ncfile_rechunked):


    TIME0 = datetime.now()

    try:
        cmd = (
            "ncks -4 -O --deflate 5 "
            + "--cnk_plc=g3d --cnk_dmn=lat,360 --cnk_dmn=lon,720 "
            + str(ncfile)
            + " "
            + ncfile_rechunked
        )
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        cmd = "module load nco & module load intel/2018.1 && " + cmd
        print(cmd)
        subprocess.check_call(cmd, shell=True)

    print("Rechunking took {0:.1f} minutes.".format((datetime.now() - TIME0).total_seconds() / 60))

    return ncfile_rechunked


def replace_nan_inf_with_orig(variable, source_file, ncfile_rechunked):

    ncfile_valid = ncfile_rechunked.rstrip(".nc4") + "_valid.nc4"
    shutil.copy(ncfile_rechunked, ncfile_valid)

    print(f"Replace invalid values in {ncfile_rechunked} with original values from {source_file}")

    ncs = nc.Dataset(source_file, "r")
    ncf = nc.Dataset(ncfile_valid, "a")

    var_orig = ncs.variables[variable]
    var = ncf.variables[variable]

    chunklen = 1000
    for ti in range(0,var.shape[0],chunklen):
        v = var[ti:ti+chunklen,:,:]
        v_orig = var_orig[ti:ti+chunklen,:,:]
        logp = ncf['logp'][ti:ti+chunklen, :, :]
        # This threshold for logp is to ensure that the model fits the data at all. It is mainly to catch values
        # for logp like -7000
        small_logp = logp < -300
        isinf = np.isinf(v)
        isnan = np.isnan(v)
        print(f"{ti}: replace {isinf.sum()} inf values, {isnan.sum()} nan values and {small_logp.sum()} values with too small logp (<-300).")

        v[isinf | isnan | small_logp] = v_orig[isinf | isnan | small_logp]
        var[ti:ti+v.shape[0],:,:] = v

    ncs.close()
    ncf.close()
    return ncfile_valid


def round_float_down(num, step=0):
    '''
    Takes a float and rounds it always down to user-defined decimal place
    params: num : foat number
    params: step : decimal place
    return: float
    Copyied from : https://stackoverflow.com/questions/9404967/taking-the-floor-of-a-float
    '''
    if not step:
        return math.floor(num)
    if step < 0:
        mplr = 10 ** (step * -1)
        return math.floor(num / mplr) * mplr
    ncnt = step
    if 1 > step > 0:
        ndec, ncnt = .0101, 1
        while ndec > step:
            ndec *= .1
            ncnt += 1
    mplr = 10 ** ncnt
    return round(math.floor(num * mplr) / mplr, ncnt)


def rescale_squared_aoi(coord_list, coord_float):
    '''
    Rescales squared aoi, returns rescaled indices latitude or longitude
    params:  
        coord_list: list of lat or lon coordinates of the aoi
        coord_float: float, latitude or longitude derived from timeseries filename
    return: float
    '''
    
    ## get correct amount of indices by rounding down always the minimum extent and round up the maximum extent
    coord_min = round_float_down(min(coord_list), 2) 
    coord_max = math.ceil(max(coord_list)*100) / 100 

    ## Formular: (new_max - new_min) / (old_max - old_min) * (v - old_min) + new_min
    coord_indice = int( (coord_list.shape[0] - 0) / ( coord_max - coord_min) * (coord_float - coord_min) + 0 )

    return coord_indice


