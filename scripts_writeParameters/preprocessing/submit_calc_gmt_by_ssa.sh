#!/bin/bash

#SBATCH --qos=priority
#SBATCH --partition=priority
#SBATCH --job-name=create_gmt_by_ssa
#SBATCH --account=isimip
#SBATCH --output=/p/tmp/sitreu/attrici/log/%x_%a.log
#SBATCH --error=/p/tmp/sitreu/attrici/log/%x_%a.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=00-23:50:00 

source activate isi-cfact_ssa

python ./calc_gmt_by_ssa.py
