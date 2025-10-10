#!/bin/bash -l
#SBATCH -J jaccard-analysis
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=5000
#SBATCH --partition topola
#SBATCH --time=0:01:00
#SBATCH -A g100-2238

# Set up environment
APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

echo "Starting Jaccard similarity analysis job..."
echo "Start time: $(date)"

# Create output directory
mkdir -p output/jaccard_results

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

# Find .adam directories in the latest sample directory
ADAM_FILES=($(find "$LATEST_SAMPLE_DIR" -name "*.adam" -type d))

if [ ${#ADAM_FILES[@]} -lt 2 ]; then
    echo "Error: Need at least 2 .adam directories for comparison!"
    echo "Found ${#ADAM_FILES[@]} .adam directories in $LATEST_SAMPLE_DIR"
    echo "Available files:"
    ls -la "$LATEST_SAMPLE_DIR" 2>/dev/null || echo "Directory is empty or inaccessible"
    exit 1
fi

echo "Found ${#ADAM_FILES[@]} .adam directories in $LATEST_SAMPLE_DIR:"
for file in "${ADAM_FILES[@]}"; do
    echo "- $(basename "$file")"
done

# Use first two .adam directories for comparison
MOUSE_ADAM_PATH="${ADAM_FILES[0]}"
FISH_ADAM_PATH="${ADAM_FILES[1]}"

echo "Using files for Jaccard analysis:"
echo "  File 1 (mouse): $MOUSE_ADAM_PATH"
echo "  File 2 (fish): $FISH_ADAM_PATH"

# Run Jaccard analysis with ADAM container
echo "Running Jaccard similarity analysis..."

# Export file paths for the Python script to use
export MOUSE_ADAM_PATH
export FISH_ADAM_PATH

$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python jaccard.py

# Check if output files were created
if [ -d "mouse_zebrafish_100x100_jaccard.parquet" ]; then
    echo "Jaccard results saved successfully!"
    echo "Moving results to output directory..."
    mv mouse_zebrafish_100x100_jaccard.parquet output/jaccard_results/
    mv top10_mouse_fish_jaccard.csv output/jaccard_results/ 2>/dev/null || echo "CSV file not found"
else
    echo "Warning: Expected output files not found!"
fi

echo "Jaccard analysis job completed!"
echo "End time: $(date)"
echo "Check output in: output/jaccard_results/"