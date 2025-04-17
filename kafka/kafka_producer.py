import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

fake = Faker()

# Kafka config
KAFKA_TOPIC = "song-plays"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Sample genres
genres = ['pop', 'rock', 'hiphop', 'classical', 'jazz', 'electronic', 'country']

# Producer setup
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def generate_mock_play():
    return {
        "user_id": f"user_{random.randint(1, 50)}",
        "song_id": f"song_{random.randint(1, 100)}",
        "timestamp": datetime.utcnow().isoformat(),
        "genre": random.choice(genres)
    }

if __name__ == "__main__":
    print(f"Producing messages to topic `{KAFKA_TOPIC}`...")
    while True:
        message = generate_mock_play()
        producer.send(KAFKA_TOPIC, value=message)
        print(f"Sent: {message}")
        time.sleep(1)  # one play per second
