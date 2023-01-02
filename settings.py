import getpass
from pathlib import Path

user = getpass.getuser()

# this will hopefully avoid hand editing paths everytime.
# fill further for convenience.
if user == "mengel":
    conda_path = "/home/mengel/anaconda3/envs/pymc3/"
    data_dir = "/home/mengel/data/20190306_IsimipDetrend/"
    # data_dir = "/p/tmp/mengel/isimip/isi-cfact"
    log_dir = "./log"

# elif user == "sitreu":
#     # conda_path = "/home/sitreu/.conda/envs/mpi_py3"
#     # data_dir = "/home/sitreu/Documents/PIK/CounterFactuals/isi-cfact/"
#     data_dir = "/p/tmp/sitreu/isimip/isi-cfact"
#     log_dir = "./log"

#data_dir =r"C:\Users\Anna\Documents\UNI\PIK\test_input"
data_dir = "/mnt/c/Users/Anna/Documents/UNI/PIK/test_input"
log_dir = "./log"


input_dir = Path(data_dir) / "test_input"
# input_dir = Path(data_dir) / "input"
# make output dir same as cwd. Helps if running more than one job.
output_dir = Path(data_dir) / "output" / Path.cwd().name

# max time in sec for sampler for a single grid cell.
timeout = 60 * 60
# tas, tasrange pr, prsn, prsnratio, ps, rlds, wind, hurs
variable = "pr"  # select variable to detrend

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
startdate = None # may at a date in the format '1950-01-01' to train only on date from after that date

# for example "GSWP3", "GSWP3-W5E5"
dataset = "GSWP3-W5E5"
# use a dataset with only subset spatial grid points for testing
#lateral_sub = 1
lateral_sub = 40

gmt_file = dataset.lower() + "_ssa_gmt.nc4"
landsea_file = dataset + "/" + "landseamask_sub" + str(lateral_sub) + ".nc"
#landsea_file = dataset + "/" + "landseamask.full" + ".nc"
#landsea_file = "ISIMIP2b_landseamask_generic_sub" + str(lateral_sub) + ".nc4"
# source_file = variable + "_" + dataset + "_sub.nc4"
source_file = variable + "_" + dataset + "_sub" + str(lateral_sub) + ".nc4"
cfact_file = variable + "_" + dataset + "_cfactual.nc4"
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
