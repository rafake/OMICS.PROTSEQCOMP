#!/bin/bash -l
#SBATCH -J jaccard-analysis
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=5000
#SBATCH --partition topola
#SBATCH --time=0:01:00
#SBATCH -A g100-2238
#SBATCH --output=slurm/jaccard-analysis-%j.out
#SBATCH --error=slurm/jaccard-analysis-%j.err

# Set up environment
APPTAINER=$PWD/tools/bin/apptainer

# Create slurm output directory
mkdir -p slurm

# Check for no-save parameter
NO_SAVE_FLAG=""
if [[ "$1" == "--no-save" || "$1" == "--dry-run" ]]; then
    NO_SAVE_FLAG="--no-save"
    echo "Running in NO-SAVE mode - results will only be displayed, not saved"
fi

echo "Starting Jaccard similarity analysis job..."
echo "Start time: $(date)"

# Create output directory (unless in no-save mode)
if [[ -z "$NO_SAVE_FLAG" ]]; then
    mkdir -p output/protein_comparison
fi

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

# Export file paths and sample timestamp for the Python script to use
export MOUSE_ADAM_PATH
export FISH_ADAM_PATH
export SAMPLE_TIMESTAMP

$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 python jaccard.py $NO_SAVE_FLAG

# Check if output files were created (only in normal mode)
if [[ -z "$NO_SAVE_FLAG" ]]; then
    if [ -d "mouse_zebrafish_100x100_jaccard.parquet" ]; then
        echo "Jaccard results saved successfully!"
        echo "Moving results to output directory..."
        mv mouse_zebrafish_100x100_jaccard.parquet output/jaccard_results/
        mv top10_mouse_fish_jaccard.csv output/jaccard_results/ 2>/dev/null || echo "CSV file not found"
    else
        echo "Warning: Expected output files not found!"
    fi
fi

echo "Jaccard analysis job completed!"
echo "End time: $(date)"
echo "Check output in: output/protein_comparison/"