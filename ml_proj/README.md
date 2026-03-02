# AI Pattern Investigator

### Real-Time Log Anomaly Detection Using Vector Retrieval

An end-to-end streaming anomaly detection system where a vector database acts as the semantic memory and decision engine.

Anomaly detection is reframed as a **similarity retrieval problem** instead of a classifier.

---

## 🎯 Core Idea

If a log embedding cannot retrieve sufficiently similar *normal* embeddings, it is considered anomalous.

The system stores **normal embeddings only**, and similarity acts as a confidence signal.

---

## 🏗 System Architecture<p align="center">

<img src="./architecture/sys_architecture.png" width="300"/>
</p>

---

## 🧠 Detection Logic

For each log:

1. Generate a 384-dimensional sentence embedding
2. Retrieve top-k nearest neighbors from normal embeddings
3. Compute cosine similarity
4. Compare against threshold derived from held-out normals
5. Flag as anomaly if similarity is below threshold

---

## 🔄 Operating Modes

### Offline Validation

* Build embedding index from normal HDFS logs
* Evaluate on labeled failure logs
* Measure ROC-AUC, recall, and false positive rate

### Real-Time Streaming

* Logs ingested via Kafka
* Embeddings generated in batches
* Vector similarity queried per log
* Decisions persisted to SQLite
* Sliding-window metrics tracked

---

## 📊 Performance Evaluation

### HDFS Trace Dataset (Real Failures)


| Metric                | Value          |
| --------------------- | -------------- |
| ROC-AUC               | 0.97           |
| Recall (Failure Logs) | 0.95           |
| False Positive Rate   | 0.013          |
| Vector Query Latency  | 6.5 ms per log |
| Embedding Dimension   | 384            |

These results indicate strong separability between normal and failure logs using similarity-based retrieval.

### Synthetic Anomaly Evaluation


| Metric               | Value          |
| -------------------- | -------------- |
| ROC-AUC              | 0.84           |
| Recall               | 0.68           |
| False Positive Rate  | 0.013          |
| Vector Query Latency | 6.7 ms per log |

Performance varied depending on semantic distance and vocabulary shift, highlighting sensitivity to distribution drift.

## 🔍 Explainability

Each anomaly includes:

* Top-k closest normal logs
* Similarity scores
* Distance from threshold

This enables **interpretable anomaly alerts** instead of black-box decisions.

---

## 🛠 Tech Stack

* Python
* Transformer-based sentence embeddings (384-dim)
* Endee Vector DB
* Apache Kafka
* Docker
* Streamlit

---

## 📌 Use Cases

* Distributed system monitoring
* Failure detection in logs
* DevOps anomaly tracking
* Security log analysis
* Behavioral drift detection

---

## 💡 Design Philosophy

This system reframes anomaly detection:

* **Not classification. Not reconstruction.**
* **Similarity-based confidence estimation over semantic memory.**
* Vector retrieval acts as the decision layer.

## ⚙️ Unified Setup Guide (Windows / macOS / Linux)

This section covers complete setup for any operating system in one place.

1️⃣ Prerequisites

Install the following:

Python 3.9 – 3.11 (must be added to PATH)

Git

Apache Kafka

2️⃣ Clone the Repository
git clone <your-repo-url>
cd <your-repo-folder>

3️⃣ Create Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
macOS / Linux
python3 -m venv venv
source venv/bin/activate

You should now see (venv) in your terminal.

4️⃣ Install Dependencies

If requirements.txt exists:

pip install -r requirements.txt

Otherwise install manually:

pip install sentence-transformers kafka-python streamlit pandas numpy scikit-learn
5️⃣ Kafka Setup

Download Kafka and extract it anywhere on your system.

Start Kafka
Windows
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
bin\windows\kafka-server-start.bat config\server.properties
macOS / Linux
bin/zookeeper-server-start.sh config/zookeeper.properties
bin/kafka-server-start.sh config/server.properties

If using Kafka 3.5+ (KRaft mode), only the broker needs to be started.

Keep Kafka running in the background.

6️⃣ Configure Environment Variables
Windows (PowerShell)
$env:KAFKA_BROKER="localhost:9092"
$env:KAFKA_TOPIC="logs_stream"
$env:KAFKA_GROUP_ID="log_consumer_group"

$env:TRACE_PATH="data/raw/Event_traces.csv"
$env:BASELINE_PATH="outputs/baseline.npy"
$env:TEXT_BASELINE_PATH="outputs/baseline_text.npy"
$env:ANOMALIES_DB_PATH="data/anomalies.db"
$env:LOG_PATH_PATTERN="C:/logs/*.log"
macOS / Linux
export KAFKA_BROKER=localhost:9092
export KAFKA_TOPIC=logs_stream
export KAFKA_GROUP_ID=log_consumer_group

export TRACE_PATH=data/raw/Event_traces.csv
export BASELINE_PATH=outputs/baseline.npy
export TEXT_BASELINE_PATH=outputs/baseline_text.npy
export ANOMALIES_DB_PATH=data/anomalies.db
export LOG_PATH_PATTERN="/var/log/*.log"

7️⃣ Build Offline Indexes (Required Before Streaming)
Build HDFS Index
python main.py --build_index

This:

Builds vector index of normal logs

Computes similarity distribution

Saves baseline.npy

Calibrates anomaly threshold

Build Text Log Index (Optional but Recommended)
python main.py --build_index_text --text_log_path data/text_normals.log

This saves baseline_text.npy.

8️⃣ Start Streaming Detection

Open a new terminal (activate venv again if needed).

Start Consumer
python kafka_cons.py
Start Producer (Replay CSV)
python kafka_prod.py --mode csv --trace_path data/raw/Event_traces.csv
Start Producer (Live Log Files)
python kafka_prod.py --mode file --log_pattern "<your-log-path-pattern>"

Example:

Windows → C:/logs/*.log

Linux → /var/log/*.log

9️⃣ Launch Dashboard
streamlit run dashboard.py

Open in browser:

http://localhost:8501

🔄 Recommended Startup Order

Start Kafka (and Zookeeper if required)

Build HDFS index

Build text index (optional)

Start consumer

Start producer

Launch dashboard

✅ Verify Setup

You should observe:

baseline.npy and optionally baseline_text.npy created

data/anomalies.db created

Consumer printing batch metrics

Dashboard showing anomaly KPIs

Once these steps complete successfully, the system is fully operational for:

Offline evaluation

Real-time Kafka-based detection

Persistent anomaly storage

Interactive explanation and monitoring

Your full pipeline is now production-ready across Windows, macOS, and Linux.
