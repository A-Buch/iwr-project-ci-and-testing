import os
import glob
import numpy as np
import netCDF4 as nc
import xarray as xr
from datetime import datetime
from pathlib import Path
import itertools as it
import pickle
import pandas as pd
from func_timeout import func_timeout, FunctionTimedOut
import attrici
import attrici.estimator as est
import attrici.datahandler as dh
import attrici.postprocess as pp
import attrici.interpolate_parameters as ip
import settings as s
from pymc3.parallel_sampling import ParallelSamplingError
import logging
import threading


s.output_dir.mkdir(parents=True,exist_ok=True)
logging.basicConfig(
    filename=s.output_dir / "failing_cells.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
# needed to silence verbose pymc3
pmlogger = logging.getLogger("pymc3")
pmlogger.propagate = False

print("Version", attrici.__version__)

try:
    submitted = os.environ["SUBMITTED"] == "1"
    task_id = int(os.environ["SLURM_ARRAY_TASK_ID"])
    njobarray = int(os.environ["SLURM_ARRAY_TASK_COUNT"])
    s.ncores_per_job = 1
    s.progressbar = False
except KeyError:
    submitted = False
    njobarray = 1
    task_id = 0
    s.progressbar = True

print("submitted:", submitted)

dh.create_output_dirs(s.output_dir)

gmt_file = s.input_dir / s.dataset / s.testarea / s.gmt_file
ncg = nc.Dataset(gmt_file, "r")
gmt = np.squeeze(ncg.variables["tas"][:])
ncg.close()

input_file = s.input_dir / s.dataset / s.testarea / s.source_file.lower()
landsea_mask_file = s.input_dir /  s.dataset / s.testarea / s.landsea_file

obs_data = nc.Dataset(input_file, "r")
nc_lsmask = nc.Dataset(landsea_mask_file, "r")
nct = obs_data.variables["time"]
lats = obs_data.variables["lat"][:]
lons = obs_data.variables["lon"][:]
longrid, latgrid = np.meshgrid(lons, lats)
jgrid, igrid = np.meshgrid(np.arange(len(lons)), np.arange(len(lats)))

ls_mask = nc_lsmask.variables["mask"][0, :, :] #["area_European_01min"][:,:] 
ls_mask[np.isnan(ls_mask)] = 1.0   # removing sea area from landseamask
print("removing sea area from landseamask")

df_specs = pd.DataFrame()
df_specs["lat"] = latgrid[ls_mask == 1]
df_specs["lon"] = longrid[ls_mask == 1]
df_specs["index_lat"] = igrid[ls_mask == 1]
df_specs["index_lon"] = jgrid[ls_mask == 1]

print("A total of", len(df_specs), "grid cells to estimate.")

if len(df_specs) % (njobarray) == 0:
    print("Grid cells can be equally distributed to Slurm tasks")
    calls_per_arrayjob = np.ones(njobarray) * len(df_specs) // (njobarray)
else:
    print("Slurm tasks not a divisor of number of grid cells, discard some cores.")
    calls_per_arrayjob = np.ones(njobarray) * len(df_specs) // (njobarray) + 1
    discarded_jobs = np.where(np.cumsum(calls_per_arrayjob) > len(df_specs))
    calls_per_arrayjob[discarded_jobs] = 0
    calls_per_arrayjob[discarded_jobs[0][0]] = len(df_specs) - calls_per_arrayjob.sum()

assert calls_per_arrayjob.sum() == len(df_specs)

# Calculate the starting and ending values for this task based
# on the SLURM task and the number of runs per task.
cum_calls_per_arrayjob = calls_per_arrayjob.cumsum(dtype=int)
start_num = 0 if task_id == 0 else cum_calls_per_arrayjob[task_id-1]
end_num = cum_calls_per_arrayjob[task_id] - 1
run_numbers = np.arange(start_num, end_num + 1, 1, dtype=np.int)
if len(run_numbers) == 0:
    print ("No runs assigned for this SLURM task.")
else:
    print("This is SLURM task", task_id, "which will do runs", start_num, "to", end_num)

estimator = est.estimator(s)

TIME0 = datetime.now()

## create file to store parameters if not exists, otherwise interpolate existing file
trace_filepath = s.output_dir / s.trace_file

if os.path.exists(trace_filepath):
    trace_file_loading = True
    print(f"Using {s.trace_file} for interpolation")
    parameter_f = ip.interpolation_parameters(trace_filepath, landsea_mask_file)
else:
    trace_file_loading = False
    out = nc.Dataset(trace_filepath, "w", format="NETCDF4") 
    pp.form_global_nc(out, nct[:8], lats, lons, None, nct.units)
    out.close()
    parameter_f = nc.Dataset(trace_filepath, "a", format="NETCDF4")



for n in run_numbers[:]:
    sp = df_specs.loc[n, :]

    # if lat >20: continue
    print(
        "This is SLURM task", task_id, "run number", n, "lat,lon", sp["lat"], sp["lon"]
    )
    # outdir_for_cell = dh.make_cell_output_dir(
        # s.output_dir, "timeseries", sp["lat"], sp["lon"], s.variable
    # )
    # fname_cell = dh.get_cell_filename(outdir_for_cell, sp["lat"], sp["lon"], s)

    outdir_for_cell_interp = dh.make_cell_output_dir(
        s.output_dir, "timeseries_interpolated", sp["lat"], sp["lon"], s.variable
    )
    fname_cell_interp = dh.get_cell_filename(outdir_for_cell_interp, sp["lat"], sp["lon"], s)

    if s.skip_if_data_exists:
        try:
            dh.test_if_data_valid_exists(fname_cell_interp)
            print(f"Existing valid data in {fname_cell_interp} . Skip calculation.")
            continue
        except Exception as e:
            print(e)
            print("No valid data found. Run calculation.")

    data = obs_data.variables[s.variable][:, sp["index_lat"], sp["index_lon"]]
    df, datamin, scale = dh.create_dataframe(nct[:], nct.units, data, gmt, s.variable)

    ## load if free_paramss.nc contains parameter values , otherwise create new free_params
    if trace_file_loading: 
        print(f"Loading interpolated parameters for position {sp.index_lat, sp.index_lon} from {s.trace_file}")
        dff, free_params = func_timeout(
            s.timeout, estimator.load_parameters, args=(parameter_f, df, sp["index_lat"], sp["index_lon"], s.map_estimate)
        )
        print("Using reloaded and interpolated parameters for ts creation")

        ## TODO current workaround: make nicer codeblock for handling of sea area (empty cells)
        t = parameter_f.logp[:, int(sp["index_lat"]), int(sp["index_lon"])]
        t = t[ ~np.isnan(t)]
        print("t",t)
        if bool(t.any())==False:
            print("empty cell, skipping to next cell", int(sp["index_lat"]), int(sp["index_lon"]))
            continue  # skip to next cell
        else:
            ## make timeseries
            df_with_cfact = estimator.estimate_timeseries(dff, free_params, datamin, scale, s.map_estimate)
            dh.save_to_disk(df_with_cfact, fname_cell_interp, sp["lat"], sp["lon"], s.storage_format) 

    else:
        print(f"No parameters exists for position {sp.index_lat, sp.index_lon}, creating new ones and writing them to {s.trace_file}")
        try:
            # TODO replace "8" with max lenght of parameter values
            dff, free_params = func_timeout(
                s.timeout, estimator.estimate_parameters, args=(nct[:8], parameter_f, df, sp["lat"], sp["lon"], sp["index_lat"], sp["index_lon"], s.map_estimate)
            )

        except (FunctionTimedOut, ParallelSamplingError, ValueError) as error:
            if str(error) == "Modes larger 1 are not allowed for the censored model.":
                raise error
            else:
                print("Sampling at", sp["lat"], sp["lon"], " timed out or failed.")
                print(error)
                logger.error(
                    str(
                        "lat,lon: "
                        + str(sp["lat"])
                        + " "
                        + str(sp["lon"])
                        + str(error)
                    )
                )
            continue


# ## interpolate newly created parameters and make timeseries
if trace_file_loading == False:
    parameter_f = ip.interpolation_parameters(trace_filepath, landsea_mask_file)
    print(f"Interpolating parameters from {trace_filepath}")
    #print(f"Storing them in {interpolated_parameters}")


    ## TODO find better way to implement code in previous loop or in a new script
    for n in run_numbers[:]:
        sp = df_specs.loc[n, :]
        outdir_for_cell_interp = dh.make_cell_output_dir(
            s.output_dir, "timeseries_interpolated", sp["lat"], sp["lon"], s.variable
            )
        fname_cell_interp = dh.get_cell_filename(outdir_for_cell_interp, sp["lat"], sp["lon"], s)

        data = obs_data.variables[s.variable][:, sp["index_lat"], sp["index_lon"]]
        df, datamin, scale = dh.create_dataframe(nct[:], nct.units, data, gmt, s.variable)
        ## load parameters file
        print("Using interpolated parameters for ts creation")
        #print(f"Loading interpolated parameters for position {sp.index_lat, sp.index_lon}")
        dff, free_params = func_timeout(
            s.timeout, estimator.load_parameters, args=(parameter_f, df, sp["index_lat"], sp["index_lon"], s.map_estimate)
        )

        ## TODO current workaround: make nicer codeblock for handling of sea area (empty cells)
        t = parameter_f.logp[:, int(sp["index_lat"]), int(sp["index_lon"])]
        t = t[ ~np.isnan(t)]
        print("t",t)
        if bool(t.any())==False:
            print("empty cell, skipping to next cell", int(sp["index_lat"]), int(sp["index_lon"]))
            continue  # skip to next cell
        else:
            ## make timeseries
            df_with_cfact = estimator.estimate_timeseries(dff, free_params, datamin, scale, s.map_estimate)
            dh.save_to_disk(df_with_cfact, fname_cell_interp, sp["lat"], sp["lon"], s.storage_format) 

## already interpolated parameters and ts created
else:
    pass


parameter_f.close()
obs_data.close()
nc_lsmask.close()

print(
    "Estimation completed for all cells. It took {0:.1f} minutes.".format(
        (datetime.now() - TIME0).total_seconds() / 60
    )
)
