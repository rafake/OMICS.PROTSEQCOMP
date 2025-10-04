# PySpark Sampling Script - Task 4
# Simple 100-sample extraction for mouse and zebrafish protein data

# Load datasets
df_mouse = spark.read.parquet("mouse_protein_parquet")
df_zebrafish = spark.read.parquet("zebrafish_protein_parquet")

# Mouse sampling
# Convert to RDD and take 100 random rows
sample_rows_mouse = df_mouse.rdd.takeSample(withReplacement=False, num=100, seed=42)

# Convert back to DataFrame
df_mouse_100 = spark.createDataFrame(sample_rows_mouse, schema=df_mouse.schema)

# Check
print("Mouse - Number of rows:", df_mouse_100.count())
df_mouse_100.show(5, truncate=False)

# Zebrafish sampling
# Convert to RDD and take 100 random rows
sample_rows_zebrafish = df_zebrafish.rdd.takeSample(withReplacement=False, num=100, seed=42)

# Convert back to DataFrame
df_zebrafish_100 = spark.createDataFrame(sample_rows_zebrafish, schema=df_zebrafish.schema)

# Check
print("Zebrafish - Number of rows:", df_zebrafish_100.count())
df_zebrafish_100.show(5, truncate=False)

# Show top 5 rows for each dataset
print("\nMouse top 5 rows:")
df_mouse_100.show(5, truncate=False)

print("\nZebrafish top 5 rows:")
df_zebrafish_100.show(5, truncate=False)

# Save to Parquet format
df_mouse_100.write.mode("overwrite").parquet("samples_parquet/mouse_100")
df_zebrafish_100.write.mode("overwrite").parquet("samples_parquet/zebrafish_100")

# Save to CSV format
df_mouse_100.write.mode("overwrite").option("header", "true").csv("samples_csv/mouse_100")
df_zebrafish_100.write.mode("overwrite").option("header", "true").csv("samples_csv/zebrafish_100")