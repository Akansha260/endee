import argparse
import uuid
import os
import numpy as np
import time

from src.embedder import LogEmbedder
from src.vector_store import VectorStore
from src.preprocess import load_hdfs_data
from src.cluster import cluster_results
from src.synthetic_generator import inject_anomaly

TRACE_PATH = "data/raw/Event_traces.csv"
BASELINE_PATH = "outputs/baseline.txt"


def build_index():
    embedder = LogEmbedder()
    store = VectorStore()

    data = load_hdfs_data(TRACE_PATH, limit=5000)
    normal_data = data[data["Label"] == "Success"]

    print(f"Indexing {len(normal_data)} normal traces...")

    for _, row in normal_data.iterrows():
        vec = embedder.encode(str(row["Features"]))
        store.upsert(
            str(uuid.uuid4()),
            vec,
            {
                "block_id": row["BlockId"],
                "label": row["Label"]
            }
        )

    print("Indexing complete.")
    print("Computing baseline similarity...")

    similarities = []

    for _, row in normal_data.sample(200).iterrows():
        vec = embedder.encode(str(row["Features"]))
        results = store.query(vec, top_k=1)
        similarities.append(results[0]["similarity"])

    baseline_mean = np.mean(similarities)
    baseline_std = np.std(similarities)

    print(f"Baseline Mean: {baseline_mean}")
    print(f"Baseline Std: {baseline_std}")

    os.makedirs("outputs", exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        f.write(f"{baseline_mean},{baseline_std}")

    print("Baseline saved.")


def load_baseline():
    if not os.path.exists(BASELINE_PATH):
        raise FileNotFoundError(
            "Baseline not found. Run --build_index first."
        )

    with open(BASELINE_PATH, "r") as f:
        mean, std = f.read().split(",")

    return float(mean), float(std)


def test_anomalies():
    import time

    data = load_hdfs_data(TRACE_PATH, limit=5000)

    embedder = LogEmbedder()
    store = VectorStore()

    baseline_mean, baseline_std = load_baseline()
    threshold = baseline_mean - 2 * baseline_std

    print(f"Using threshold: {threshold}")

    fail_data = data[data["Label"] == "Fail"]

    correct = 0
    total = len(fail_data)

    total_query_time = 0
    total_embed_time = 0

    start_eval = time.time()

    for _, row in fail_data.iterrows():

        # --- Embedding timing ---
        t0 = time.time()
        vec = embedder.encode(str(row["Features"]))
        t1 = time.time()
        total_embed_time += (t1 - t0)

        # --- Query timing ---
        q0 = time.time()
        results = store.query(vec, top_k=5)
        q1 = time.time()
        total_query_time += (q1 - q0)

        top_similarity = results[0]["similarity"]

        anomaly_flag = top_similarity < threshold

        if anomaly_flag:
            correct += 1

    end_eval = time.time()

    detection_rate = correct / total if total > 0 else 0

    print("\n=== Anomaly Detection Evaluation ===")
    print(f"Total Fail Cases: {total}")
    print(f"Detected: {correct}")
    print(f"Detection Rate: {round(detection_rate, 4)}")

    # -------- False Positive Evaluation --------
    normal_sample = data[data["Label"] == "Success"].sample(200)

    false_positive = 0

    for _, row in normal_sample.iterrows():
        vec = embedder.encode(str(row["Features"]))
        results = store.query(vec, top_k=1)
        top_similarity = results[0]["similarity"]

        if top_similarity < threshold:
            false_positive += 1

    fp_rate = false_positive / 200

    print(f"False Positive Rate (200 normals): {round(fp_rate, 4)}")

    # -------- Performance Metrics --------
    total_eval_time = end_eval - start_eval

    avg_embed_latency = total_embed_time / total
    avg_query_latency = total_query_time / total
    throughput = total / total_eval_time

    print("\n=== Performance Metrics ===")
    print(f"Average Embedding Latency: {round(avg_embed_latency * 1000, 4)} ms")
    print(f"Average Query Latency: {round(avg_query_latency * 1000, 4)} ms")
    print(f"Total Evaluation Time: {round(total_eval_time, 4)} sec")
    print(f"Throughput: {round(throughput, 2)} queries/sec")

def test_synthetic_anomalies():
    data = load_hdfs_data(TRACE_PATH, limit=5000)

    embedder = LogEmbedder()
    store = VectorStore()

    baseline_mean, baseline_std = load_baseline()
    threshold = baseline_mean - 2 * baseline_std

    normal_data = data[data["Label"] == "Success"].sample(200)

    detected = 0
    total = len(normal_data)

    for _, row in normal_data.iterrows():
        original_seq = str(row["Features"])
        synthetic_seq = inject_anomaly(original_seq)

        vec = embedder.encode(synthetic_seq)
        results = store.query(vec, top_k=1)

        top_similarity = results[0]["similarity"]

        if top_similarity < threshold:
            detected += 1

    detection_rate = detected / total

    print("\n=== Synthetic Anomaly Evaluation ===")
    print(f"Total Synthetic Cases: {total}")
    print(f"Detected: {detected}")
    print(f"Detection Rate: {round(detection_rate, 4)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--build_index", action="store_true")
    parser.add_argument("--test_anomalies", action="store_true")
    parser.add_argument("--generate_synthetic", action="store_true")

    args = parser.parse_args()

    if args.build_index:
        build_index()
    elif args.test_anomalies:
        test_anomalies()
    elif args.generate_synthetic:
        test_synthetic_anomalies()
    else:
        print("Use --build_index or --test_anomalies")