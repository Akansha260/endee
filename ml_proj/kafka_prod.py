import time
import os
import json
import signal
import sys
import pandas as pd
from kafka import KafkaProducer
from src.synthetic_generator import inject_anomaly

# ==============================
# Kafka Configuration
# ==============================

KAFKA_BROKER = "localhost:9092"
TOPIC = "logs_stream"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
    acks="all",              # strongest durability guarantee
    retries=5,               # retry on transient failures
    linger_ms=5,             # small batching for efficiency
    enable_idempotence=True  # avoid duplicate sends
)

# ==============================
# Graceful Shutdown
# ==============================

def shutdown_handler(sig, frame):
    print("\nFlushing pending messages...")
    producer.flush()
    producer.close()
    print("Producer closed cleanly.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)

# ==============================
# Load Dataset
# ==============================

TRACE_PATH = "data/raw/Event_traces.csv"
data = pd.read_csv(TRACE_PATH)

USE_SYNTHETIC = os.getenv("USE_SYNTHETIC", "true").lower() == "true"

# ==============================
# Stream Logs
# ==============================

for _, row in data.iterrows():
    log_entry = str(row["Features"])
    label = row["Label"]

    # Inject anomaly into successful logs (controlled drift simulation)
    if USE_SYNTHETIC and label == "Success":
        log_entry = inject_anomaly(log_entry)

    # Embedding-ready structure
    message = {
        "text": f"Features: {log_entry} | Label: {label}",
        "metadata": {
            "label": label
        }
    }

    try:
        producer.send(
            TOPIC,
            key=label,        # ensures same label stays ordered
            value=message
        )
        print(f"Sent: {label} | {log_entry[:60]}...")
        time.sleep(0.01)

    except Exception as e:
        print("Failed to send message:", e)

# ==============================
# Final Flush
# ==============================

producer.flush()
producer.close()
print("All logs sent successfully.")
