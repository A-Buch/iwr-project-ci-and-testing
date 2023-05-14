#!/bin/bash

#SBATCH --qos=priority ##priority  ##
#SBATCH --partition=priority
#SBATCH --job-name=attrici_interpolation
#SBATCH --account=dmcci
#SBATCH --output=/p/tmp/annabu/attrici_interpolation/log/%x_%a.log
#SBATCH --error=/p/tmp/annabu/attrici_interpolation/log/%x_%a.log
##SBATCH --mail-type=END,FAIL,TIME_LIMIT
##SBATCH --mail-user=annabu@pik-potsdam.de
#SBATCH --nodes=1  # make sure all cores we get are on one node,  jobs of this type may not span nodes.
#SBATCH --ntasks=1
###SBATCH --array=0-3370%800
#SBATCH --array=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:30:00


# rm -rf /tmp/*

module purge
module load compiler/gnu/7.3.0
module load git
module load anaconda/5.0.0_py3

export CXX=g++
tmpdir=/p/tmp/annabu/attrici_interpolation/theano_${SLURM_ARRAY_TASK_ID}.tmp
mkdir -p $tmpdir
export TMPDIR=$tmpdir

## for 1arr+1CPU -> comment
## settings for multiprocessing
#unset I_MPI_DAPL_UD
#unset I_MPI_DAPL_UD_PROVIDER
#export I_MPI_PMI_LIBRARY=/p/system/slurm/lib/libpmi.so

## for 1arr+1CPU -> comment
## if you're using OpenMP for threading
#export OMP_PROC_BIND=true # make sure our threads stick to cores
#export OMP_NUM_THREADS=16 ##8  # see: intern Cluster User Guide documentation.com, matches how many cpus-per-task we asked for
#export SUBMITTED=1

compiledir=/p/tmp/annabu/attrici_interpolation/theano/$SLURM_ARRAY_TASK_ID
mkdir -p $compiledir
export THEANO_FLAGS=base_compiledir=$compiledir

cleanup() {
  rm -r $compiledir
  rm -r $tmpdir
  exit
}

cp /home/annabu/theanorc ./theanorc
# trap cleanup SIGTERM

source activate attrici_2
#python -u ./scripts/preprocessing/merge_data.py &
#python -u ./scripts/preprocessing/binary_mask.py &
#python -u ./scripts/calc_gmt_by_ssa.py &
#python -u ./scripts/run_estimation.py &
#python -u ./scripts/mask_interpolated_parameterfile.py &
python -u ./scripts/merge_cfact.py &


wait
cleanup

echo "Finished run."

## measure time after job 
# sacct -j jobID_0 --format=submit
# sacct -j jobID_3370 --format=end

