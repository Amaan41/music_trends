# Instructions

# Prerequisites

Python 3.7+

Kafka & Zookeeper running locally or in Docker

# Running Kafka Scripts
1. Start Zookeeper and Kafka

zookeeper-server-start.sh config/zookeeper.properties

OR

zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties

kafka-server-start.sh config/server.properties 

OR

kafka-server-start /opt/homebrew/etc/kafka/server.properties

2. Create Kafka Topic (if needed)

kafka-topics.sh --create --topic music-logs --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

3. Run Producer

python producer.py

4. Run Stream Processing Script

python stream/main_streaming_consumer.py

5. Run Batch Processing Script

python batch/batch_processing_main.py

6. Gather the final report

python batch/insights_report.py


