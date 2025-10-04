#!/bin/bash -l
#SBATCH -J test-task 
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=10
#SBATCH --partition topola
#SBATCH --time=00:05:00
#SBATCH -A g100-2238

APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

echo "Using Apptainer from $APPTAINER"

# Run your PySpark script inside the ADAM container
$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python test_script.py