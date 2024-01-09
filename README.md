
# ATTRICI - counterfactual climate for impact attribution

Code implementing the methods described in the paper `ATTRICI 1.1 - counterfactual climate for impact attribution` in Geoscientific Model Development. The code is archived at [ZENODO](https://doi.org/10.5281/zenodo.3828914).

*Note*: Example input file (already merged) located in PIK cloud within a shared folder called *ERA5_example_input*

In this branch an interpolation approach is tested. 
The aim is to increase the perfomrance of the current toolbox by only calculating a subset of the cells for an AOI, remaining cells will be interpolated. 
For this the bias between original and interpolated counterfactual is evaluated inside ```overview.ipynb```


Adapt your paths and file names in the following scripts and in ```settings.py```:

#### Align factual input file
Joins timesteps, align dimesnions into one file and creates a subset of the AOI
`python -u ./merge_data.py &`

#### Create landseamask and binary mask
Creates a land(sea)mask based on the factual input dataset. 
The binary mask is only needed for testing the interpolation
`python -u ./create_masks.py &`


#### Write out trace files
Write out trace file containing parameter values on which the counterfactual variable is based on. 
One trace file is created for each cell of the AOI. 
`python -u ./run_estimation_write.py &`

`conda create -c conda-forge -n attrici "pymc>=5" python=3.10.11`

#### Interpolate parameters
Interpolate parameters. The script loads the parameters stored in the trace files, writes them to a netCDF file and interpolates them. 
The script contains functions which are currently used for testing the interpolation approach, they will be removed later.  
`python -u ./interpolate_parameters.py &`

#### Load parameters and write to timeseries files
Load the interpolated parameters to timeseries files for each cell of the AOI.
Only a single process is needed - set in the batch script `#SBATCH --array=1`
`python -u ./run_estimation_load.py &`

#### Create counterfactual dataset
Based on the timeseries files a netCDF4 file containing the counterfactual values is created
`python -u ./merge_cfact.py &`


## Example for SLURM job script:
*Explantation of commands used on PIKs HPC cluster*

```
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


# set tmp_dir and compiledir which are needed for theano package
export CXX=g++
tmpdir=/p/tmp/<username>/theano/theano_${SLURM_ARRAY_TASK_ID}.tmp
mkdir -p $tmpdir
export TMPDIR=$tmpdir

compiledir=/p/tmp/<username>/theano/$SLURM_ARRAY_TASK_ID
mkdir -p $compiledir
export THEANO_FLAGS=base_compiledir=$compiledir

# settings for multiprocessing
unset I_MPI_DAPL_UD
unset I_MPI_DAPL_UD_PROVIDER
export I_MPI_PMI_LIBRARY=/p/system/slurm/lib/libpmi.so

# if you're using OpenMP for threading
export OMP_PROC_BIND=true # make sure our threads stick to cores
export OMP_NUM_THREADS=8  # see: intern Custer User Guide documentation.com, matches how many cpus-per-task we asked for
export SUBMITTED=1


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

#### Uncomment the script you need #####
#python -u ./create_masks.py &
#python -u ./run_estimation_write.py &
#python -u ./run_estimation_load.py &


wait
cleanup

echo "Finished run."

```





## Credits

We rely on the [pymc3](https://github.com/pymc-devs/pymc3) package for probabilistic programming (Salvatier et al. 2016).

An early version of the code on Bayesian estimation of parameters in timeseries with periodicity in PyMC3 was inspired by [Ritchie Vink's](https://www.ritchievink.com) [post](https://www.ritchievink.com/blog/2018/10/09/build-facebooks-prophet-in-pymc3-bayesian-time-series-analyis-with-generalized-additive-models/) on Bayesian timeseries analysis with additive models.

## License

This code is licensed under GPLv3, see the LICENSE.txt. See commit history for authors.