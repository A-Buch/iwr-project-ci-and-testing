
# ATTRICI - counterfactual climate for impact attribution

Code implementing the methods described in the paper `ATTRICI 1.1 - counterfactual climate for impact attribution` in Geoscientific Model Development. The code is archived at [ZENODO](https://doi.org/10.5281/zenodo.3828914).


## Project Structure
* All general settings are defined in [settings.py](settings.py).
* The code can be run with [run_estimation.py](run_estimation.py) or [run_single_cell.py](run_single_cell.py).
* The probability model for different climate variables is specified in [models.py](attrici/models.py)
* The choice of the probability model for a variable is specified in [estimator.py](attrici/estimator.py)


## Installion under WSL2

Please do:
Replace ```<env_name>``` by self-defined environment name and ```<path_to>``` by the file path to the environment file located in the ```config``` folder

Navigate to the ```test_input``` folder if you haven't done yet:

Create conda environment with python=3.7 and all packages mentioned in environment.yml
`conda create --name <env_name> --file ./<path_to>/config/environment.yml`

Activate conda environment
`conda activate <env_name>`

Install package which is not mentioned in environment.yml
`pip install func_timeout`

If pymc3 can be loaded as module in PPC cluster, you may need to install mkl_rt package 
`conda install mkl`

You may optionally 
`cp config/theanorc ~/.theanorc`

Load compiler
`module load compiler/gnu/7.3.0`

In the root package directory 
`pip install -e .`

Override the conda setting with 
`export CXX=g++`


## USAGE

The parallelization part to run large datasets is currently taylored to the supercomputer at the Potsdam Institute for Climate Impact Research using the [slurm scheduler](https://slurm.schedmd.com/documentation.html). Generalizing it into a package is ongoing work. We use the GNU compiler as the many parallel compile jobs through jobarrays and JIT compilation conflict with the few Intel licenses.

Adjust `settings.py`


**Option 1 for input data (sample):**

Use the provided sample dataset, which is already preprocessed, located in `./test-input/GSWP3-W5E5/`. In this subfolder the datasets for the variables precipiation (pr) and air temperature (tas) are provided, as also a land-sea mask.
Skip the section about Preprocessing and run following python scripts directly to generate counterfactual data:
```python run_estimation.py```
```python merge_cfact.py```


**Option 2 for input data (user-defined):**

Alternatively load input data from [https://data.isimip.org](https://data.isimip.org)]
The input for one variable is a single netcdf file containing all time steps. 
Create smoothed gmt time series as predictor using `preprocessing/calc_gmt_by_ssa.py` with adjusted file-paths.
Get auxiliary *tasskew* and *tasrange* time series using `preprocessing/create_tasrange_tasskew.py` with adjusted file-paths.

For estimating parameter distributions (above step 1) and smaller datasets
`python run_estimation.py`

For larger datasets, produce a `submit.sh` file via
`python create_submit.py`

Then submit to the slurm scheduler
`sbatch submit.sh`

For merging the single timeseries files to netcdf datasets
`python merge_cfact.py`


## Handle several runs with different settings

Copy the `settings.py`, `run_estimation.py`, `merge_cfact.py` and `submit.sh` to a separate directory,
for example `myrunscripts`. Adjust `settings.py` and `submit.sh`, in particular the output directoy, and continue as in Usage.


## Preprocessing

Example for GSWP3-W5E5 dataset, which is first priority in ISIMIP3a.

`cd preprocess` 
Download decadal data and merge it into one file per variable.
Adjust output paths and
`python merge_data.py`
Approximately 1 hour.

Produce GMT from gridded surface air temperature and use SSA to smooth it.
Use a separate conda env to cover SSA package dependencies.
Adjust output paths and
`python calc_gmt_by_ssa.py`
Approximately less than an hour.

Create tasrange and tasskew from tas variables.
Adjust output paths and
`python create_tasmin_tasmax.py`
Approximately an hour.

For testing smaller dataset, use
`python subset_data.py`
Add sub01 to filenames, if no subsetting is used.

Land-sea file creation
We use the ISIMIP2b land-sea mask to select only land cells for processing.
Smaller datasets through subsetting were created using CDO.


## Postprocessing

For tasmin and tasmax, we do not estimate counterfactual time series individually to avoid large relative errors in the daily temperature range as pointed out by (Piani et al. 2010). Following (Piani et al. 2010), we estimate counterfactuals of the daily temperature range tasrange = tasmax - tasmin and the skewness of the daily temperature tasskew = (tas - tasmin) / tasrange. Use [create_tasmin_tasmax.py](postprocessing/create_tasmin_tasmax.py)
with adjusted paths for the _tas_, _tasrange_ and _tasskew_ counterfactuals.

A counterfactual huss is derived from the counterfacual tas, ps and hurs using the equations of Buck (1981) as described in Weedon et al. (2010). Use [derive_huss.sh](postprocessing/derive_huss.sh)
with adjusted file names and the required time range.


## Example

See [here](examples/tas_example.ipynb) for a notebook visualizing the generated counterfactual data.


## Example for SLURM job script:
*Explantation of commands used on PIKs HPC cluster*

'''
#!/bin/bash

#SBATCH --qos=standby   ## takes currently unused nodes
#SBATCH --partition=priority

#SBATCH --job-name=attrici_tas_corr
#SBATCH --account=dmcci
#SBATCH --output=/p/tmp/<username>/log/%x_%a.log
#SBATCH --error=/p/tmp/<username>/log/%x_%a.log
#SBATCH --mail-type=END,FAIL,TIME_LIMIT
#SBATCH --mail-user=<pik.mailadrress>
#SBATCH --ntasks=1
#SBATCH --array=0-3370%800  ## divides into 3370 indepentend jobs, while always max. 800 are running at the same time
#SBATCH --cpus-per-task=2
#SBATCH --time=01:00:00

# rm -rf /tmp/*  # optional: empty tmp folder

module purge
module load compiler/gnu/7.3.0
module load git
module load anaconda/5.0.0_py3

export CXX=g++

# set tmp_dir and comiledir which are needed for theano package
tmpdir=/p/tmp/<username>/theano/theano_${SLURM_ARRAY_TASK_ID}.tmp
mkdir -p $tmpdir
export TMPDIR=$tmpdir

compiledir=/p/tmp/<username>/theano/$SLURM_ARRAY_TASK_ID
mkdir -p $compiledir
export THEANO_FLAGS=base_compiledir=$compiledir

# define garbage collector for cleaning up after python script execution as also in case jobs are aborted
cleanup() {
  rm -r $compiledir
  rm -r $tmpdir
  exit
}

# copy theanorc to current working directory. It includes settings on which pymc3 is based.
# Note: Within theanorc "floatX = float64" should be set.
cp /home/<username>/theanorc ./theanorc

# activate conda env and generate counterfactual climate data
source activate <env_name>
python -u ./scripts/run_estimation.py
python -u ./scripts/merge_cfact.py &
wait
cleanup

echo "Finished run."

'''





## Credits

We rely on the [pymc3](https://github.com/pymc-devs/pymc3) package for probabilistic programming (Salvatier et al. 2016).

An early version of the code on Bayesian estimation of parameters in timeseries with periodicity in PyMC3 was inspired by [Ritchie Vink's](https://www.ritchievink.com) [post](https://www.ritchievink.com/blog/2018/10/09/build-facebooks-prophet-in-pymc3-bayesian-time-series-analyis-with-generalized-additive-models/) on Bayesian timeseries analysis with additive models.

## License

This code is licensed under GPLv3, see the LICENSE.txt. See commit history for authors.
