#!/bin/bash -l
#SBATCH -J test-task 
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=10
#SBATCH --partition topola
#SBATCH --time=00:05:00
#SBATCH -A g100-2238

echo "hello world sbatch"