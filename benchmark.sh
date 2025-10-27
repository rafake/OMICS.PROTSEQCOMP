#!/bin/bash -l
#SBATCH -J OMICS-multi-benchmark    # job name
#SBATCH -N 1                        # number of nodes (1 node is sufficient)
#SBATCH -n 1                        # number of tasks (1 task)
#SBATCH -c 16                       # request 16 CPUs per task (maximum we'll use)
#SBATCH --mem=32000                 # request 32GB memory for large dataset processing
#SBATCH --time=00:30:00             # extended time limit for large datasets
#SBATCH -A g100-2238                # your computational grant
#SBATCH -p topola                   # partition, i.e., "queue"
#SBATCH --output=slurm/OMICS-multi-benchmark-%j.out
#SBATCH --error=slurm/OMICS-multi-benchmark-%j.err

# Set up environment
APPTAINER=$PWD/tools/apptainer/bin/apptainer

# Create slurm output directory
mkdir -p slurm

# Configure Spark memory settings for large datasets
export SPARK_DRIVER_MEMORY="12g"
export SPARK_EXECUTOR_MEMORY="12g"
export SPARK_DRIVER_MAXRESULTSIZE="8g"
export SPARK_SERIALIZER="org.apache.spark.serializer.KryoSerializer"
# Additional JVM tuning for large datasets
export SPARK_DRIVER_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=200"
export SPARK_EXECUTOR_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=200"

# Check for required comparison method parameter
if [[ -z "$1" ]]; then
    echo "Error: Missing required parameter!"
    echo "Usage: sbatch benchmark_multi_srun.sh <comparison_method>"
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

# Define core counts to test
CORE_COUNTS=(1 2 4 8 16)

# Get the number of CPUs allocated to this job
ALLOCATED_CPUS=${SLURM_CPUS_PER_TASK:-1}

echo "Starting OMICS multi-core benchmark job..."
echo "Benchmarking: $COMPARISON_METHOD analysis"
echo "Allocated CPUs: $ALLOCATED_CPUS"
echo "Testing core counts: ${CORE_COUNTS[*]}"
echo "Note: $COMPARISON_METHOD script runs in no-save mode for pure performance measurement"
echo "Start time: $(date)"

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

# Loop through different core counts and run benchmarks sequentially
for CORES in "${CORE_COUNTS[@]}"; do
    echo ""
    echo "========================================="
    echo "Running $COMPARISON_METHOD benchmark with $CORES cores..."
    echo "Start time for $CORES cores: $(date)"
    echo "========================================="
    
    # Run benchmark using srun with specified core count
    srun -N 1 -n 1 -c $CORES \
    $APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 \
    bash -c "export SPARK_DRIVER_MEMORY=$SPARK_DRIVER_MEMORY; export SPARK_EXECUTOR_MEMORY=$SPARK_EXECUTOR_MEMORY; export SPARK_DRIVER_MAXRESULTSIZE=$SPARK_DRIVER_MAXRESULTSIZE; export SPARK_SERIALIZER=$SPARK_SERIALIZER; export SPARK_DRIVER_OPTS='$SPARK_DRIVER_OPTS'; export SPARK_EXECUTOR_OPTS='$SPARK_EXECUTOR_OPTS'; time python ${COMPARISON_METHOD}.py --no-save" \
    > output/benchmark_results/${SAMPLE_TIMESTAMP}/${COMPARISON_METHOD}_benchmark_${CORES}cores.out 2>&1
    
    # Check if the benchmark completed successfully
    if [ $? -eq 0 ]; then
        echo "✓ $COMPARISON_METHOD benchmark with $CORES cores completed successfully!"
    else
        echo "✗ $COMPARISON_METHOD benchmark with $CORES cores failed!"
    fi
    
    echo "Results saved to: output/benchmark_results/${SAMPLE_TIMESTAMP}/${COMPARISON_METHOD}_benchmark_${CORES}cores.out"
done

echo ""
echo "========================================="
echo "All benchmarks completed!"
echo "End time: $(date)"
echo "========================================="
echo "Results directory: output/benchmark_results/${SAMPLE_TIMESTAMP}/"
echo "Files created:"
for CORES in "${CORE_COUNTS[@]}"; do
    echo "  - ${COMPARISON_METHOD}_benchmark_${CORES}cores.out"
done

