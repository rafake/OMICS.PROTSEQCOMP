#!/bin/bash -l
#SBATCH -J minhash-analysis
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=5000
#SBATCH --partition topola
#SBATCH --time=0:01:00
#SBATCH -A g100-2238

# Set up environment
APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

echo "Starting MinHash similarity analysis job..."
echo "Start time: $(date)"

# Create output directory
mkdir -p output/minhash_results

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

# Find parquet directories in the latest sample directory
PARQUET_FILES=($(find "$LATEST_SAMPLE_DIR" -name "*.parquet" -type d))

if [ ${#PARQUET_FILES[@]} -lt 2 ]; then
    echo "Error: Need at least 2 parquet directories for comparison!"
    echo "Found ${#PARQUET_FILES[@]} parquet directories in $LATEST_SAMPLE_DIR"
    echo "Available files:"
    ls -la "$LATEST_SAMPLE_DIR" 2>/dev/null || echo "Directory is empty or inaccessible"
    exit 1
fi

echo "Found ${#PARQUET_FILES[@]} parquet directories in $LATEST_SAMPLE_DIR:"
for file in "${PARQUET_FILES[@]}"; do
    echo "- $(basename "$file")"
done

# Use first two parquet directories for comparison
MOUSE_PARQUET_PATH="${PARQUET_FILES[0]}"
FISH_PARQUET_PATH="${PARQUET_FILES[1]}"

echo "Using files for MinHash analysis:"
echo "  File 1 (mouse): $MOUSE_PARQUET_PATH"
echo "  File 2 (fish): $FISH_PARQUET_PATH"

# Run MinHash analysis with ADAM container
echo "Running MinHash similarity analysis..."

# Export file paths and sample timestamp for the Python script to use
export MOUSE_PARQUET_PATH
export FISH_PARQUET_PATH
export SAMPLE_TIMESTAMP

$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python minhash.py

echo "MinHash analysis job completed!"
echo "End time: $(date)"
echo "Check output in: output/minhash_results/"