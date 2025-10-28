#!/bin/bash -l
#SBATCH -J OMICS-multi-benchmark-p    # job name
#SBATCH -N 1                        # number of nodes (1 node is sufficient)
#SBATCH -n 1                        # number of tasks (1 task)
#SBATCH -c 24                       # request 24 CPUs per task (maximum we'll use)
#SBATCH --mem=110000                # request 110GB memory for large dataset processing
#SBATCH --time=00:30:00             # extended time limit for large datasets
#SBATCH -A g100-2238                # your computational grant
#SBATCH -p topola                   # partition, i.e., "queue"
#SBATCH --output=slurm/OMICS-multi-benchmark-p-%j.out
#SBATCH --error=slurm/OMICS-multi-benchmark-p-%j.err

# Set up environment
APPTAINER=$PWD/tools/apptainer/bin/apptainer

# Create slurm output directory
mkdir -p slurm

# Load Anaconda module for better performance benchmarking
echo "Loading Anaconda module for native Python/Spark execution..."
module load apps/anaconda/2024-10

# Configure Spark settings optimized for core count and partitions
configure_spark_settings() {
    local cores=$1
    
    # Partition configuration: 3 partitions per core for good load balancing
    local partitions=$((cores * 3))
    
    # Memory configuration: scale with core count using available 110GB RAM
    # Rule: ~4-6GB per core, with 8GB minimum and 50GB maximum per component
    local memory_per_component=$((cores * 4096 + 8192))  # cores * 4GB + 8GB base
    if [ $memory_per_component -lt 8192 ]; then memory_per_component=8192; fi      # min 8GB
    if [ $memory_per_component -gt 51200 ]; then memory_per_component=51200; fi    # max 50GB (leave room for OS)
    
    local driver_memory="${memory_per_component}m"
    local executor_memory="${memory_per_component}m"
    local max_result_size=$((memory_per_component / 2))  # Half of driver memory
    
    # Export Spark configuration
    export SPARK_SQL_SHUFFLE_PARTITIONS=$partitions
    export SPARK_DEFAULT_PARALLELISM=$partitions
    export SPARK_DRIVER_MEMORY=$driver_memory
    export SPARK_EXECUTOR_MEMORY=$executor_memory
    export SPARK_DRIVER_MAXRESULTSIZE="${max_result_size}m"
    export SPARK_SERIALIZER="org.apache.spark.serializer.KryoSerializer"
    export SPARK_DRIVER_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=200"
    export SPARK_EXECUTOR_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=200"
    
    echo "Spark configuration for $cores cores:"
    echo "  Partitions: $partitions"
    echo "  Driver memory: $driver_memory"
    echo "  Executor memory: $executor_memory"
    echo "  Max result size: ${max_result_size}m"
}

# Verify Python and PySpark availability
echo "Python version: $(python --version)"
echo "Testing PySpark availability..."
python -c "from pyspark.sql import SparkSession; print('PySpark is available')" || {
    echo "Warning: PySpark not available in Anaconda, falling back to ADAM container"
    USE_CONTAINER=true
}


# Parse parameters
MAX_CORES=24
COMPARISON_METHOD=""
LENGTH_FILTER_FLAG=""

# Simple parameter parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        -c) MAX_CORES="$2"; shift 2 ;;
        -m) MEMORY_MB="$2"; shift 2 ;;
        -t) TIME_LIMIT="$2"; shift 2 ;;
        --length-filter) LENGTH_FILTER_FLAG="--length-filter"; shift ;;
        jaccard|minhash) COMPARISON_METHOD="$1"; shift ;;
        *) shift ;;
    esac
done

# Check required parameter
if [[ "$COMPARISON_METHOD" != "jaccard" && "$COMPARISON_METHOD" != "minhash" ]]; then
    echo "Usage: sbatch benchmark.sh <jaccard|minhash> [-c cores] [-m memory] [-t time]"
    exit 1
fi

# Define core counts to test
CORE_COUNTS=(1 2 4)
if [ $MAX_CORES -ge 8 ]; then CORE_COUNTS+=(8); fi
if [ $MAX_CORES -ge 16 ]; then CORE_COUNTS+=(16); fi
if [ $MAX_CORES -ge 24 ]; then CORE_COUNTS+=(24); fi

# Get the number of CPUs allocated to this job
ALLOCATED_CPUS=${SLURM_CPUS_PER_TASK:-1}

echo "Starting OMICS multi-core benchmark job..."
echo "Benchmarking: $COMPARISON_METHOD analysis"
echo "Testing core counts: ${CORE_COUNTS[*]}"
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
    
    # Configure optimal Spark settings for this core count
    configure_spark_settings $CORES
    
    # Run benchmark using srun with specified core count
    if [[ "$USE_CONTAINER" == "true" ]]; then
        echo "Using ADAM container (fallback mode)"
        srun -c $CORES \
        $APPTAINER exec docker://quay.io/biocontainers/adam:1.0.1--hdfd78af_0 \
        bash -c "export SPARK_DRIVER_MEMORY=$SPARK_DRIVER_MEMORY; export SPARK_EXECUTOR_MEMORY=$SPARK_EXECUTOR_MEMORY; export SPARK_DRIVER_MAXRESULTSIZE=$SPARK_DRIVER_MAXRESULTSIZE; export SPARK_SERIALIZER='$SPARK_SERIALIZER'; export SPARK_DRIVER_OPTS='$SPARK_DRIVER_OPTS'; export SPARK_EXECUTOR_OPTS='$SPARK_EXECUTOR_OPTS'; export SPARK_SQL_SHUFFLE_PARTITIONS=$SPARK_SQL_SHUFFLE_PARTITIONS; export SPARK_DEFAULT_PARALLELISM=$SPARK_DEFAULT_PARALLELISM; time python ${COMPARISON_METHOD}.py --no-save $LENGTH_FILTER_FLAG" \
        > output/benchmark_results/${SAMPLE_TIMESTAMP}/${COMPARISON_METHOD}_benchmark_${CORES}cores.out 2>&1
    else
        echo "Using native Anaconda Python (optimized for benchmarking)"
        srun -c $CORES \
        bash -c "module load apps/anaconda/2024-10; export SPARK_DRIVER_MEMORY=$SPARK_DRIVER_MEMORY; export SPARK_EXECUTOR_MEMORY=$SPARK_EXECUTOR_MEMORY; export SPARK_DRIVER_MAXRESULTSIZE=$SPARK_DRIVER_MAXRESULTSIZE; export SPARK_SERIALIZER='$SPARK_SERIALIZER'; export SPARK_DRIVER_OPTS='$SPARK_DRIVER_OPTS'; export SPARK_EXECUTOR_OPTS='$SPARK_EXECUTOR_OPTS'; export SPARK_SQL_SHUFFLE_PARTITIONS=$SPARK_SQL_SHUFFLE_PARTITIONS; export SPARK_DEFAULT_PARALLELISM=$SPARK_DEFAULT_PARALLELISM; time python ${COMPARISON_METHOD}.py --no-save $LENGTH_FILTER_FLAG" \
        > output/benchmark_results/${SAMPLE_TIMESTAMP}/${COMPARISON_METHOD}_benchmark_${CORES}cores.out 2>&1
    fi
    
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

