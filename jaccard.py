from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, lit, size, rand
from pyspark.sql.types import FloatType, ArrayType, StringType
import os

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
mouse_df = spark.read.format("parquet").load("mouse.adam")
fish_df  = spark.read.format("parquet").load("danio.adam")

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
pairs = mouse_kmers.crossJoin(fish_kmers) \
    .select(
        col("name").alias("mouse_id"),
        col("sequence").alias("mouse_seq"),
        col("kmers").alias("mouse_kmers"),
        col("name_1").alias("fish_id"),
        col("sequence_1").alias("fish_seq"),
        col("kmers_1").alias("fish_kmers")
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
# 9️⃣ Save outputs
# ----------------------------------------------------------
results.write.mode("overwrite").parquet("mouse_zebrafish_100x100_jaccard.parquet")
top10.write.mode("overwrite").csv("top10_mouse_fish_jaccard.csv", header=True)

# ----------------------------------------------------------
# 🔟 Show results
# ----------------------------------------------------------
top10.show(truncate=False)