from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, lit, when, row_number, asc
from pyspark.sql.window import Window

# MySQL config
db_url = "jdbc:mysql://localhost:3306/spotifydb"
mysql_properties = {
    "user": "root",
    "password": "zayaan@06",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# Initialize Spark session
spark = SparkSession.builder \
    .appName("SpotifyInsights") \
    .config("spark.driver.extraClassPath", "/Users/mehenazasghar/Downloads/mysql-connector-j-9.3.0/mysql-connector-j-9.3.0.jar") \
    .getOrCreate()

def get_top10(df, entity_col):
    # Get latest (year, week)
    latest = df.select("year", "week").distinct().orderBy(col("year").desc(), col("week").desc()).limit(1)
    latest_year, latest_week = latest.collect()[0]["year"], latest.collect()[0]["week"]

    # Filter for latest week
    latest_df = df.filter((col("year") == latest_year) & (col("week") == latest_week))

    # Deduplicate ranks: tie-breaker by alphabetical order
    window = Window.orderBy(col("total_plays").desc(), col(entity_col).asc())
    ranked_df = latest_df.withColumn("ranked", row_number().over(window)).filter(col("ranked") <= 10)

    return ranked_df.select(entity_col, "total_plays", "ranked")

def hour_window_summary(df):
    df = df.withColumn("window", (col("hour_of_day") / 3).cast("int") * 3)
    return df.groupBy("window").sum("total_ms_played") \
        .orderBy("window") \
        .withColumn("time_range", concat_ws("-", col("window"), (col("window") + 3) % 24)) \
        .select("time_range", col("sum(total_ms_played)").alias("total_ms_played"))

def day_summary(df):
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    # Convert day_of_week to int if needed
    df = df.withColumn("day_index", col("day_of_week").cast("int"))

    # Use when/otherwise chain for day names
    day_expr = when(col("day_index") == 0, lit("Sunday")) \
        .when(col("day_index") == 1, lit("Monday")) \
        .when(col("day_index") == 2, lit("Tuesday")) \
        .when(col("day_index") == 3, lit("Wednesday")) \
        .when(col("day_index") == 4, lit("Thursday")) \
        .when(col("day_index") == 5, lit("Friday")) \
        .when(col("day_index") == 6, lit("Saturday")) \
        .otherwise(lit("Sunday"))

    return df.withColumn("day_name", day_expr) \
             .select(col("day_name").alias("day"), col("total_ms_played")) \
             .orderBy("day_index")


def song_length_summary(df):
    return df.withColumn("month", col("month_year")) \
             .select("month", col("avg_song_length_sec").cast("double")) \
             .orderBy("month")

# Load tables
weekly_top_songs = spark.read.jdbc(db_url, "weekly_top_songs", properties=mysql_properties)
weekly_top_artists = spark.read.jdbc(db_url, "weekly_top_artists", properties=mysql_properties)
yearly_listen_analysis = spark.read.jdbc(db_url, "yearly_listen_analysis", properties=mysql_properties)
hour_distribution = spark.read.jdbc(db_url, "hour_distribution_trends", properties=mysql_properties)
day_distribution = spark.read.jdbc(db_url, "day_distribution_trends", properties=mysql_properties)
song_length_trends = spark.read.jdbc(db_url, "song_length_trends", properties=mysql_properties)

# Generate and show insights
print("\n🎵 Top 10 Songs for Latest Week:")
get_top10(weekly_top_songs, "track_name").show(truncate=False)

print("\n🎤 Top 10 Artists for Latest Week:")
get_top10(weekly_top_artists, "artist_name").show(truncate=False)

print("\n🕒 Listening Hours (Most Recent Year):")
latest_year_df = yearly_listen_analysis.orderBy(col("year").desc()).limit(1)
latest_year_df.selectExpr("concat('You listened for ', yearly_listen_hours, ' hours in ', year) as summary").show(truncate=False)

print("\n⏰ Listening by Time Window (Hours):")
hour_window_summary(hour_distribution).show(truncate=False)

print("\n📅 Listening by Day:")
day_summary(day_distribution).show(truncate=False)

print("\n📈 Monthly Avg Listen Time Per Song:")
song_length_summary(song_length_trends).show(truncate=False)

spark.stop()
