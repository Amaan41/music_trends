Instructions
Prerequisites
Python 3.7+

Kafka & Zookeeper running locally or in Docker

Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
🧪 Running Kafka Scripts
1. Start Zookeeper and Kafka

bash
Copy
Edit
# Example using Kafka locally installed
zookeeper-server-start.sh config/zookeeper.properties
kafka-server-start.sh config/server.properties
Or using Docker (if you provide a docker-compose.yml):

bash
Copy
Edit
docker-compose up
2. Create Kafka Topic (if needed)

bash
Copy
Edit
kafka-topics.sh --create --topic music-logs --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
3. Run Producer

bash
Copy
Edit
python kafka/producer.py
4. Run Consumer

bash
Copy
Edit
python kafka/consumer_test.py
