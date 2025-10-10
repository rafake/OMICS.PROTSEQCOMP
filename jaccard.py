from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, lit, size, rand
from pyspark.sql.types import FloatType, ArrayType, StringType
import os
import shutil
from datetime import datetime

# ----------------------------------------------------------
# 0️⃣ Check working directory
# ----------------------------------------------------------
print("Current working directory:", os.getcwd())
print("Files in current directory:")
for item in os.listdir():
    print(f"  - {item}")

# ----------------------------------------------------------
# 1️⃣ Start Spark session
# ----------------------------------------------------------
spark = SparkSession.builder \
    .appName("MouseFishJaccard") \
    .getOrCreate()

# ----------------------------------------------------------
# 2️⃣ Load Parquet / ADAM data
# ----------------------------------------------------------
# Get file paths from environment variables or use defaults
mouse_path = os.environ.get('MOUSE_ADAM_PATH', 'mouse.adam')
fish_path = os.environ.get('FISH_ADAM_PATH', 'danio.adam')

print(f"Loading mouse data from: {mouse_path}")
print(f"Loading fish data from: {fish_path}")

mouse_df = spark.read.format("parquet").load(mouse_path)
fish_df  = spark.read.format("parquet").load(fish_path)

# ----------------------------------------------------------
# 3️⃣ Sample 100 random sequences from each species
# ----------------------------------------------------------
mouse_sample = mouse_df.select("name", "sequence").orderBy(rand()).limit(100)
fish_sample  = fish_df.select("name", "sequence").orderBy(rand()).limit(100)

# ----------------------------------------------------------
# 4️⃣ Define a helper function to extract unique 3-mers
# ----------------------------------------------------------
def get_unique_kmers(seq, k=3):
    if seq is None or len(seq) < k:
        return []
    return list(set(seq[i:i+k] for i in range(len(seq) - k + 1)))

get_kmers_udf = udf(get_unique_kmers, ArrayType(StringType()))

mouse_kmers = mouse_sample.withColumn("kmers", get_kmers_udf(col("sequence")))
fish_kmers  = fish_sample.withColumn("kmers", get_kmers_udf(col("sequence")))

# ----------------------------------------------------------
# 5️⃣ Create all pairwise combinations (100 x 100 = 10,000)
# ----------------------------------------------------------
# First alias the DataFrames to avoid column name conflicts
mouse_kmers_aliased = mouse_kmers.alias("mouse")
fish_kmers_aliased = fish_kmers.alias("fish")

pairs = mouse_kmers_aliased.crossJoin(fish_kmers_aliased) \
    .select(
        col("mouse.name").alias("mouse_id"),
        col("mouse.sequence").alias("mouse_seq"),
        col("mouse.kmers").alias("mouse_kmers"),
        col("fish.name").alias("fish_id"),
        col("fish.sequence").alias("fish_seq"),
        col("fish.kmers").alias("fish_kmers")
    )

# ----------------------------------------------------------
# 6️⃣ Define a Jaccard similarity UDF
# ----------------------------------------------------------
def jaccard_similarity(kmers1, kmers2):
    if not kmers1 or not kmers2:
        return 0.0
    set1, set2 = set(kmers1), set(kmers2)
    union = len(set1 | set2)
    if union == 0:
        return 0.0
    inter = len(set1 & set2)
    return inter / union

jaccard_udf = udf(jaccard_similarity, FloatType())

# ----------------------------------------------------------
# 7️⃣ Compute Jaccard similarity in parallel
# ----------------------------------------------------------
results = pairs.withColumn("jaccard", jaccard_udf(col("mouse_kmers"), col("fish_kmers")))

# ----------------------------------------------------------
# 8️⃣ Sort and get top-10 most similar pairs
# ----------------------------------------------------------
top10 = results.orderBy(col("jaccard").desc()).limit(10)

# ----------------------------------------------------------
# 9️⃣ Save outputs to timestamped directory
# ----------------------------------------------------------
# Use sample timestamp from environment variable, or fall back to current time
sample_timestamp = os.environ.get('SAMPLE_TIMESTAMP')
if sample_timestamp:
    timestamp = sample_timestamp
    print(f"Using sample timestamp from environment: {timestamp}")
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"No sample timestamp found, using current time: {timestamp}")

comparison_output_dir = f"output/protein_comparison/{timestamp}"
jaccard_output_dir = f"{comparison_output_dir}/jaccard"
os.makedirs(jaccard_output_dir, exist_ok=True)

print(f"Saving Jaccard results to: {jaccard_output_dir}")

# Save all results to Parquet
results.write.mode("overwrite").parquet(f"{jaccard_output_dir}/mouse_zebrafish_100x100_jaccard.parquet")

# For CSV output, exclude array columns (CSV doesn't support complex types)
top10_for_csv = top10.select("mouse_id", "mouse_seq", "fish_id", "fish_seq", "jaccard")
top10_for_csv.write.mode("overwrite").csv(f"{jaccard_output_dir}/top10_mouse_fish_jaccard.csv", header=True)

# Copy input files to shared comparison directory
print("Copying input sample files to shared comparison directory...")

# Create shared input data directory
input_data_dir = f"{comparison_output_dir}/input_data"
os.makedirs(input_data_dir, exist_ok=True)

# Copy mouse sample files
mouse_source = mouse_path
mouse_dest = f"{input_data_dir}/mouse_sample"
if os.path.exists(mouse_source):
    shutil.copytree(mouse_source, mouse_dest, dirs_exist_ok=True)
    print(f"Mouse sample data copied to: {mouse_dest}")
else:
    print(f"Warning: Mouse source directory not found: {mouse_source}")

# Copy fish sample files
fish_source = fish_path
fish_dest = f"{input_data_dir}/fish_sample"
if os.path.exists(fish_source):
    shutil.copytree(fish_source, fish_dest, dirs_exist_ok=True)
    print(f"Fish sample data copied to: {fish_dest}")
else:
    print(f"Warning: Fish source directory not found: {fish_source}")

print("Jaccard similarity analysis completed successfully!")
print(f"Results saved to protein comparison directory: {comparison_output_dir}")
print(f"Jaccard results structure:")
print(f"  - {jaccard_output_dir}/mouse_zebrafish_100x100_jaccard.parquet (all results)")
print(f"  - {jaccard_output_dir}/top10_mouse_fish_jaccard.csv (top 10 matches)")
print(f"Shared input data:")
print(f"  - {input_data_dir}/mouse_sample/ (original mouse data)")
print(f"  - {input_data_dir}/fish_sample/ (original fish data)")

# ----------------------------------------------------------
# 🔟 Show results
# ----------------------------------------------------------
print("\nTop 10 most similar protein pairs:")
top10.select("mouse_id", "fish_id", "jaccard").show(truncate=False)