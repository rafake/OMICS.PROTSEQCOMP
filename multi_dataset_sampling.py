# Multi-Dataset PySpark Sampling Script
# Processes any dataset passed via environment variables

from pyspark.sql import SparkSession
import os
from datetime import datetime

# Get dataset info from environment/variables
dataset_name = globals().get('dataset_name', 'unknown')
input_path = globals().get('input_path', 'input/')
batch_output_dir = globals().get('batch_output_dir', None)
batch_timestamp = globals().get('batch_timestamp', None)

# If not running from batch script, find latest sample directory
if batch_output_dir is None or batch_timestamp is None:
    import glob
    sample_dirs = glob.glob("output/samples_parquet/sample_*")
    if sample_dirs:
        # Sort by directory name (which includes timestamp) and get the latest
        latest_sample_dir = sorted(sample_dirs)[-1]
        batch_output_dir = latest_sample_dir
        # Extract timestamp from directory name
        batch_timestamp = latest_sample_dir.split('sample_')[-1]
        print(f"Using latest sample directory: {latest_sample_dir}")
    else:
        # Create new timestamped directory if none exist
        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_output_dir = f"output/samples_parquet/sample_{batch_timestamp}"
        os.makedirs(batch_output_dir, exist_ok=True)
        print(f"Created new sample directory: {batch_output_dir}")

# Initialize Spark session
spark = SparkSession.builder \
    .appName(f"Sampling_{dataset_name}") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Set log level to reduce verbose output
spark.sparkContext.setLogLevel("WARN")

print(f"Starting protein sampling for dataset: {dataset_name}")

try:
    # Load dataset from input directory
    print(f"Loading parquet data from: {input_path}")
    df = spark.read.parquet(input_path)
    
    total_count = df.count()
    print(f"Total protein sequences in {dataset_name}: {total_count}")
    
    if total_count == 0:
        print(f"No data found in {dataset_name}, skipping sampling")
    else:
        # Display schema
        print("Dataset schema:")
        df.printSchema()
        
        # Take sample (100 or all if less than 100)
        sample_size = min(100, total_count)
        print(f"Taking {sample_size} random samples...")
        
        # Sampling - Convert to RDD and take random rows
        sample_rows = df.rdd.takeSample(withReplacement=False, num=sample_size, seed=42)
        
        # Convert back to DataFrame
        df_sample = spark.createDataFrame(sample_rows, schema=df.schema)
        
        # Verify sample
        print(f"Sample size: {df_sample.count()}")
        print("Sample preview:")
        df_sample.show(5, truncate=False)
        
        # Save to Parquet format (single file) with batch timestamp
        output_parquet = f"{batch_output_dir}/{batch_timestamp}_100_{dataset_name}"
        print(f"Saving samples to Parquet: {output_parquet}")
        df_sample.coalesce(1).write.mode("overwrite").parquet(output_parquet)
        
        print(f"Sampling completed for {dataset_name}!")
        print(f"Output file saved to: {output_parquet}/")

except Exception as e:
    print(f"Error processing {dataset_name}: {str(e)}")

finally:
    # Stop Spark session
    spark.stop()