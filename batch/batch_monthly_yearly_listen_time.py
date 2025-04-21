from pyspark.sql import SparkSession
from pyspark.sql.functions import col, substring, year, month, sum as sum_
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("Monthly and Yearly Listen Time Analysis") \
    .getOrCreate()

# Database connection properties
db_properties = {
    "user": "root",
    "password": "zayaan@06",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# Read data from the monthly_listening_time table
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "monthly_listening_time") \
    .options(**db_properties) \
    .load()

# Extract year and month from month_year column
df = df.withColumn("year", substring(col("month_year"), 1, 4)) \
       .withColumn("month", substring(col("month_year"), 6, 2))

# Calculate total listen time per month in hours
monthly_listen_time = df.withColumn("listen_hours", col("total_ms_played") / 3600000)

# Calculate total listen time per year
yearly_listen_time = monthly_listen_time.groupBy("year") \
    .agg(sum_("total_ms_played").alias("yearly_ms_played")) \
    .withColumn("yearly_listen_hours", col("yearly_ms_played") / 3600000)

# Calculate month-over-month growth rate
window_spec = Window.orderBy("year", "month")
monthly_growth = monthly_listen_time.withColumn(
    "prev_month_ms", F.lag("total_ms_played", 1).over(window_spec)
).withColumn(
    "growth_rate", 
    F.when(col("prev_month_ms").isNotNull(), 
           ((col("total_ms_played") - col("prev_month_ms")) / col("prev_month_ms") * 100)
          ).otherwise(None)
)

# Save monthly data with growth metrics
monthly_growth.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "monthly_listen_analysis") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

# Save yearly data
yearly_listen_time.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/spotifydb") \
    .option("dbtable", "yearly_listen_analysis") \
    .options(**db_properties) \
    .mode("overwrite") \
    .save()

# Display the most recent 6 months of data
print("Recent 6 Months of Listening Data:")
monthly_growth.orderBy(col("year").desc(), col("month").desc()) \
    .select("year", "month", "listen_hours", "growth_rate") \
    .limit(6) \
    .show()

# Display yearly data
print("Yearly Listening Data:")
yearly_listen_time.orderBy("year") \
    .select("year", "yearly_listen_hours") \
    .show()

spark.stop()