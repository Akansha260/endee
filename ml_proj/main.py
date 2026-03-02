# import argparse
# import uuid
# import os
# import numpy as np
# import time
#
# from src.embedder import LogEmbedder
# from src.vector_store import VectorStore
# from src.preprocess import load_hdfs_data
# from src.cluster import cluster_results
# from src.synthetic_generator import inject_anomaly
#
# TRACE_PATH = "data/raw/Event_traces.csv"
# BASELINE_PATH = "outputs/baseline.txt"
#
#
# def build_index():
#     embedder = LogEmbedder()
#     store = VectorStore()
#
#     data = load_hdfs_data(TRACE_PATH, limit=5000)
#     normal_data = data[data["Label"] == "Success"]
#
#     print(f"Indexing {len(normal_data)} normal traces...")
#
#     for _, row in normal_data.iterrows():
#         vec = embedder.encode(str(row["Features"]))
#         store.upsert(
#             str(uuid.uuid4()),
#             vec,
#             {
#                 "block_id": row["BlockId"],
#                 "label": row["Label"]
#             }
#         )
#
#     print("Indexing complete.")
#     print("Computing baseline similarity...")
#
#     similarities = []
#
#     for _, row in normal_data.sample(200).iterrows():
#         vec = embedder.encode(str(row["Features"]))
#         results = store.query(vec, top_k=1)
#         similarities.append(results[0]["similarity"])
#
#     baseline_mean = np.mean(similarities)
#     baseline_std = np.std(similarities)
#
#     print(f"Baseline Mean: {baseline_mean}")
#     print(f"Baseline Std: {baseline_std}")
#
#     os.makedirs("outputs", exist_ok=True)
#     with open(BASELINE_PATH, "w") as f:
#         f.write(f"{baseline_mean},{baseline_std}")
#
#     print("Baseline saved.")
#
#
# def load_baseline():
#     if not os.path.exists(BASELINE_PATH):
#         raise FileNotFoundError(
#             "Baseline not found. Run --build_index first."
#         )
#
#     with open(BASELINE_PATH, "r") as f:
#         mean, std = f.read().split(",")
#
#     return float(mean), float(std)
#
#
# def test_anomalies():
#     import time
#
#     data = load_hdfs_data(TRACE_PATH, limit=5000)
#
#     embedder = LogEmbedder()
#     store = VectorStore()
#
#     baseline_mean, baseline_std = load_baseline()
#     threshold = baseline_mean - 2 * baseline_std
#
#     print(f"Using threshold: {threshold}")
#
#     fail_data = data[data["Label"] == "Fail"]
#
#     correct = 0
#     total = len(fail_data)
#
#     total_query_time = 0
#     total_embed_time = 0
#
#     start_eval = time.time()
#
#     for _, row in fail_data.iterrows():
#
#         # --- Embedding timing ---
#         t0 = time.time()
#         vec = embedder.encode(str(row["Features"]))
#         t1 = time.time()
#         total_embed_time += (t1 - t0)
#
#         # --- Query timing ---
#         q0 = time.time()
#         results = store.query(vec, top_k=5)
#         q1 = time.time()
#         total_query_time += (q1 - q0)
#
#         top_similarity = results[0]["similarity"]
#
#         anomaly_flag = top_similarity < threshold
#
#         if anomaly_flag:
#             correct += 1
#
#     end_eval = time.time()
#
#     detection_rate = correct / total if total > 0 else 0
#
#     print("\n=== Anomaly Detection Evaluation ===")
#     print(f"Total Fail Cases: {total}")
#     print(f"Detected: {correct}")
#     print(f"Detection Rate: {round(detection_rate, 4)}")
#
#     # -------- False Positive Evaluation --------
#     normal_sample = data[data["Label"] == "Success"].sample(200)
#
#     false_positive = 0
#
#     for _, row in normal_sample.iterrows():
#         vec = embedder.encode(str(row["Features"]))
#         results = store.query(vec, top_k=1)
#         top_similarity = results[0]["similarity"]
#
#         if top_similarity < threshold:
#             false_positive += 1
#
#     fp_rate = false_positive / 200
#
#     print(f"False Positive Rate (200 normals): {round(fp_rate, 4)}")
#
#     # -------- Performance Metrics --------
#     total_eval_time = end_eval - start_eval
#
#     avg_embed_latency = total_embed_time / total
#     avg_query_latency = total_query_time / total
#     throughput = total / total_eval_time
#
#     print("\n=== Performance Metrics ===")
#     print(f"Average Embedding Latency: {round(avg_embed_latency * 1000, 4)} ms")
#     print(f"Average Query Latency: {round(avg_query_latency * 1000, 4)} ms")
#     print(f"Total Evaluation Time: {round(total_eval_time, 4)} sec")
#     print(f"Throughput: {round(throughput, 2)} queries/sec")
#
# def test_synthetic_anomalies():
#     data = load_hdfs_data(TRACE_PATH, limit=5000)
#
#     embedder = LogEmbedder()
#     store = VectorStore()
#
#     baseline_mean, baseline_std = load_baseline()
#     threshold = baseline_mean - 2 * baseline_std
#
#     normal_data = data[data["Label"] == "Success"].sample(200)
#
#     detected = 0
#     total = len(normal_data)
#
#     for _, row in normal_data.iterrows():
#         original_seq = str(row["Features"])
#         synthetic_seq = inject_anomaly(original_seq)
#
#         vec = embedder.encode(synthetic_seq)
#         results = store.query(vec, top_k=1)
#
#         top_similarity = results[0]["similarity"]
#
#         if top_similarity < threshold:
#             detected += 1
#
#     detection_rate = detected / total
#
#     print("\n=== Synthetic Anomaly Evaluation ===")
#     print(f"Total Synthetic Cases: {total}")
#     print(f"Detected: {detected}")
#     print(f"Detection Rate: {round(detection_rate, 4)}")
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#
#     parser.add_argument("--build_index", action="store_true")
#     parser.add_argument("--test_anomalies", action="store_true")
#     parser.add_argument("--generate_synthetic", action="store_true")
#
#     args = parser.parse_args()
#
#     if args.build_index:
#         build_index()
#     elif args.test_anomalies:
#         test_anomalies()
#     elif args.generate_synthetic:
#         test_synthetic_anomalies()
#     else:
#         print("Use --build_index or --test_anomalies")

import argparse
import uuid
import os
import numpy as np
import pandas as pd
import time
from sklearn.metrics import roc_curve, auc

from src.embedder import LogEmbedder
from src.vector_store import VectorStore
from src.preprocess import load_hdfs_data
from src.anomaly_detection import compute_threshold, is_anomalous
from src.explanation_engine import explain
from src.synthetic_generator import inject_anomaly

from config import TRACE_PATH, BASELINE_PATH, TEXT_BASELINE_PATH


def build_index():
    embedder = LogEmbedder()
    store = VectorStore()

    data = load_hdfs_data(TRACE_PATH, limit=5000)

    normal_data = data[data["Label"] == "Success"]
    train_normals = normal_data.sample(frac=0.8, random_state=42)
    test_normals = normal_data.drop(train_normals.index)

    print(f"Indexing {len(train_normals)} training normal traces...")

    for _, row in train_normals.iterrows():
        vec = embedder.encode(str(row["Features"]))
        store.insert(
            vec,
            {"label": row["Label"]}
        )

    print("Indexing complete.")
    print("Computing baseline from held-out normals...")

    similarities = []

    for _, row in test_normals.sample(200).iterrows():
        vec = embedder.encode(str(row["Features"]))
        results = store.query(vec, top_k=1)
        similarities.append(results[0]["similarity"])

    similarities = np.array(similarities)
    threshold = compute_threshold(similarities, method="percentile", value=5)

    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    np.save(BASELINE_PATH, similarities)

    print(f"Threshold (5th percentile): {threshold}")
    print("Baseline saved.")


def build_text_index(text_log_path: str):
    """
    Build a separate index + baseline for plain text logs
    (e.g. Windows CBS logs extracted to data/text_normals.log).
    """
    if not os.path.exists(text_log_path):
        raise FileNotFoundError(f"text_log_path not found: {text_log_path}")

    embedder = LogEmbedder()
    # Separate index for text logs
    store = VectorStore(index_name="logs_index_text")

    with open(text_log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        raise ValueError("No non-empty lines found in text_log_path")

    print(f"Loaded {len(lines)} text log lines for baseline.")

    # Simple 80/20 split
    split_idx = int(0.8 * len(lines))
    train_lines = lines[:split_idx]
    test_lines = lines[split_idx:]

    print(f"Indexing {len(train_lines)} training text normals...")

    for line in train_lines:
        vec = embedder.encode(line)
        store.insert(vec, {"source": "text"})

    print("Indexing complete for text logs.")
    print("Computing baseline from held-out text normals...")

    similarities = []

    for line in test_lines:
        vec = embedder.encode(line)
        results = store.query(vec, top_k=1)
        if not results:
            continue
        similarities.append(results[0]["similarity"])

    if not similarities:
        raise ValueError("No similarities computed for text baseline.")

    similarities = np.array(similarities)
    threshold = compute_threshold(similarities, method="percentile", value=5)

    os.makedirs(os.path.dirname(TEXT_BASELINE_PATH), exist_ok=True)
    np.save(TEXT_BASELINE_PATH, similarities)

    print(f"[TEXT] Threshold (5th percentile): {threshold}")
    print(f"[TEXT] Baseline saved to {TEXT_BASELINE_PATH}.")


def evaluate(use_synthetic=False):
    embedder = LogEmbedder()
    store = VectorStore()

    if not os.path.exists(BASELINE_PATH):
        raise FileNotFoundError("Run --build_index first.")

    baseline_similarities = np.load(BASELINE_PATH)
    threshold = compute_threshold(baseline_similarities,
                                  method="percentile",
                                  value=5)

    data = load_hdfs_data(TRACE_PATH, limit=5000)

    if use_synthetic:
        print("Injecting synthetic anomalies into normal logs...")

        normal_data = data[data["Label"] == "Success"].copy()

        # Create synthetic anomalies from normal logs
        synthetic = normal_data.copy()
        synthetic["Features"] = synthetic["Features"].apply(inject_anomaly)
        synthetic["Label"] = "Fail"  # mark injected as anomaly

        # Combine original normals + synthetic anomalies
        test_data = pd.concat([normal_data, synthetic]).reset_index(drop=True)

    else:
        test_data = data.copy()

    y_true = []
    y_scores = []
    similarities_eval = []
    latencies = []

    for _, row in test_data.iterrows():
        vec = embedder.encode(str(row["Features"]))

        t0 = time.time()
        results = store.query(vec, top_k=1)
        latency = time.time() - t0

        similarity = results[0]["similarity"]

        # For ROC we use an anomaly score (higher = more anomalous)
        y_scores.append(1 - similarity)
        similarities_eval.append(similarity)
        latencies.append(latency)

        y_true.append(1 if row["Label"] == "Fail" else 0)

    # ROC
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)

    predictions = [1 if is_anomalous(sim, threshold) else 0
                   for sim in similarities_eval]

    tp = sum((p == 1 and t == 1) for p, t in zip(predictions, y_true))
    fp = sum((p == 1 and t == 0) for p, t in zip(predictions, y_true))
    fn = sum((p == 0 and t == 1) for p, t in zip(predictions, y_true))
    tn = sum((p == 0 and t == 0) for p, t in zip(predictions, y_true))

    print("\n=== Evaluation Report ===")
    print(f"AUC: {round(roc_auc, 4)}")
    print(f"TP: {tp}  FP: {fp}")
    print(f"FN: {fn}  TN: {tn}")

    print(f"Recall: {round(tp / (tp + fn + 1e-9), 4)}")
    print(f"FPR: {round(fp / (fp + tn + 1e-9), 4)}")
    print(f"Avg Latency: {round(np.mean(latencies) * 1000, 3)} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--build_index", action="store_true")
    parser.add_argument(
        "--build_index_text",
        action="store_true",
        help="Build index + baseline for plain text logs",
    )
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument(
        "--text_log_path",
        type=str,
        default="data/text_normals.log",
        help="Path to normal text logs file (one line per log)",
    )

    args = parser.parse_args()

    if args.build_index:
        build_index()
    elif args.build_index_text:
        build_text_index(args.text_log_path)
    elif args.evaluate:
        evaluate(use_synthetic=args.synthetic)
    else:
        print("Use --build_index or --evaluate")