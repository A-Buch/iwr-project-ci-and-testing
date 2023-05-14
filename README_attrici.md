
# ATTRICI - counterfactual climate for impact attribution

Code implementing the methods described in the paper `ATTRICI 1.1 - counterfactual climate for impact attribution` in Geoscientific Model Development. The code is archived at [ZENODO](https://doi.org/10.5281/zenodo.3828914).



*Note*: Example input file (already merged) located in PIK cloud within a shared folder called *ERA5_example_input*


## Write out parameters to file 
Run files located in scripts_writeParameters with submit.sh, i.e. with example input data
Uncomment within submit.sh:
`python -u ./scripts/run_estimation.py &`

### Interpolate parameters
Run interpolation script with submit.sh. Uncomment within submit.sh:
`python -u ./scripts/mask_interpolated_parameterfile.py &`

## Load parameters and write to timeseries files
Run files located in scripts_loadParameters with submit.sh
Uncomment within submit.sh:
`python -u ./scripts/run_estimation.py &`




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

```





## Credits

We rely on the [pymc3](https://github.com/pymc-devs/pymc3) package for probabilistic programming (Salvatier et al. 2016).

An early version of the code on Bayesian estimation of parameters in timeseries with periodicity in PyMC3 was inspired by [Ritchie Vink's](https://www.ritchievink.com) [post](https://www.ritchievink.com/blog/2018/10/09/build-facebooks-prophet-in-pymc3-bayesian-time-series-analyis-with-generalized-additive-models/) on Bayesian timeseries analysis with additive models.

## License

This code is licensed under GPLv3, see the LICENSE.txt. See commit history for authors.
