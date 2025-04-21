from pyspark.sql import SparkSession
from pyspark.sql.functions import col, weekofyear, year
from pyspark.sql.window import Window
from pyspark.sql import functions as F

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("Weekly Top Artists Batch Processing") \
    .getOrCreate()

# Database connection properties
db_properties = {
    "user": "root",
    "password": "zayaan@06",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# Read data from the top_artist table
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "top_artist") \
    .options(**db_properties) \
    .load()

# Convert string datetime to actual timestamps
df = df.withColumn("window_start", F.to_timestamp("window_start"))

# Extract week and year information
df = df \
    .withColumn("year", year("window_start")) \
    .withColumn("week", weekofyear("window_start"))

# Aggregate play counts by artist for each week
weekly_artist_counts = df.groupBy("year", "week", "artist_name") \
    .agg(F.sum("play_count").alias("total_plays"))

# Define a window partitioned by year and week, ordered by play count
window_spec = Window.partitionBy("year", "week").orderBy(F.desc("total_plays"))

# Add rank column to identify top 10
top_artists_df = weekly_artist_counts \
    .withColumn("rank", F.rank().over(window_spec)) \
    .filter(col("rank") <= 10)

# Show the results
top_artists_df = top_artists_df.orderBy("year", "week", "rank")

# Save to database
top_artists_df.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "weekly_top_artists") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

# Display results for the most recent week
current_year = spark.sql("SELECT YEAR(CURRENT_DATE()) as year").collect()[0]['year']
current_week = spark.sql("SELECT WEEKOFYEAR(CURRENT_DATE()) as week").collect()[0]['week']

print(f"Top 10 Artists for Week {current_week}, {current_year}:")
top_artists_df.filter((col("year") == current_year) & (col("week") == current_week)) \
    .select("rank", "artist_name", "total_plays") \
    .show()

spark.stop()