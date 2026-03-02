import pandas as pd
import streamlit as st
import numpy as np

from src.db import get_recent_detections, get_stats
from src.embedder import LogEmbedder
from src.vector_store import VectorStore
from src.anomaly_detection import compute_threshold, is_anomalous
from src.explanation_engine import explain
from config import BASELINE_PATH, TEXT_BASELINE_PATH, THRESHOLD_PERCENTILE


st.set_page_config(
    page_title="Log Anomaly Dashboard",
    layout="wide",
)

st.title("Log Anomaly Dashboard")

# Sidebar controls
st.sidebar.header("Filters")
window_minutes = st.sidebar.selectbox(
    "Stats window",
    options=[15, 60, 240, 1440],
    index=1,
    format_func=lambda m: f"{m} min" if m < 60 else f"{m // 60} h",
)
limit = st.sidebar.slider("Recent rows", min_value=50, max_value=1000, value=200, step=50)
status_filter = st.sidebar.multiselect(
    "Status filter",
    options=["ANOMALY", "NORMAL"],
    default=["ANOMALY", "NORMAL"],
)

# KPIs
stats = get_stats(last_minutes=window_minutes)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Events (window)", stats["total"])
col2.metric("Anomalies (window)", stats["anomalies"])
col3.metric("Anomaly rate", f"{stats['anomaly_rate'] * 100:.2f}%")
avg_score_display = f"{stats['avg_score']:.4f}" if stats["avg_score"] is not None else "—"
col4.metric("Avg anomaly score", avg_score_display)

st.markdown("---")

# Recent detections table
records = get_recent_detections(limit=limit)
if not records:
    st.info("No detections recorded yet. Start the Kafka consumer and let it run for a bit.")
else:
    df = pd.DataFrame(records)

    if status_filter:
        df = df[df["status"].isin(status_filter)]

    # Shorten log text for table view
    df_display = df.copy()
    df_display["log_preview"] = df_display["log_text"].str.slice(0, 120)

    st.subheader("Recent detections")
    st.dataframe(
        df_display[
            ["id", "timestamp", "status", "score", "similarity", "source", "label", "log_preview"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Details")
    selected_id = st.selectbox(
        "Select detection ID for full details",
        options=df["id"].tolist(),
        format_func=lambda x: f"#{x}",
    )

    if selected_id is not None:
        row = df[df["id"] == selected_id].iloc[0]
        st.write(f"**Timestamp**: {row['timestamp']}")
        st.write(f"**Status**: {row['status']}")
        st.write(f"**Score**: {row['score']:.4f}")
        st.write(f"**Similarity**: {row['similarity']:.4f}")
        st.write(f"**Source**: {row['source']}")
        st.write(f"**Label**: {row.get('label')}")
        st.markdown("**Log text**")
        st.code(row["log_text"])


@st.cache_resource
def _load_hdfs_model_and_store():
    embedder = LogEmbedder()
    store = VectorStore(index_name="logs_index")
    return embedder, store


@st.cache_resource
def _load_text_model_and_store():
    embedder = LogEmbedder()
    store = VectorStore(index_name="logs_index_text")
    return embedder, store


@st.cache_resource
def _load_hdfs_baseline():
    sims = np.load(BASELINE_PATH)
    mean = float(np.mean(sims))
    std = float(np.std(sims))
    perc_threshold = float(
        compute_threshold(
            sims,
            method="percentile",
            value=THRESHOLD_PERCENTILE,
        )
    )
    # More conservative, stats-based threshold for explanations
    stat_threshold = float(mean - 2 * std)
    return sims, mean, std, perc_threshold, stat_threshold


@st.cache_resource
def _load_text_baseline():
    sims = np.load(TEXT_BASELINE_PATH)
    mean = float(np.mean(sims))
    std = float(np.std(sims))
    perc_threshold = float(
        compute_threshold(
            sims,
            method="percentile",
            value=THRESHOLD_PERCENTILE,
        )
    )
    stat_threshold = float(mean - 2 * std)
    return sims, mean, std, perc_threshold, stat_threshold


st.markdown("---")
st.subheader("Explain a specific log")

log_type = st.radio(
    "Log type",
    options=["HDFS features (CSV)", "Text log (system)"],
    index=1,
)

input_log = st.text_area(
    "Paste a log line to analyse",
    height=120,
    placeholder="Example: INFO Block 123 replicated successfully on node 5 ...",
)

if st.button("Analyse log"):
    if not input_log.strip():
        st.warning("Please enter a non-empty log line.")
    else:
        if log_type == "HDFS features (CSV)":
            embedder, store = _load_hdfs_model_and_store()
            _, mean, std, perc_threshold, stat_threshold = _load_hdfs_baseline()
        else:
            embedder, store = _load_text_model_and_store()
            _, mean, std, perc_threshold, stat_threshold = _load_text_baseline()

        vec = embedder.encode(input_log)
        results = store.query(vec, top_k=5)

        if not results:
            st.error("No neighbours found in the index. Run `--build_index` and start the consumer first.")
        else:
            similarities = [r["similarity"] for r in results]
            mean_similarity = float(sum(similarities) / len(similarities))
            # Use a stricter, stats-based threshold here to avoid over-flagging
            anomalous = is_anomalous(mean_similarity, stat_threshold)
            explanation_text = explain(mean_similarity, mean, std)

            st.write(f"**Status**: {'ANOMALY' if anomalous else 'NORMAL'}")
            st.write(f"**Mean similarity**: {mean_similarity:.4f}")
            st.write(f"**Threshold (percentile)**: {perc_threshold:.4f}")
            st.write(f"**Threshold (mean-2σ)**: {stat_threshold:.4f}")
            st.write(f"**Explanation**: {explanation_text}")


