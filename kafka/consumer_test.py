from kafka import KafkaConsumer
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    'song-plays',  # Topic
    group_id='music-trends-group',
    bootstrap_servers='localhost:9092',  # Replace with your Kafka broker
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  # Deserialize JSON messages
)

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("MusicTrendsConsumer") \
    .getOrCreate()

# Create an empty list to accumulate messages
messages = []

# Poll the Kafka Consumer for messages
for message in consumer:
    print(f"Received message: {message.value}")
    messages.append(message.value)
    
    # Optionally, process the message here or send it directly to Spark
    # For now, we will simulate Spark streaming by accumulating and processing messages after collection
    
    if len(messages) > 100:  # Process every 100 messages (you can adjust this logic)
        # Convert the accumulated messages into a Spark DataFrame
        df = spark.read.json(spark.sparkContext.parallelize(messages))
        
        # Perform some transformations on the DataFrame
        # Example: Count the most played songs by hour
        df_with_timestamp = df.withColumn("timestamp", col("timestamp").cast("timestamp"))
        df_by_hour = df_with_timestamp.groupBy(
            window(col("timestamp"), "1 hour").alias("hour_window"),
            "song_id"
        ).count().orderBy("hour_window")

        # Show the result (this would be in your Spark job's output)
        df_by_hour.show()

        # Clear the message buffer
        messages = []

# This is a simple implementation; in a real-world scenario, you'd likely use
# structured streaming to process messages in real-time.
