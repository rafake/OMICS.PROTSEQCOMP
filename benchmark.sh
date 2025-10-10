#!/bin/bash -l
#SBATCH -J OMICS-benchmark          # job name
#SBATCH -N 1                        # number of nodes (1 node is sufficient)
#SBATCH -n 1                        # number of tasks (1 task)
#SBATCH --time=00:30:00             # time limit (in HH:MM:SS format)
#SBATCH -A g100-2238                # your computational grant
#SBATCH -p topola                   # partition, i.e., "queue"
#SBATCH --array=0-4                 # array job for 5 different core counts

# Set up environment
APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

# Define core counts array
CORE_COUNTS=(1 2 4 8 16)
CORES=${CORE_COUNTS[$SLURM_ARRAY_TASK_ID]}

# Set the number of CPUs for this specific array task
export SLURM_CPUS_PER_TASK=$CORES

# Check for required comparison method parameter
if [[ -z "$1" ]]; then
    echo "Error: Missing required parameter!"
    echo "Usage: sbatch benchmark.sh <comparison_method>"
    echo "Available methods:"
    echo "  jaccard  - Benchmark Jaccard similarity analysis"
    echo "  minhash  - Benchmark MinHash similarity analysis"
    exit 1
fi

COMPARISON_METHOD="$1"

# Validate comparison method
if [[ "$COMPARISON_METHOD" != "jaccard" && "$COMPARISON_METHOD" != "minhash" ]]; then
    echo "Error: Invalid comparison method '$COMPARISON_METHOD'"
    echo "Available methods: jaccard, minhash"
    exit 1
fi

echo "Starting OMICS benchmark job (Array Task $SLURM_ARRAY_TASK_ID)..."
echo "Benchmarking: $COMPARISON_METHOD analysis"
echo "Note: $COMPARISON_METHOD script runs in no-save mode for pure performance measurement"
echo "Start time: $(date)"
echo "Using $SLURM_CPUS_PER_TASK CPU cores (from array position $SLURM_ARRAY_TASK_ID)"

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
    echo "Found ${#ADAM_FILES[@]} .adam directories in $LATEST_SAMPLE_DIR"
    exit 1
fi

# Use first two .adam directories for comparison
MOUSE_ADAM_PATH="${ADAM_FILES[0]}"
FISH_ADAM_PATH="${ADAM_FILES[1]}"

echo "Using files for $COMPARISON_METHOD benchmark:"
echo "  File 1 (mouse): $MOUSE_ADAM_PATH"
echo "  File 2 (fish): $FISH_ADAM_PATH"

# Export file paths and sample timestamp for the Python script to use
export MOUSE_ADAM_PATH
export FISH_ADAM_PATH
export SAMPLE_TIMESTAMP

# Create output directory for benchmark results
mkdir -p output/benchmark_results/${SAMPLE_TIMESTAMP}

# Benchmark command with time measurement
echo "Running $COMPARISON_METHOD benchmark with $SLURM_CPUS_PER_TASK cores..."
echo "$COMPARISON_METHOD script running in no-save mode for pure computation timing..."

# Run benchmark and save results to timestamped directory
srun -N 1 -n 1 -c $SLURM_CPUS_PER_TASK \
/usr/bin/time -v \
$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 \
python ${COMPARISON_METHOD}.py --no-save \
> output/benchmark_results/${SAMPLE_TIMESTAMP}/${COMPARISON_METHOD}_benchmark_${SLURM_CPUS_PER_TASK}cores.out 2>&1

echo "$COMPARISON_METHOD benchmark completed (Array Task $SLURM_ARRAY_TASK_ID)!"
echo "End time: $(date)"
echo "Results saved to: output/benchmark_results/${SAMPLE_TIMESTAMP}/${COMPARISON_METHOD}_benchmark_${SLURM_CPUS_PER_TASK}cores.out"