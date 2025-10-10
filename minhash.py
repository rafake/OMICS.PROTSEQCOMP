from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, rand, explode, collect_list
from pyspark.sql.types import ArrayType, StringType
from pyspark.ml.feature import HashingTF, MinHashLSH
import os
import shutil
import sys
from datetime import datetime

# ----------------------------------------------------------
# 0️⃣ Check for no-save parameter and working directory
# ----------------------------------------------------------
# Check if --no-save parameter is passed
no_save_mode = "--no-save" in sys.argv or "--dry-run" in sys.argv
if no_save_mode:
    print("Running in NO-SAVE mode - results will only be displayed, not saved")

print("Current working directory:", os.getcwd())

# ------------------------------------------------------------
# 1️⃣ Start Spark session
# ------------------------------------------------------------
spark = SparkSession.builder.appName("MouseFishMinHash").getOrCreate()

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
def get_kmers(seq, k=3):
    if seq is None or len(seq) < k:
        return []
    return [seq[i:i+k] for i in range(len(seq) - k + 1)]

get_kmers_udf = udf(get_kmers, ArrayType(StringType()))

mouse_kmers = mouse_sample.withColumn("kmers", get_kmers_udf(col("sequence")))
fish_kmers  = fish_sample.withColumn("kmers", get_kmers_udf(col("sequence")))

# ------------------------------------------------------------
# 5️⃣ Convert k-mers to hashed feature vectors
# ------------------------------------------------------------
hashingTF = HashingTF(inputCol="kmers", outputCol="features", numFeatures=2**16)

mouse_hashed = hashingTF.transform(mouse_kmers)
fish_hashed  = hashingTF.transform(fish_kmers)

# ------------------------------------------------------------
# 6️⃣ Build MinHashLSH model
# ------------------------------------------------------------
mh = MinHashLSH(inputCol="features", outputCol="hashes", numHashTables=8)
model = mh.fit(mouse_hashed.union(fish_hashed))

# Transform both datasets to compute their MinHash signatures
mouse_mh = model.transform(mouse_hashed)
fish_mh  = model.transform(fish_hashed)

# ------------------------------------------------------------
# 7️⃣ Compute pairwise MinHash similarities
# ------------------------------------------------------------
# Approximate similarity join: finds pairs above a Jaccard threshold
similarities = model.approxSimilarityJoin(
    datasetA=mouse_mh,
    datasetB=fish_mh,
    threshold=1.0,  # 1.0 = include all pairs
    distCol="dist"
)

# ------------------------------------------------------------
# 8️⃣ Process results
# ------------------------------------------------------------
# Convert Spark’s distance (1 - Jaccard) to similarity
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

    # Copy mouse sample files (only if not already present)
    mouse_source = mouse_path
    mouse_dest = f"{input_data_dir}/mouse_sample"
    if not os.path.exists(mouse_dest):
        if os.path.exists(mouse_source):
            shutil.copytree(mouse_source, mouse_dest, dirs_exist_ok=True)
            print(f"Mouse sample data copied to: {mouse_dest}")
        else:
            print(f"Warning: Mouse source directory not found: {mouse_source}")
    else:
        print(f"Mouse sample data already exists at: {mouse_dest}")

    # Copy fish sample files (only if not already present)
    fish_source = fish_path
    fish_dest = f"{input_data_dir}/fish_sample"
    if not os.path.exists(fish_dest):
        if os.path.exists(fish_source):
            shutil.copytree(fish_source, fish_dest, dirs_exist_ok=True)
            print(f"Fish sample data copied to: {fish_dest}")
        else:
            print(f"Warning: Fish source directory not found: {fish_source}")
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