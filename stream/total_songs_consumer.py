from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, window, count
from pyspark.sql.types import *
import mysql.connector

# 1. Create Spark session
spark = SparkSession.builder \
    .appName("SongsPerWindow") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2. Define schema for incoming data
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

# 3. Read from Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "listen-time") \
    .load()

# 4. Parse and filter data where ms_played > 0
df_parsed = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")).select("data.*") \
    .withColumn("ts", to_timestamp(col("ts"))) \
    .filter(col("ms_played") > 0)

# 5. Aggregate songs per 30-minute window
agg_df = df_parsed.withWatermark("ts", "30 minutes") \
    .groupBy(window(col("ts"), "30 minutes")) \
    .agg(count("*").alias("total_songs"))

# 6. Format data to match table schema
agg_df = agg_df.selectExpr(
    "window.start as window_start",
    "window.end as window_end",
    "total_songs"
)
first_batch = True  # global flag to track first batch

def write_to_mysql(batch_df, batch_id):
    import pandas as pd
    global first_batch

    if batch_df.isEmpty():
        return

    batch_df_local = batch_df.toPandas()

    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="zayaan@06",
            database="spotifydb"
        )
        cursor = connection.cursor()

        # Clear table only on the first batch
        if first_batch:
            cursor.execute("DELETE FROM songs_per_window")
            connection.commit()
            first_batch = False  # turn off after first execution

        insert_query = """
        INSERT INTO songs_per_window (window_start, window_end, total_songs)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE total_songs = VALUES(total_songs)
        """

        records = [
            (
                row["window_start"].to_pydatetime(),
                row["window_end"].to_pydatetime(),
                int(row["total_songs"])
            )
            for _, row in batch_df_local.iterrows()
        ]

        cursor.executemany(insert_query, records)
        connection.commit()

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 8. Start query
query = agg_df.writeStream \
    .foreachBatch(write_to_mysql) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/songs_per_window") \
    .start()

query.awaitTermination()

