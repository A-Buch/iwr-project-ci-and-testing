#!/bin/bash


#SBATCH --qos=short
#SBATCH --partition=standard
##priority
#SBATCH --job-name=create_gmt_by_ssa
#SBATCH --account=dmcci
##SBATCH --account=isimip
#SBATCH --output=./log/%x_%a.log
#SBATCH --error=./log/%x_%a.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=00-23:50:00 

##source activate isi-cfact_ssa

python ./scripts/calc_gmt_by_ssa.py
