import os

# Paths
TRACE_PATH = os.environ.get("TRACE_PATH", "data/raw/Event_traces.csv")
BASELINE_PATH = os.environ.get("BASELINE_PATH", "outputs/baseline.npy")
# Separate baseline for text logs (e.g. Windows CBS)
TEXT_BASELINE_PATH = os.environ.get("TEXT_BASELINE_PATH", "outputs/baseline_text.npy")
ANOMALIES_DB_PATH = os.environ.get("ANOMALIES_DB_PATH", "data/anomalies.db")
LOG_PATH_PATTERN = os.environ.get("LOG_PATH_PATTERN", "/var/log/hdfs/*.log")

# Kafka
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "logs_stream")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "log_consumer_group")

# Thresholding
THRESHOLD_PERCENTILE = float(os.environ.get("THRESHOLD_PERCENTILE", "5"))

