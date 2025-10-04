# PySpark Commands for Mus Musculus Sampling
# Reads parquet files from input/mus_musculus and creates 100 samples

from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder \
    .appName("MusMusculusSampling") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Set log level to reduce verbose output
spark.sparkContext.setLogLevel("WARN")

print("Starting Mus musculus protein sampling...")

# Load Mus musculus dataset from input directory
print("Loading Mus musculus parquet data...")
df_mouse = spark.read.parquet("input/mus_muculus")

print(f"Total Mus musculus protein sequences: {df_mouse.count()}")

# Display schema
print("Dataset schema:")
df_mouse.printSchema()

# Stop Spark session
spark.stop()