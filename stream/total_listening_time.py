from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, sum, date_format
from pyspark.sql.types import *
import mysql.connector

# 1. Create Spark session
spark = SparkSession.builder \
    .appName("MonthlyListeningTime") \
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

# 5. Aggregate total listening time by month
agg_df = df_parsed.withWatermark("ts", "30 minutes") \
    .groupBy(date_format(col("ts"), "yyyy-MM").alias("month_year")) \
    .agg(sum("ms_played").alias("total_ms_played"))

# 6. Function to write to MySQL with upsert logic
def write_to_mysql(batch_df, batch_id):
    import pandas as pd

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

        insert_query = """
        INSERT INTO monthly_listening_time (month_year, total_ms_played)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE total_ms_played = VALUES(total_ms_played)
        """

        records = [
            (row["month_year"], int(row["total_ms_played"]))
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

# 7. Format data for monthly listening time storage
agg_df = agg_df.select("month_year", "total_ms_played")

# 8. Start the stream and write results to MySQL
query = agg_df.writeStream \
    .foreachBatch(write_to_mysql) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/monthly_listening_time") \
    .start()

query.awaitTermination()

