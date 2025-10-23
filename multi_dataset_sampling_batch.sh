#!/bin/bash -l
#SBATCH -J multi-sampling-task
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=5000
#SBATCH --partition topola
#SBATCH --time=00:30:00
#SBATCH -A g100-2238
#SBATCH --output=slurm/multi-sampling-task-%j.out
#SBATCH --error=slurm/multi-sampling-task-%j.err

# Apptainer path (local installation in repository)
APPTAINER=$PWD/tools/apptainer/bin/apptainer

# Create slurm output directory
mkdir -p slurm

# Create timestamped output directory for this batch run
BATCH_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BATCH_OUTPUT_DIR="output/samples_parquet/sample_${BATCH_TIMESTAMP}"
mkdir -p "$BATCH_OUTPUT_DIR"

echo "Starting multi-dataset sampling job..."
echo "Batch timestamp: $BATCH_TIMESTAMP"
echo "Output directory: $BATCH_OUTPUT_DIR"

# Iterate through directories in input folder
for input_dir in input/*/; do
    if [[ -d "$input_dir" ]]; then
        # Extract directory name (remove input/ prefix and trailing slash)
        dataset_name=$(basename "$input_dir")
        
        # Check if directory contains parquet files or has parquet suffix
        if [[ "$dataset_name" == *"parquet"* ]] || find "$input_dir" -name "*.parquet" -type f | grep -q .; then
            echo "Processing dataset: $dataset_name"
            
            # Run sampling for this dataset
            $APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python -c "
import sys
sys.path.append('.')
dataset_name = '$dataset_name'
input_path = '$input_dir'
batch_output_dir = '$BATCH_OUTPUT_DIR'
batch_timestamp = '$BATCH_TIMESTAMP'
exec(open('multi_dataset_sampling.py').read())
"
            
            echo "Completed sampling for: $dataset_name"
        else
            echo "Skipping $dataset_name (no parquet files found)"
        fi
    fi
done

echo "Multi-dataset sampling job completed!"