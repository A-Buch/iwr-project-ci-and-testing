#!/usr/bin/env python3

# coding: utf-8

import glob
import itertools as it
from pathlib import Path
import netCDF4 as nc
import numpy as np
import pandas as pd
from datetime import datetime
import subprocess
import attrici.postprocess as pp
import settings as s

# options for postprocess
rechunk = False
# cdo_processing needs rechunk
cdo_processing = False

TIME0 = datetime.now()

ts_dir = s.output_dir / "timeseries" / s.variable
cfact_dir = s.output_dir / "cfact" / s.variable

data_gen = ts_dir.glob("**/*" + s.storage_format)
cfact_dir.mkdir(parents=True, exist_ok=True)
cfact_file = cfact_dir / s.cfact_file


### access data from source file
obs = nc.Dataset(Path(s.input_dir) / s.dataset / s.testarea / s.source_file.lower(), "r")
time = obs.variables["time"][:]
lat = obs.variables["lat"][:]
lon = obs.variables["lon"][:]


### check which data is available
data_list = []
lat_indices = []
lon_indices = []

for i in data_gen:
    data_list.append(str(i))
    lat_float = float(str(i).split("lat")[-1].split("_")[0])
    lon_float = float(str(i).split("lon")[-1].split(s.storage_format)[0])
    # lat_indices.append(int(180 - 2 * lat_float - 0.5))
    # lon_indices.append(int(2 * lon_float - 0.5 + 360))
    
    ## regional AOI (rescaling needed)   
    ## TODO: make this more robust, so that also a regional AOI with nth pixel cells (e.g. s.lateral_sub = 40) is usable
    if s.lateral_sub == 1 :
        lat_indices.append( pp.rescale_squared_aoi(lat, lat_float ))
        lon_indices.append( pp.rescale_squared_aoi(lon, lon_float ))

    # global AOI, optional with sparse values on every nth pixel cell (no rescaling needed)
    else:  
        lat_indices.append(int(180 - 2 * lat_float - 0.5))
        lon_indices.append(int(2 * lon_float - 0.5 + 360))

    
print(len(lat_indices), len(lon_indices) )  # shape 51 x 51 (org sub40))
print(len(np.unique(lat_indices)), len(np.unique(lon_indices)) )  # 7 x 16 (org sub40)
print(np.unique(lat_indices))
print(np.unique(lon_indices))  

## TODO fix rescale_squared_aoi() for lon:indes:
lon_indices = []
for i in lon:
    idx = lon.index(i)
    lon_indices.append(idx)
print("Updated list:", lon_indices) 


if s.lateral_sub == 1 :
    lat_indices = lat_indices[: : -1]  # reverse indieces to undone flip of spatial extent


# adjust indices if datasets are subsets (lat/lon-shapes are smaller than 360/720)
# TODO: make this more robust
lat_indices = np.array(lat_indices) / s.lateral_sub
lon_indices = np.array(lon_indices) / s.lateral_sub


# append later with more variables if needed
variables_to_report = {s.variable: "cfact", s.variable + "_orig": "y"}

#  get headers and form empty netCDF file with all meatdata
headers = pp.read_from_disk(data_list[0]).keys()
print("headers from ts", headers)
#headers = headers.drop(["t", "ds", "gmt", "gmt_scaled"])  # org
headers = headers.drop(['ds', 'y', 'logp'])
#headers = headers.drop(["ds"])
out = nc.Dataset(cfact_file, "w", format="NETCDF4")
pp.form_global_nc(out, time, lat, lon, headers, obs.variables["time"].units)
print("out.variables", out.variables.keys())
#print("lat_indices", lat_indices, lon_indices)

for (i, j, dfpath) in it.zip_longest(lat_indices, lon_indices, data_list):
    df = pp.read_from_disk(dfpath)
    for head in headers:
        print("head, i ,j ", head, i , j)
        if head in out.variables.keys():
            pass
        else:
            print(f"create new variable {head} in {cfact_file}") 
            #data = out.createVariable(head, "f4", chunksizes=(time.shape[0], 1, 1), fill_value=1e20) 
            data = out.createVariable(head, "f4", ("time", "lat", "lon"), chunksizes=(time.shape[0], 1, 1), fill_value=1e20) 
        ts = df[head]
        out.variables[head][:, int(i), int(j)] = np.array(ts)
    print("wrote data from", dfpath, "to", i, j)
out.close()

print("Successfully wrote", cfact_file, "file. Took")
print("It took {0:.1f} minutes.".format((datetime.now() - TIME0).total_seconds() / 60))


if rechunk:
    cfact_rechunked = pp.rechunk_netcdf(cfact_file)

if cdo_processing:
    cdo_ops = {
        "monmean": "monmean -selvar,cfact,y",
        "yearmean": "yearmean -selvar,cfact,y",
        #    "monmean_valid": "monmean -setrtomiss,-1e20,1.1574e-06 -selvar,cfact,y",
        #    "yearmean_valid": "yearmean -setrtomiss,-1e20,1.1574e-06 -selvar,cfact,y",
        "trend": "trend -selvar,cfact,y",
        #    "trend_valid": "trend -setrtomiss,-1e20,1.1574e-06 -selvar,cfact,y",
    }

    for cdo_op in cdo_ops:

        outfile = str(cfact_file).rstrip(".nc4") + "_" + cdo_op + ".nc4"
        print(outfile)
        if "trend" in cdo_op:
            outfile = (
                outfile.rstrip(".nc4") + "_1.nc4 " + outfile.rstrip(".nc4") + "_2.nc4"
            )
        try:
            cmd = "cdo " + cdo_ops[cdo_op] + " " + cfact_rechunked + " " + outfile
            print(cmd)
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError:
            cmd = "module load cdo && " + cmd
            print(cmd)
            subprocess.check_call(cmd, shell=True)
