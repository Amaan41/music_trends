from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, hour, date_format, dayofweek
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("Listening Trends Dashboard Data Generator") \
    .getOrCreate()

# Database connection properties
db_properties = {
    "user": "root",
    "password": "zayaan@06",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# Read data from streaming_stats (avg time per song)
avg_time_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "streaming_stats") \
    .options(**db_properties) \
    .load()

# Read data from songs_per_window
songs_count_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "songs_per_window") \
    .options(**db_properties) \
    .load()

# Convert string datetime to actual timestamps
avg_time_df = avg_time_df.withColumn("window_start", to_timestamp("window_start"))
songs_count_df = songs_count_df.withColumn("window_start", to_timestamp("window_start"))

# Calculate time of day trends - when do people listen to music?
hour_distribution = avg_time_df \
    .withColumn("hour_of_day", hour("window_start")) \
    .groupBy("hour_of_day") \
    .agg(F.count("*").alias("window_count"), 
         F.sum("avg_ms_played").alias("total_ms_played"))

# Calculate day of week trends
day_distribution = avg_time_df \
    .withColumn("day_of_week", dayofweek("window_start")) \
    .groupBy("day_of_week") \
    .agg(F.count("*").alias("window_count"),
         F.sum("avg_ms_played").alias("total_ms_played"))

# Calculate average song length trend over time (by month)
song_length_trend = avg_time_df \
    .withColumn("month_year", date_format("window_start", "yyyy-MM")) \
    .groupBy("month_year") \
    .agg(F.avg("avg_ms_played").alias("avg_song_length_ms")) \
    .withColumn("avg_song_length_sec", col("avg_song_length_ms") / 1000)

# Calculate listening intensity (songs per 30min window) trend
listening_intensity = songs_count_df \
    .withColumn("month_year", date_format("window_start", "yyyy-MM")) \
    .groupBy("month_year") \
    .agg(F.avg("total_songs").alias("avg_songs_per_window"))

# Save all the trend data to database
hour_distribution.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "hour_distribution_trends") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

day_distribution.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "day_distribution_trends") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

song_length_trend.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "song_length_trends") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

listening_intensity.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "listening_intensity_trends") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

# Display sample results
print("Hour of Day Distribution:")
hour_distribution.orderBy("hour_of_day").show(24)

print("Day of Week Distribution:")
day_distribution.orderBy("day_of_week").show(7)

print("Monthly Song Length Trends:")
song_length_trend.orderBy("month_year").show(10)

print("Monthly Listening Intensity Trends:")
listening_intensity.orderBy("month_year").show(10)

spark.stop()