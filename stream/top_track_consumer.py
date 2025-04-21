from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, window, count
from pyspark.sql.types import *
import mysql.connector

# Spark session
spark = SparkSession.builder \
    .appName("TopTrackByPlayCount") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Define schema
schema = StructType([
    StructField("ts", StringType()),
    StructField("platform", StringType()),
    StructField("ms_played", IntegerType()),
    StructField("track_name", StringType()),
    StructField("artist_name", StringType()),
    StructField("album_name", StringType()),
    StructField("reason_start", StringType()),
    StructField("reason_end", StringType()),
    StructField("shuffle", StringType()),
    StructField("skipped", StringType()),
])

# Read from Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "top10") \
    .load()

# Parse and clean data
df_parsed = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")).select("data.*") \
    .withColumn("ts", to_timestamp(col("ts"))) \
    .filter(col("ms_played") > 0)

# Aggregate: Count plays per track per sliding window
agg_df = df_parsed.withWatermark("ts", "30 minutes") \
    .groupBy(window(col("ts"), "30 minutes", "5 minutes"), col("track_name")) \
    .agg(count("*").alias("play_count"))

# Write to MySQL
clear_table_flag = True

def write_to_mysql(batch_df, batch_id):
    global clear_table_flag
    if batch_df.isEmpty():
        return

    if clear_table_flag:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                database="spotifydb",
                user="root",
                password="zayaan@06"
            )
            cursor = conn.cursor()
            cursor.execute("DELETE FROM top_track")
            conn.commit()
            clear_table_flag = False
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"MySQL Error: {e}")
            raise

    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number

    # Apply ranking logic here since batch_df is static
    window_spec = Window.partitionBy("window").orderBy(col("play_count").desc())

    top_tracks = batch_df.withColumn("rank", row_number().over(window_spec)) \
                         .filter(col("rank") == 1) \
                         .selectExpr(
                             "window.start as window_start",
                             "window.end as window_end",
                             "track_name",
                             "play_count"
                         )

    top_tracks.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("dbtable", "top_track") \
        .option("user", "root") \
        .option("password", "zayaan@06") \
        .mode("append") \
        .save()

# Start streaming query
query = agg_df.writeStream \
    .foreachBatch(write_to_mysql) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/top_track_count") \
    .start()

query.awaitTermination()

