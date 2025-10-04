#!/bin/bash -l
#SBATCH -J sampling-task
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=5000
#SBATCH --partition topola
#SBATCH --time=00:05:00
#SBATCH -A g100-2238

APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

# Run Spark container with sampling commands
$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python mus_musculus_sampling.py

echo "Mus musculus sampling job completed!"