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

# Load Anaconda module for Python environment with matplotlib
echo "Loading Anaconda module..."
module load apps/anaconda/2024-10

# Verify Python and required packages are available
echo "Python version:"
python --version
echo "Checking required packages..."
python -c "import matplotlib, pandas; print('matplotlib and pandas are available')" 2>/dev/null || {
    echo "Warning: matplotlib or pandas may not be available"
    echo "Attempting to install with conda..."
    conda install -y matplotlib pandas
}

# Create slurm and plots output directories
mkdir -p slurm plots

echo "Starting benchmark results analysis job..."
echo "SLURM Job ID: $SLURM_JOB_ID"
echo "SLURM output files will be moved to: slurm/benchmark-analysis-$SLURM_JOB_ID.out/err"
echo "Using Anaconda Python environment"
echo "Start time: $(date)"
echo ""
echo "Usage options:"
echo "  sbatch analyze_benchmark_batch.sh                    # Analyze latest benchmark results"
echo "  sbatch analyze_benchmark_batch.sh <directory_path>   # Analyze specific directory"

# Check if analysis script exists
if [[ ! -f "analyze_benchmark_results.py" ]]; then
    echo "Error: analyze_benchmark_results.py not found in current directory"
    echo "Please make sure you're running this from the correct directory"
    exit 1
fi

# Check for optional directory parameter or find latest automatically
if [[ -n "$1" ]]; then
    BENCHMARK_DIR="$1"
    echo "Using specified benchmark directory: $BENCHMARK_DIR"
else
    # Find the latest benchmark directory automatically
    echo "No directory specified, searching for latest benchmark results..."
    
    # Check if output/benchmark_results exists
    if [[ ! -d "output/benchmark_results" ]]; then
        echo "Error: output/benchmark_results directory does not exist"
        echo "Please run benchmark.sh first to generate benchmark results."
        echo ""
        echo "Usage examples:"
        echo "  sbatch benchmark.sh jaccard"
        echo "  sbatch benchmark.sh minhash"
        exit 1
    fi
    
    # Find all benchmark directories (timestamp format: YYYYMMDD_HHMMSS)
    BENCHMARK_DIRS=($(find output/benchmark_results -maxdepth 1 -type d -name "*_*" | sort))
    
    if [[ ${#BENCHMARK_DIRS[@]} -eq 0 ]]; then
        echo "Error: No benchmark result directories found in output/benchmark_results/"
        echo "Please run benchmark.sh first to generate benchmark results."
        echo ""
        echo "Usage examples:"
        echo "  sbatch benchmark.sh jaccard"
        echo "  sbatch benchmark.sh minhash"
        exit 1
    fi
    
    # Get the latest benchmark directory (last in sorted array)
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

# Run the Python analysis script using Anaconda Python
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
    
    # Check for plots in the benchmark results directory
    PLOTS_FILE="$BENCHMARK_DIR/plots/benchmark_performance_analysis.png"
    if [[ -f "$PLOTS_FILE" ]]; then
        echo "  - Performance plots: $PLOTS_FILE"
        echo "    File size: $(du -h "$PLOTS_FILE" | cut -f1)"
    else
        echo "  - Performance plots: Check job output above (plots may not have been saved)"
    fi
    echo "  - Detailed summary: Check job output above"
    echo ""
    echo "To view the results:"
    echo "  - Summary tables are displayed in the job output above"
    echo "  - Performance plots saved in benchmark results directory"
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
echo "  - Analysis plots: $BENCHMARK_DIR/plots/benchmark_performance_analysis.png"