# kafka/producer.py

import csv
import json
import time
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic_name = 'song-plays'
file_path = '../data/spotify_history.csv'  # Adjust if running from another directory

with open(file_path, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    print(f"Producing messages to topic `{topic_name}`...")

    for row in reader:
        message = {
            "ts": row["ts"],
            "platform": row["platform"],
            "ms_played": int(row["ms_played"]),
            "track_name": row["track_name"],
            "artist_name": row["artist_name"],
            "album_name": row["album_name"],
            "reason_start": row["reason_start"],
            "reason_end": row["reason_end"],
            "shuffle": row["shuffle"] == 'true',
            "skipped": row["skipped"] == 'true'
        }

        producer.send(topic_name, message)
        print("Sent:", message)
        time.sleep(1)  # simulate streaming one record at a time

producer.flush()
