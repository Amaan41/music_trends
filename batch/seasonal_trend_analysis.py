from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, month, year, count, avg, desc
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("Seasonal Music Trend Analysis") \
    .getOrCreate()

# Database connection properties  
db_properties = {
    "user": "root",
    "password": "zayaan@06",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# Read data from the top_track table
tracks_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "top_track") \
    .options(**db_properties) \
    .load()

# Read data from the streaming_stats table
streaming_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "streaming_stats") \
    .options(**db_properties) \
    .load()

# Convert string datetime to actual timestamps
tracks_df = tracks_df.withColumn("window_start", to_timestamp("window_start"))
streaming_df = streaming_df.withColumn("window_start", to_timestamp("window_start"))

# Extract month and year
tracks_df = tracks_df \
    .withColumn("year", year("window_start")) \
    .withColumn("month", month("window_start"))

streaming_df = streaming_df \
    .withColumn("year", year("window_start")) \
    .withColumn("month", month("window_start"))

# Define seasons
seasons = {
    "Winter": [12, 1, 2],
    "Spring": [3, 4, 5],
    "Summer": [6, 7, 8],
    "Fall": [9, 10, 11]
}

# Create season column
def season_udf(month):
    for season_name, months in seasons.items():
        if month in months:
            return season_name
    return None

# Register UDF
season_udf_spark = F.udf(season_udf)

# Add season column
tracks_df = tracks_df.withColumn("season", season_udf_spark(col("month")))
streaming_df = streaming_df.withColumn("season", season_udf_spark(col("month")))

# Seasonal top tracks
seasonal_tracks = tracks_df.groupBy("year", "season", "track_name") \
    .agg(F.sum("play_count").alias("total_plays"))

# Window specification for ranking within season/year
window_spec = Window.partitionBy("year", "season").orderBy(desc("total_plays"))

# Get top 10 tracks per season per year
seasonal_top_tracks = seasonal_tracks \
    .withColumn("rank", F.rank().over(window_spec)) \
    .filter(col("rank") <= 10)

# Seasonal listening statistics
seasonal_stats = streaming_df.groupBy("year", "season") \
    .agg(
        avg("avg_ms_played").alias("avg_song_length_ms"),
        count("*").alias("total_song_plays")
    )

# Store results
seasonal_top_tracks.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "seasonal_top_tracks") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

seasonal_stats.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "seasonal_listening_stats") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

# Display sample results for the most recent year
current_year = spark.sql("SELECT YEAR(CURRENT_DATE()) as year").collect()[0]['year']
    
print(f"Top Tracks by Season for {current_year}:")
seasonal_top_tracks.filter(col("year") == current_year) \
    .orderBy("season", "rank") \
    .select("season", "rank", "track_name", "total_plays") \
    .show()

print(f"Seasonal Listening Stats for {current_year}:")
seasonal_stats.filter(col("year") == current_year) \
    .orderBy("season") \
    .select("season", "avg_song_length_ms", "total_song_plays") \
    .show()

spark.stop()