Instructions:

Prerequisites

Python 3.7+

Kafka & Zookeeper running locally or in Docker

# Running Kafka Scripts
1. Start Zookeeper and Kafka

zookeeper-server-start.sh config/zookeeper.properties
kafka-server-start.sh config/server.properties

2. Create Kafka Topic (if needed)
kafka-topics.sh --create --topic music-logs --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

3. Run Producer
python kafka/producer.py

4. Run Consumer
python kafka/consumer_test.py
