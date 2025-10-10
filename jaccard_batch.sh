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

# Check if input files exist
if [ ! -d "mouse.adam" ] || [ ! -d "danio.adam" ]; then
    echo "Error: Input files mouse.adam or danio.adam not found!"
    echo "Please ensure the ADAM parquet files are in the current directory."
    exit 1
fi

echo "Input files found:"
echo "- mouse.adam: $(ls -la mouse.adam 2>/dev/null | wc -l) files"
echo "- danio.adam: $(ls -la danio.adam 2>/dev/null | wc -l) files"

# Run Jaccard analysis with ADAM container
echo "Running Jaccard similarity analysis..."
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