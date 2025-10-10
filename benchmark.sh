#!/bin/bash -l
#SBATCH -J OMICS-benchmark          # job name
#SBATCH -N 1                        # number of nodes (1 node is sufficient)
#SBATCH -n 1                        # number of tasks (1 task)
#SBATCH -c 4                        # number of cores (here: 4, you can change this!)
#SBATCH --time=00:30:00             # time limit (in HH:MM:SS format)
#SBATCH -A g100-2238                # your computational grant
#SBATCH -p topola                   # partition, i.e., "queue"

# Set up environment
APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

# Check for no-save parameter
NO_SAVE_FLAG=""
if [[ "$1" == "--no-save" || "$1" == "--dry-run" ]]; then
    NO_SAVE_FLAG="--no-save"
    echo "Running in NO-SAVE mode - results will only be displayed, not saved"
fi

echo "Starting OMICS benchmark job..."
echo "Start time: $(date)"
echo "Using $SLURM_CPUS_PER_TASK CPU cores"

# Find the latest sample directory based on timestamp
SAMPLE_DIRS=($(find output/samples_parquet -name "sample_*" -type d | sort))

if [ ${#SAMPLE_DIRS[@]} -eq 0 ]; then
    echo "Error: No sample directories found in output/samples_parquet/"
    echo "Please run multi_dataset_sampling_batch.sh first to generate samples."
    exit 1
fi

# Get the latest sample directory (last in sorted array)
LATEST_SAMPLE_DIR="${SAMPLE_DIRS[-1]}"
echo "Using latest sample directory: $LATEST_SAMPLE_DIR"

# Extract timestamp from sample directory name (format: sample_YYYYMMDD_HHMMSS)
SAMPLE_TIMESTAMP=$(basename "$LATEST_SAMPLE_DIR" | sed 's/sample_//')
echo "Extracted sample timestamp: $SAMPLE_TIMESTAMP"

# Find .adam directories in the latest sample directory
ADAM_FILES=($(find "$LATEST_SAMPLE_DIR" -name "*.adam" -type d))

if [ ${#ADAM_FILES[@]} -lt 2 ]; then
    echo "Error: Need at least 2 .adam directories for comparison!"
    exit 1
fi

# Use first two .adam directories for comparison
MOUSE_ADAM_PATH="${ADAM_FILES[0]}"
FISH_ADAM_PATH="${ADAM_FILES[1]}"

echo "Using files for benchmark:"
echo "  File 1 (mouse): $MOUSE_ADAM_PATH"
echo "  File 2 (fish): $FISH_ADAM_PATH"

# Export file paths and sample timestamp for the Python script to use
export MOUSE_ADAM_PATH
export FISH_ADAM_PATH
export SAMPLE_TIMESTAMP

# Create output directory for benchmark results (unless in no-save mode)
if [[ -z "$NO_SAVE_FLAG" ]]; then
    mkdir -p output/benchmark_results
fi

# Benchmark command with time measurement
echo "Running benchmark with $SLURM_CPUS_PER_TASK cores..."

if [[ -z "$NO_SAVE_FLAG" ]]; then
    # Normal mode: save benchmark results to file
    srun -N 1 -n 1 -c $SLURM_CPUS_PER_TASK \
    /usr/bin/time -v \
    $APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 \
    python jaccard.py \
    > output/benchmark_results/jaccard_benchmark_${SLURM_CPUS_PER_TASK}cores_${SAMPLE_TIMESTAMP}.out 2>&1
    
    echo "Benchmark completed!"
    echo "End time: $(date)"
    echo "Results saved to: output/benchmark_results/jaccard_benchmark_${SLURM_CPUS_PER_TASK}cores_${SAMPLE_TIMESTAMP}.out"
else
    # No-save mode: run with timing but don't save benchmark output to file
    srun -N 1 -n 1 -c $SLURM_CPUS_PER_TASK \
    /usr/bin/time -v \
    $APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 \
    python jaccard.py $NO_SAVE_FLAG
    
    echo "Benchmark completed (no-save mode)!"
    echo "End time: $(date)"
    echo "No benchmark files saved - results displayed above only"
fi