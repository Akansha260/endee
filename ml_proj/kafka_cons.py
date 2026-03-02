import json
import time
import numpy as np
from kafka import KafkaConsumer

from src.embedder import LogEmbedder
from src.vector_store import VectorStore
from src.anomaly_detection import compute_threshold, is_anomalous
from src.db import insert_batch as insert_detections_batch
from src.metrics import METRICS
from src.db import insert_batch as insert_detections_batch

# ==============================
# CONFIG
# ==============================

KAFKA_BROKER = "localhost:9092"
TOPIC = "logs_stream"
GROUP_ID = "log_consumer_group"
BATCH_SIZE = 32

BASELINE_PATH = "outputs/baseline.npy"

# ==============================
# LOAD BASELINE THRESHOLD
# ==============================

baseline_similarities = np.load(BASELINE_PATH)
mean_sim = float(np.mean(baseline_similarities))
std_sim = float(np.std(baseline_similarities))

perc_threshold = float(
    compute_threshold(
        baseline_similarities,
        method="percentile",
        value=5,
    )
)
stat_threshold = float(mean_sim - 2 * std_sim)

# Use the more conservative (higher) of the two thresholds
threshold = max(perc_threshold, stat_threshold)

print(
    "Using anomaly thresholds: "
    f"percentile={perc_threshold:.6f}, "
    f"mean-2σ={stat_threshold:.6f}, "
    f"effective={threshold:.6f}"
)

# ==============================
# INITIALIZE COMPONENTS
# ==============================

embedder = LogEmbedder()
store = VectorStore()

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,  # manual commit
    group_id=GROUP_ID,
    max_poll_records=100
)

print(" Listening for logs...")

# ==============================
# STREAM PROCESSING LOOP
# ==============================

buffer = []

while True:
    records = consumer.poll(timeout_ms=1000)

    for tp, messages in records.items():
        for message in messages:
            buffer.append(message)

    if len(buffer) >= BATCH_SIZE:
        try:
            start_time = time.time()

            texts = []
            metadata_batch = []

            # Extract data
            for msg in buffer:
                log = msg.value
                text = log["text"]
                metadata = log.get("metadata", {})

                texts.append(text)
                metadata_batch.append(metadata)

            # ----------------------
            # 1️⃣ Batch Embedding
            # ----------------------
            vectors = embedder.encode_batch(texts)

            # ----------------------
            # 2️⃣ Batch Vector Query
            # ----------------------
            results = store.query_batch(vectors, top_k=5)

            # ----------------------
            # 3️⃣ Evaluate Anomalies & persist
            # ----------------------
            detections_payload = []
            batch_anomalies = 0

            normals_vectors = []
            normals_metadata = []

            for i, res in enumerate(results):

                if not res:
                    # Cold start case: no neighbors yet, treat as fully normal
                    mean_similarity = 1.0
                else:
                    similarities = [
                        r["similarity"] for r in res
                    ]
                    mean_similarity = sum(similarities) / len(similarities)

                anomalous = is_anomalous(
                    mean_similarity,
                    threshold
                )

                status = "ANOMALY" if anomalous else "NORMAL"
                if anomalous:
                    batch_anomalies += 1
                score = 1.0 - mean_similarity

                print(
                    f"{texts[i][:60]} | "
                    f"Score: {mean_similarity:.6f} | "
                    f"{status}"
                )

                meta = metadata_batch[i] if i < len(metadata_batch) else {}
                label = meta.get("label")

                detections_payload.append(
                    {
                        "log_text": texts[i],
                        "label": label,
                        "similarity": float(mean_similarity),
                        "score": float(score),
                        "status": status,
                        "source": meta.get("source", "kafka"),
                    }
                )

                # Keep the index "clean": only grow it with behaviour
                # currently considered NORMAL, to avoid contaminating
                # the reference set with anomalies.
                if status == "NORMAL":
                    normals_vectors.append(vectors[i])
                    normals_metadata.append(meta)

            # Persist detections for dashboarding/analysis
            insert_detections_batch(detections_payload)

            # ----------------------
            # 4️⃣ Insert normals into Memory
            # ----------------------
            if normals_vectors:
                store.insert_batch(normals_vectors, normals_metadata)

            # ----------------------
            # 5️⃣ Commit Offsets
            # ----------------------
            consumer.commit()

            end_time = time.time()
            batch_latency = end_time - start_time

            METRICS.record_batch(
                num_msgs=len(buffer),
                batch_latency_sec=batch_latency,
                num_anomalies=batch_anomalies,
            )

            snapshot = METRICS.snapshot()
            print(
                f"Batch processed in {batch_latency:.4f} sec | "
                f"msgs_total={snapshot['total_messages']} "
                f"anomalies_total={snapshot['total_anomalies']} "
                f"anomaly_rate={snapshot['anomaly_rate']:.4f}\n"
            )

            buffer.clear()

        except Exception as e:
            print("Batch processing failed:", e)
            print("Offsets not committed. Retrying...")
