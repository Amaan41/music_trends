from kafka import KafkaProducer
import time
import pandas as pd
import json

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

df = pd.read_csv("../data/spotify_history.csv")  # Your large dataset

for index, row in df.iterrows():
    data = row.to_dict()
    producer.send('total_songs', data)
    time.sleep(0.2)  # simulate streaming

