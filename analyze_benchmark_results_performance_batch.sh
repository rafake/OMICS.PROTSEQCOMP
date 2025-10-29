#!/bin/bash -l
#SBATCH -J benchmark-performance-analysis
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2000
#SBATCH --partition topola
#SBATCH --time=0:05:00
#SBATCH -A g100-2238
#SBATCH --output=benchmark-performance-analysis-%j.out
#SBATCH --error=benchmark-performance-analysis-%j.err

# Load Anaconda module for Python environment with matplotlib
module load apps/anaconda/2024-10

# Verify Python and required packages are available
python --version
python -c "import matplotlib, pandas; print('matplotlib and pandas are available')" 2>/dev/null || {
    echo "Warning: matplotlib or pandas may not be available"
    echo "Attempting to install with conda..."
    conda install -y matplotlib pandas
}

# Create slurm and plots output directories
mkdir -p slurm plots

echo "Starting benchmark performance analysis job..."
echo "SLURM Job ID: $SLURM_JOB_ID"
echo "SLURM output files will be moved to: slurm/benchmark-performance-analysis-$SLURM_JOB_ID.out/err"
echo "Using Anaconda Python environment"
echo "Start time: $(date)"
echo ""
echo "Usage options:"
echo "  sbatch analyze_benchmark_results_performance_batch.sh <log_file_path> <benchmark_results_dir>"

echo "  <log_file_path>         Path to the batch log file with Spark configuration info (required)"
echo "  <benchmark_results_dir> Path to the benchmark results directory (optional, will auto-detect if not provided)"

# Check if analysis script exists
if [[ ! -f "analyze_benchmark_results_performance.py" ]]; then
    echo "Error: analyze_benchmark_results_performance.py not found in current directory"
    exit 1
fi

# Check for required log file parameter
if [[ -z "$1" ]]; then
    echo "Error: Log file path is required as the first argument."
    exit 1
fi
LOG_FILE_PATH="$1"

# Check for optional benchmark results directory parameter
if [[ -n "$2" ]]; then
    BENCHMARK_DIR="$2"
    echo "Using specified benchmark directory: $BENCHMARK_DIR"
else
    # Find the latest benchmark directory automatically
    echo "No directory specified, searching for latest benchmark results..."
    if [[ ! -d "output/benchmark_results" ]]; then
        echo "Error: output/benchmark_results directory does not exist"
        exit 1
    fi
    BENCHMARK_DIRS=($(find output/benchmark_results -maxdepth 1 -type d -name "*_*" | sort))
    if [[ ${#BENCHMARK_DIRS[@]} -eq 0 ]]; then
        echo "Error: No benchmark result directories found in output/benchmark_results/"
        exit 1
    fi
    BENCHMARK_DIR="${BENCHMARK_DIRS[-1]}"
    echo "Found latest benchmark directory: $BENCHMARK_DIR"
fi

# Verify the directory exists and contains benchmark files
if [[ ! -d "$BENCHMARK_DIR" ]]; then
    echo "Error: Directory '$BENCHMARK_DIR' does not exist"
    exit 1
fi

# Count benchmark files
BENCHMARK_FILES=($(find "$BENCHMARK_DIR" -maxdepth 1 -name "*_benchmark_*cores.out" 2>/dev/null))
if [[ ${#BENCHMARK_FILES[@]} -eq 0 ]]; then
    echo "Error: No benchmark files found in '$BENCHMARK_DIR'"
    exit 1
fi

echo "Found ${#BENCHMARK_FILES[@]} benchmark files:"
for file in "${BENCHMARK_FILES[@]}"; do
    echo "  - $(basename "$file")"
done
echo ""

# Create plots output directory
mkdir -p plots

echo "Running benchmark performance analysis..."
echo "============================================================================"

# Run the Python analysis script using Anaconda Python
python analyze_benchmark_results_performance.py "$LOG_FILE_PATH" "$BENCHMARK_DIR"

ANALYSIS_RESULT=$?

echo ""
echo "============================================================================"
echo "Benchmark performance analysis job completed!"
echo "End time: $(date)"

if [[ $ANALYSIS_RESULT -eq 0 ]]; then
    echo "Analysis completed successfully!"
    echo ""
    echo "Output files:"
    PERF_PLOT="$BENCHMARK_DIR/plots/benchmark_performance.png"
    SPARK_PLOT="$BENCHMARK_DIR/plots/benchmark_spark_config.png"
    if [[ -f "$PERF_PLOT" ]]; then
        echo "  - Performance plot: $PERF_PLOT"
        echo "    File size: $(du -h "$PERF_PLOT" | cut -f1)"
    else
        echo "  - Performance plot: Check job output above (plot may not have been saved)"
    fi
    if [[ -f "$SPARK_PLOT" ]]; then
        echo "  - Spark config plots: $SPARK_PLOT"
        echo "    File size: $(du -h "$SPARK_PLOT" | cut -f1)"
    else
        echo "  - Spark config plots: Check job output above (plot may not have been saved)"
    fi
    echo "  - Detailed summary: Check job output above"
    echo ""
    echo "To view the results:"
    echo "  - Summary tables are displayed in the job output above"
    echo "  - Plots saved in benchmark results directory"
else
    echo "Analysis failed with exit code: $ANALYSIS_RESULT"
    echo "Check the error messages above for details"
fi

# Move SLURM output files to slurm directory
if [[ -f "benchmark-performance-analysis-$SLURM_JOB_ID.out" ]]; then
    mv "benchmark-performance-analysis-$SLURM_JOB_ID.out" "slurm/"
    echo "Moved: benchmark-performance-analysis-$SLURM_JOB_ID.out -> slurm/"
fi
if [[ -f "benchmark-performance-analysis-$SLURM_JOB_ID.err" ]]; then
    mv "benchmark-performance-analysis-$SLURM_JOB_ID.err" "slurm/"
    echo "Moved: benchmark-performance-analysis-$SLURM_JOB_ID.err -> slurm/"
fi

echo "Final output locations:"
echo "  - SLURM logs: slurm/benchmark-performance-analysis-$SLURM_JOB_ID.out/err"
echo "  - Analysis plots: $BENCHMARK_DIR/plots/benchmark_partitions_analysis.png"
