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

## ⚙️ Setup Guide

Follow the steps below to run the AI Pattern Investigator locally.

---

### 1️⃣ Create and Activate Python Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

---

### 2️⃣ Install Required Python Packages

Install dependencies from requirements file:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install the minimum required packages manually:

```bash
pip install sentence-transformers kafka-python streamlit pandas numpy scikit-learn
```

---

### 3️⃣ Configure Environment Variables

Example (PowerShell on Windows):

```powershell
$env:KAFKA_BROKER="localhost:9092"
$env:TRACE_PATH="data/raw/Event_traces.csv"
$env:LOG_PATH_PATTERN="C:/logs/*.log"
```

Adjust paths and Kafka broker address as needed.

---

### 4️⃣ Build Offline HDFS Normal Index and Baseline

This step:
- Loads normal logs  
- Inserts 80% into the vector database  
- Uses 20% held-out logs to compute similarity baseline  
- Saves baseline to `outputs/baseline.npy`

```bash
python main.py --build_index
```

---

### 5️⃣ Build Offline Text-Log Index and Baseline

Reads mostly normal logs (e.g., Windows CBS Info lines), inserts into the vector store, and computes similarity baseline.

```bash
python main.py --build_index_text --text_log_path data/text_normals.log
```

---

### 6️⃣ Evaluate HDFS Detector (Optional)

Reports:
- AUC  
- Recall  
- False Positive Rate  
- Average similarity query latency  

```bash
python main.py --evaluate
python main.py --evaluate --synthetic
```

---

### 7️⃣ Start Kafka Consumer + Detector (Live Streaming)

This service:
- Batches logs  
- Generates embeddings  
- Queries vector database  
- Flags anomalies  
- Persists detections to SQLite  
- Updates live metrics  

```bash
python kafka_cons.py
```

---

### 8️⃣ Start Kafka Producer (CSV Mode)

Streams HDFS traces into Kafka.  
Optionally injects synthetic anomalies.

```bash
python kafka_prod.py --mode csv --trace_path data/raw/Event_traces.csv
```

---

### 9️⃣ Start Kafka Producer (Live Log File Mode)

Tails system log files and streams lines into Kafka.

```bash
python kafka_prod.py --mode file --log_pattern "C:/logs/*.log"
```

---

### 🔟 Start Streamlit Dashboard

Displays:
- KPIs  
- Recent detections  
- Detailed log inspection  
- “Explain a log” interactive feature  

```bash
streamlit run dashboard.py
```

---

### 1️⃣1️⃣ Docker Setup (Optional)

#### Build Containers

```bash
docker-compose build
```

#### Start All Services

Includes:
- Embedding + detection service  
- Vector database  
- Kafka  
- Dashboard  

```bash
docker-compose up
```

#### Stop All Services

```bash
docker-compose down
```

---

## ✅ You’re Ready

Once running, the system will:
- Ingest logs  
- Generate embeddings  
- Perform real-time similarity search  
- Detect anomalies  
