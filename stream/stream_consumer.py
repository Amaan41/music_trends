from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, window, avg
from pyspark.sql.types import *
import mysql.connector

spark = SparkSession.builder \
    .appName("SpotifyStreamProcessing") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

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
    .option("subscribe", "streaming-stats") \
    .load()

df_parsed = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")).select("data.*")

df_parsed = df_parsed.withColumn("ts", to_timestamp(col("ts")))

agg_df = df_parsed.withWatermark("ts", "30 minutes") \
    .groupBy(window(col("ts"), "30 minutes"), col("track_name")) \
    .agg(avg("ms_played").alias("avg_ms_played"))

# Flag to indicate whether to clear the table
clear_table_flag = True

# Function to write data to MySQL
def write_to_mysql(batch_df, batch_id):
    global clear_table_flag
    
    # Only clear the table for the first batch
    if clear_table_flag:
        print("Clearing table and writing batch data to MySQL...")
        
        # Connect to MySQL
        try:
            conn = mysql.connector.connect(
                host="localhost",
                database="spotifydb",
                user="root",
                password="zayaan@06"
            )
            cursor = conn.cursor()

            # Clear the existing data in the table before inserting new data
            cursor.execute("DELETE FROM streaming_stats")
            conn.commit()

            # Set flag to False so the table is not cleared again
            clear_table_flag = False

            # Write the new batch data to MySQL
            batch_df.write \
                .format("jdbc") \
                .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
                .option("driver", "com.mysql.cj.jdbc.Driver") \
                .option("dbtable", "streaming_stats") \
                .option("user", "root") \
                .option("password", "zayaan@06") \
                .mode("append") \
                .save()

            cursor.close()
            conn.close()

        except mysql.connector.Error as e:
            print(f"Error while connecting to MySQL: {e}")
            raise  # Re-raise the exception to ensure the error is logged
    else:
        # For subsequent batches, simply append the data to the table without clearing it
        print("Writing batch data to MySQL without clearing table...")
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
            .option("driver", "com.mysql.cj.jdbc.Driver") \
            .option("dbtable", "streaming_stats") \
            .option("user", "root") \
            .option("password", "zayaan@06") \
            .mode("append") \
            .save()

agg_df = agg_df.selectExpr(
    "window.start as window_start",
    "window.end as window_end",
    "track_name",
    "avg_ms_played"
)

# Start the query to write to MySQL using foreachBatch
query = agg_df.writeStream \
    .foreachBatch(write_to_mysql) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/spotify_stats") \
    .start()

query.awaitTermination()

