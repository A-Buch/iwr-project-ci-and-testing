import os
import getpass
from pathlib import Path
import logging
import functools

# user = getpass.getuser()
# user = "root"  # TODO run GithubActions by setting username e.g. "root"

# this will hopefully avoid hand editing paths everytime.
# fill further for convenience.
# if user == "annabu":
#     data_dir = "/p/projects/ou/rd3/dmcci/basd_era5-land_to_efas-meteo/"
#     log_dir = "./log"
#     output_dir = Path("/p/tmp/annabu/projects/attrici/output")

# elif user == "root":
#     data_dir = "/mnt/c/Users/Anna/Documents/UNI/HiWi/IWRcourses_PY_ML_meetings/effective_software_testing/iwr-project-ci-and-testing/demo_input"
#     log_dir = "./log"
#     output_dir = Path("/mnt/c/Users/Anna/Documents/UNI/HiWi/IWRcourses_PY_ML_meetings/effective_software_testing/iwr-project-ci-and-testing/demo_output") # noqa: E501

## to have a reproducable example load test input data
data_dir = "./tests/test_data/demo_input"
log_dir = "./log"
output_dir = Path("./tests/test_data/demo_output") # noqa: E501

# # for example "GSWP3", "GSWP3-W5E5"
dataset = "ERA5"

# select variable to detrend
variable = "tas"
tile = "00003"
hour = "18"


input_dir = Path(data_dir) / dataset / tile
# folder for testing tile 9 and 10: "attrici_input" / dataset
output_dir = output_dir / tile # / Path.cwd().name  ## make output dir same as cwd. Helps if running more than one job.    
#log_dir = log_dir + "/" + tile

# max time in sec for sampler for a single grid cell.
timeout = 60 * 60
# tas, tasrange pr, prsn, prsnratio, ps, rlds, wind, hurs

# number of modes for fourier series of model
# TODO: change to one number only, as only the first element of list is used.
modes = [4, 4, 4, 4]
# NUTS or ADVI
# Compute maximum approximate posterior # todo is this equivalent to maximum likelihood?
map_estimate = True
# bayesian inference will only be called if map_estimate=False
inference = "NUTS"

seed = 0  # for deterministic randomisation
subset = 1  # only use every subset datapoint for bayes estimation for speedup
startdate = None  # may at a date in the format '1950-01-01' to train only on date from after that date

# use a dataset with only subset spatial grid points for testing
lateral_sub = 1

gmt_file = dataset.lower() + "_ssa_gmt.nc4"
landsea_file = f"landmask_{tile}_demo.nc"
# source_file = variable + "_" + dataset + "_sub.nc4"
source_file = (
    f"rechunked_{dataset}_{variable}{hour}_{dataset}_1950_2020_t_{tile}_basd_redim_demo.nc4"
)
cfact_file = f"{source_file.split('.')[0]}_cfact_demo.nc"
# .h5 or .csv
storage_format = ".h5"

# "all" or list like ["y","y_scaled","mu","sigma"]
# for productions runs, use ["cfact"]
# report_variables = "all"
report_variables = ["ds", "y", "cfact", "logp"]
# reporting to netcdf can include all report variables
# "cfact" is translated to variable, and "y" to variable_orig
report_to_netcdf = [variable, variable + "_orig", "logp"]

# if map_estimate used, save_trace only writes small data amounts, so advised to have True.
save_trace = True
skip_if_data_exists = True

# model run settings
tune = 500  # number of draws to tune model
draws = 1000  # number of sampling draws per chain
chains = 2  # number of chains to calculate (min 2 to check for convergence)

# number of cores to use for one gridpoint
# submitted jobs will have ncores_per_job=1 always.
ncores_per_job = 2
progressbar = True  # print progress in output (.err file for mpi)

#### settings for create_submit.py
# number of parallel jobs through jobarray
# needs to be divisor of number of grid cells
njobarray = 64



## test: decorator for logger
def decorate_init_logger(func):
    """
    Decorator for logger
    """
    @functools.wraps(func)  # preserve original func information from magic methods such as __repr__
    def wrapper(*args):

        # Call the wrapped function
        logger = func(*args)

        # Log file handler
        log_file = "./log/log_warning.log"
        print(f"Creating separate log file {log_file} for warning message")
        if not os.path.exists(log_file):
            open(log_file, "w+").close()

        return logger
    return wrapper


## decorated/wrapped func
# @decorate_init_logger # uncoment when to make decorator permanent
def init_logger(name):
    """
    Set up a logger instance
    name (str): Name of logger
    log_file (str): path to log file
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S",
    )
    # Add stream handler
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.INFO)
    streamhandler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(streamhandler)

    return logger
