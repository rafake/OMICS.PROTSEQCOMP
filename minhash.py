from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, rand, explode, collect_list, length, greatest, abs
from pyspark.sql.types import ArrayType, StringType
from pyspark.sql.functions import pandas_udf
from pyspark.sql.functions import floor
import pandas as pd
from pyspark.ml.feature import HashingTF, MinHashLSH
import os
import shutil
import sys
from datetime import datetime

# ----------------------------------------------------------
# 0️⃣ Check for no-save parameter and working directory

# Check if --no-save parameter is passed
no_save_mode = "--no-save" in sys.argv or "--dry-run" in sys.argv
if no_save_mode:
    print("Running in NO-SAVE mode - results will only be displayed, not saved")

# Check if --length-filter parameter is passed
length_filter_mode = "--length-filter" in sys.argv
if length_filter_mode:
    print("Running in LENGTH-FILTER mode - only comparing pairs with <10% length difference")

print("Current working directory:", os.getcwd())

# ------------------------------------------------------------
# 1️⃣ Start Spark session
# ------------------------------------------------------------
from pyspark import SparkConf
conf = SparkConf()
conf.set("spark.sql.shuffle.partitions", "96")
conf.set("spark.sql.adaptive.enabled", "true")
conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
conf.set("spark.sql.adaptive.shuffle.targetPostShuffleInputSize", "64MB")
conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")

conf.set("spark.memory.fraction", "0.5")
conf.set("spark.memory.storageFraction", "0.2")

conf.set("spark.executor.instances", "4")
conf.set("spark.executor.cores", "6")
conf.set("spark.executor.memory", "20g")
conf.set("spark.executor.memoryOverhead", "4g")
conf.set("spark.driver.memory", "12g")
spark = SparkSession.builder.appName("MouseFishMinHash").config(conf=conf).getOrCreate()

# ------------------------------------------------------------
# 2️⃣ Load ADAM data from sample directories
# ------------------------------------------------------------
# Get file paths from environment variables or use defaults
mouse_path = os.environ.get('MOUSE_ADAM_PATH', 'mouse.adam')
fish_path = os.environ.get('FISH_ADAM_PATH', 'danio.adam')

print(f"Loading mouse data from: {mouse_path}")
print(f"Loading fish data from: {fish_path}")

# Load ADAM format data (which is stored as parquet internally)
mouse_df = spark.read.format("parquet").load(mouse_path)
fish_df  = spark.read.format("parquet").load(fish_path)

# ------------------------------------------------------------
# 3️⃣ Use all sequences from sample data (already sampled)
# ------------------------------------------------------------
print(f"Mouse dataset contains {mouse_df.count()} sequences")
print(f"Fish dataset contains {fish_df.count()} sequences")

mouse_sample = mouse_df.select("name", "sequence")
fish_sample  = fish_df.select("name", "sequence")

# ------------------------------------------------------------
# 4️⃣ Define UDF to extract 3-mers
# ------------------------------------------------------------
@pandas_udf(ArrayType(StringType()))
def get_kmers_pd(seqs: pd.Series) -> pd.Series:
    k = 3
    return seqs.fillna("").apply(lambda s: [s[i:i+k] for i in range(len(s)-k+1)] if len(s) >= k else [])

mouse_kmers = mouse_sample.withColumn("kmers", get_kmers_pd(col("sequence")))
fish_kmers  = fish_sample.withColumn("kmers", get_kmers_pd(col("sequence")))

# ------------------------------------------------------------
# 5️⃣ Convert k-mers to hashed feature vectors
# ------------------------------------------------------------

hashingTF = HashingTF(inputCol="kmers", outputCol="features", numFeatures=2**14)  # 16,384

mouse_hashed = hashingTF.transform(mouse_kmers).select("name", "sequence", "features")
fish_hashed  = hashingTF.transform(fish_kmers).select("name", "sequence", "features")

# Add sequence length and bucket columns for bucketing
def add_len_bucket(df, bucket=100):  # 100 aa bucket works well
    return (df.withColumn("sequence_length", length(col("sequence")))
              .withColumn("len_bucket", floor(col("sequence_length")/bucket)))

mouse_h = add_len_bucket(mouse_hashed)
fish_h  = add_len_bucket(fish_hashed)

# ------------------------------------------------------------
# 6️⃣ Build MinHashLSH model
# ------------------------------------------------------------



# --- per-bucket LSH joins (keep this) ---
mh = MinHashLSH(inputCol="features", outputCol="hashes", numHashTables=12)  # was 8
model_mouse = mh.fit(mouse_hashed)

bucket_rows = (mouse_h.select("len_bucket").distinct()
               .intersect(fish_h.select("len_bucket").distinct())
               .collect())
buckets = [r["len_bucket"] for r in bucket_rows]

def is_empty(df):
    return df.selectExpr("1").limit(1).count() == 0

all_parts = []
for b in buckets:
    m_part = mouse_h.filter(col("len_bucket") == b).repartition(96)
    f_part = fish_h.filter(col("len_bucket") == b).repartition(96)
    if is_empty(m_part) or is_empty(f_part):
        continue
    m_mh = model_mouse.transform(m_part)
    f_mh = model_mouse.transform(f_part)
    part = model_mouse.approxSimilarityJoin(m_mh, f_mh, threshold=0.05, distCol="dist")
    all_parts.append(part)

if all_parts:
    similarities = all_parts[0]
    for part in all_parts[1:]:
        similarities = similarities.unionByName(part)
else:
    empty_schema = model_mouse.approxSimilarityJoin(
        model_mouse.transform(mouse_h.limit(0)),
        model_mouse.transform(fish_h.limit(0)),
        threshold=0.05, distCol="dist").schema
    similarities = spark.createDataFrame([], empty_schema)

# (global join removed; only per-bucket similarities are used)

# ------------------------------------------------------------
# 8️⃣ Process results
# ------------------------------------------------------------
# Convert Spark's distance (1 - Jaccard) to similarity
if length_filter_mode:
    results = similarities.select(
        col("datasetA.name").alias("mouse_id"),
        col("datasetB.name").alias("fish_id"),
        col("datasetA.sequence_length").alias("mouse_length"),
        col("datasetB.sequence_length").alias("fish_length"),
        (1 - col("dist")).alias("minhash_similarity")
    ).filter(
        abs(col("mouse_length") - col("fish_length")) / 
        greatest(col("mouse_length"), col("fish_length")) <= 0.1
    )
    print("Applied length filtering: comparing only pairs with ≤10% length difference")
else:
    results = similarities.select(
        col("datasetA.name").alias("mouse_id"),
        col("datasetB.name").alias("fish_id"),
        (1 - col("dist")).alias("minhash_similarity")
    )

# Get top-10 most similar pairs
top10 = results.orderBy(col("minhash_similarity").desc()).limit(10)

# ------------------------------------------------------------
# 9️⃣ Save outputs to timestamped directory (unless in no-save mode)
# ------------------------------------------------------------
if not no_save_mode:
    # Use sample timestamp from environment variable, or fall back to current time
    sample_timestamp = os.environ.get('SAMPLE_TIMESTAMP')
    if sample_timestamp:
        timestamp = sample_timestamp
        print(f"Using sample timestamp from environment: {timestamp}")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"No sample timestamp found, using current time: {timestamp}")

    comparison_output_dir = f"output/protein_comparison/{timestamp}"
    minhash_output_dir = f"{comparison_output_dir}/minhash"
    os.makedirs(minhash_output_dir, exist_ok=True)

    print(f"Saving MinHash results to: {minhash_output_dir}")

    # Save all results to Parquet
    results.write.mode("overwrite").parquet(f"{minhash_output_dir}/mouse_fish_minhash_results.parquet")

    # Save top 10 results to CSV (essential columns only)
    top10_for_csv = top10.select("mouse_id", "fish_id", "minhash_similarity")
    top10_for_csv.write.mode("overwrite").csv(f"{minhash_output_dir}/top10_mouse_fish_minhash.csv", header=True)

    # Copy input files to shared comparison directory (only if not already copied)
    print("Checking for shared input data directory...")

    # Create shared input data directory
    input_data_dir = f"{comparison_output_dir}/input_data"
    os.makedirs(input_data_dir, exist_ok=True)

    # Copy mouse sample files (only if not already present and local)
    mouse_source = mouse_path
    mouse_dest = f"{input_data_dir}/mouse_sample"
    def is_local(p):
        return p.startswith("/") and os.path.exists(p)
    if not os.path.exists(mouse_dest):
        if is_local(mouse_source):
            shutil.copytree(mouse_source, mouse_dest, dirs_exist_ok=True)
            print(f"Mouse sample data copied to: {mouse_dest}")
        else:
            print(f"Warning: Mouse source directory not found or not local: {mouse_source}")
    else:
        print(f"Mouse sample data already exists at: {mouse_dest}")

    # Copy fish sample files (only if not already present and local)
    fish_source = fish_path
    fish_dest = f"{input_data_dir}/fish_sample"
    if not os.path.exists(fish_dest):
        if is_local(fish_source):
            shutil.copytree(fish_source, fish_dest, dirs_exist_ok=True)
            print(f"Fish sample data copied to: {fish_dest}")
        else:
            print(f"Warning: Fish source directory not found or not local: {fish_source}")
    else:
        print(f"Fish sample data already exists at: {fish_dest}")

    print("MinHash similarity analysis completed successfully!")
    print(f"Results saved to protein comparison directory: {comparison_output_dir}")
    print(f"MinHash results structure:")
    print(f"  - {minhash_output_dir}/mouse_fish_minhash_results.parquet (all results)")
    print(f"  - {minhash_output_dir}/top10_mouse_fish_minhash.csv (top 10 matches)")
    print(f"Shared input data:")
    print(f"  - {input_data_dir}/mouse_sample/ (original mouse data)")
    print(f"  - {input_data_dir}/fish_sample/ (original fish data)")
else:
    print("Skipping file save operations (no-save mode enabled)")
    print("MinHash similarity analysis completed - results displayed below only")

# ------------------------------------------------------------
# 🔟 Show results
# ------------------------------------------------------------
print("\nTop 10 most similar protein pairs:")
top10.select("mouse_id", "fish_id", "minhash_similarity").show(truncate=False)

spark.stop()