#!/bin/bash -l
#SBATCH -J benchmark-analysis
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2000
#SBATCH --partition topola
#SBATCH --time=0:05:00
#SBATCH -A g100-2238
#SBATCH --output=benchmark-analysis-%j.out
#SBATCH --error=benchmark-analysis-%j.err

# Set up environment
APPTAINER=$HOME/zadanie/1_environment/apptainer_local/bin/apptainer

# Create slurm and plots output directories
mkdir -p slurm plots

echo "Starting benchmark results analysis job..."
echo "SLURM Job ID: $SLURM_JOB_ID"
echo "SLURM output files will be moved to: slurm/benchmark-analysis-$SLURM_JOB_ID.out/err"
echo "Start time: $(date)"

# Check if analysis script exists
if [[ ! -f "analyze_benchmark_results.py" ]]; then
    echo "Error: analyze_benchmark_results.py not found in current directory"
    echo "Please make sure you're running this from the correct directory"
    exit 1
fi

# Check for required directory parameter
if [[ -z "$1" ]]; then
    echo "Error: Missing required parameter!"
    echo "Usage: sbatch analyze_benchmark_batch.sh <benchmark_directory>"
    echo ""
    echo "Example:"
    echo "  sbatch analyze_benchmark_batch.sh output/benchmark_results/20251023_145030"
    echo ""
    echo "The directory should contain files matching: *_benchmark_*cores.out"
    exit 1
fi

BENCHMARK_DIR="$1"
echo "Using specified benchmark directory: $BENCHMARK_DIR"

# Verify the directory exists and contains benchmark files
if [[ ! -d "$BENCHMARK_DIR" ]]; then
    echo "Error: Directory '$BENCHMARK_DIR' does not exist"
    exit 1
fi

# Count benchmark files
BENCHMARK_FILES=($(find "$BENCHMARK_DIR" -maxdepth 1 -name "*_benchmark_*cores.out" 2>/dev/null))
if [[ ${#BENCHMARK_FILES[@]} -eq 0 ]]; then
    echo "Error: No benchmark files found in '$BENCHMARK_DIR'"
    echo "Looking for files matching pattern: *_benchmark_*cores.out"
    echo ""
    echo "Files in directory:"
    ls -la "$BENCHMARK_DIR" 2>/dev/null || echo "Directory is empty or inaccessible"
    exit 1
fi

echo "Found ${#BENCHMARK_FILES[@]} benchmark files:"
for file in "${BENCHMARK_FILES[@]}"; do
    echo "  - $(basename "$file")"
done
echo ""

# Create plots output directory
mkdir -p plots

echo "Running benchmark analysis..."
echo "============================================================================"

# Run the Python analysis script inside Apptainer container
$APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 \
python analyze_benchmark_results.py "$BENCHMARK_DIR"

ANALYSIS_RESULT=$?

echo ""
echo "============================================================================"
echo "Benchmark analysis job completed!"
echo "End time: $(date)"

if [[ $ANALYSIS_RESULT -eq 0 ]]; then
    echo "Analysis completed successfully!"
    echo ""
    echo "Output files:"
    if [[ -f "plots/benchmark_performance_analysis.png" ]]; then
        echo "  - Performance plots: plots/benchmark_performance_analysis.png"
        echo "    File size: $(du -h plots/benchmark_performance_analysis.png | cut -f1)"
    else
        echo "  - Performance plots: Check job output above (plots may not have been saved)"
    fi
    echo "  - Detailed summary: Check job output above"
    echo ""
    echo "To view the results:"
    echo "  - Summary tables are displayed in the job output above"
    echo "  - Performance plots saved to plots/benchmark_performance_analysis.png"
else
    echo "Analysis failed with exit code: $ANALYSIS_RESULT"
    echo "Check the error messages above for details"
fi

# Move SLURM output files to slurm directory
echo ""
echo "Moving SLURM output files to slurm directory..."
if [[ -f "benchmark-analysis-$SLURM_JOB_ID.out" ]]; then
    mv "benchmark-analysis-$SLURM_JOB_ID.out" "slurm/"
    echo "Moved: benchmark-analysis-$SLURM_JOB_ID.out -> slurm/"
fi
if [[ -f "benchmark-analysis-$SLURM_JOB_ID.err" ]]; then
    mv "benchmark-analysis-$SLURM_JOB_ID.err" "slurm/"
    echo "Moved: benchmark-analysis-$SLURM_JOB_ID.err -> slurm/"
fi

echo "Final output locations:"
echo "  - SLURM logs: slurm/benchmark-analysis-$SLURM_JOB_ID.out/err"
echo "  - Analysis plots: plots/benchmark_performance_analysis.png"