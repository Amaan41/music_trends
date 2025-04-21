import subprocess

# Path to MySQL connector JAR
mysql_jar_path = "/Users/mehenazasghar/Downloads/mysql-connector-j-9.3.0/mysql-connector-j-9.3.0.jar"

# Spark submit command base
spark_base_cmd = [
    "spark-submit",
    "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,org.apache.kafka:kafka-clients:3.5.1",
    "--driver-class-path", mysql_jar_path,
    "--jars", mysql_jar_path
]

# List of consumer scripts
scripts = [
    "stream_consumer.py",
    "top_artist_consumer.py",
    "top_track_consumer.py",
    "total_songs_consumer.py",
    "total_listening_time.py"
]

# Start all consumers as subprocesses
processes = []
for script in scripts:
    print(f"Starting {script}...")
    cmd = spark_base_cmd + [script]
    proc = subprocess.Popen(cmd)
    processes.append(proc)

# Optional: Wait for all processes to complete (if you want to block until they’re done)
for proc in processes:
    proc.wait()
