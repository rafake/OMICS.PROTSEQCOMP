#!/bin/bash -l
#SBATCH -J multi-sampling-task
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8000
#SBATCH --partition topola
#SBATCH --time=00:30:00
#SBATCH -A g100-2238

APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

# Create output directories
mkdir -p output/samples_parquet
mkdir -p output/samples_csv

echo "Starting multi-dataset sampling job..."

# Iterate through directories in input folder
for input_dir in input/*/; do
    if [[ -d "$input_dir" ]]; then
        # Extract directory name (remove input/ prefix and trailing slash)
        dataset_name=$(basename "$input_dir")
        
        # Check if directory contains parquet files or has parquet suffix
        if [[ "$dataset_name" == *"parquet"* ]] || find "$input_dir" -name "*.parquet" -type f | grep -q .; then
            echo "Processing dataset: $dataset_name"
            
            # Create dataset-specific output directories
            mkdir -p "output/samples_parquet/${dataset_name}_100"
            mkdir -p "output/samples_csv/${dataset_name}_100"
            
            # Run sampling for this dataset
            $APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python -c "
import sys
sys.path.append('.')
dataset_name = '$dataset_name'
input_path = '$input_dir'
exec(open('multi_dataset_sampling.py').read())
"
            
            echo "Completed sampling for: $dataset_name"
        else
            echo "Skipping $dataset_name (no parquet files found)"
        fi
    fi
done

echo "Multi-dataset sampling job completed!"