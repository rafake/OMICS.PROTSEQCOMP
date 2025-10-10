from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, rand, explode, collect_list
from pyspark.sql.types import ArrayType, StringType
from pyspark.ml.feature import HashingTF, MinHashLSH

# ------------------------------------------------------------
# 1️⃣ Start Spark session
# ------------------------------------------------------------
spark = SparkSession.builder.appName("MouseFishMinHash").getOrCreate()

# ------------------------------------------------------------
# 2️⃣ Load Parquet / ADAM data
# ------------------------------------------------------------
mouse_df = spark.read.parquet("mouse.adam")
fish_df  = spark.read.parquet("danio.adam")

# ------------------------------------------------------------
# 3️⃣ Randomly sample 100 sequences from each
# ------------------------------------------------------------
mouse_sample = mouse_df.select("name", "sequence").orderBy(rand()).limit(100)
fish_sample  = fish_df.select("name", "sequence").orderBy(rand()).limit(100)

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

top10.show(truncate=False)

# ------------------------------------------------------------
# 9️⃣ Save results
# ------------------------------------------------------------
results.write.mode("overwrite").parquet("mouse_fish_minhash_results.parquet")
top10.write.mode("overwrite").csv("top10_mouse_fish_minhash.csv", header=True)

spark.stop()