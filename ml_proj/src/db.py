import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Iterable, Dict, Any, List


DB_PATH = os.environ.get("ANOMALIES_DB_PATH", "data/anomalies.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            log_text TEXT NOT NULL,
            label TEXT,
            similarity REAL NOT NULL,
            score REAL NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL
        )
        """
    )
    conn.commit()


@contextmanager
def get_connection():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        _init_db(conn)
        yield conn
    finally:
        conn.close()


def insert_detection(
    log_text: str,
    label: str | None,
    similarity: float,
    score: float,
    status: str,
    source: str = "kafka",
) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO detections (
                timestamp, log_text, label,
                similarity, score, status, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, log_text, label, similarity, score, status, source),
        )
        conn.commit()


def insert_batch(
    records: Iterable[Dict[str, Any]],
) -> None:
    rows: List[tuple] = []
    now = datetime.now(timezone.utc).isoformat()
    for rec in records:
        rows.append(
            (
                rec.get("timestamp", now),
                rec["log_text"],
                rec.get("label"),
                rec["similarity"],
                rec["score"],
                rec["status"],
                rec.get("source", "kafka"),
            )
        )

    if not rows:
        return

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO detections (
                timestamp, log_text, label,
                similarity, score, status, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def get_recent_detections(limit: int = 200) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT id, timestamp, log_text, label,
                   similarity, score, status, source
            FROM detections
            ORDER BY datetime(timestamp) DESC
            LIMIT ?
            """,
            (limit,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_stats(last_minutes: int = 60) -> dict[str, Any]:
    """
    Compute stats over detections in the last `last_minutes` minutes.

    We filter timestamps in Python because they are stored as ISO8601 with
    timezone (e.g. 2026-03-01T21:45:06.123456+00:00), which SQLite's
    datetime() helper does not handle reliably for range queries.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=last_minutes)

    with get_connection() as conn:
        cur = conn.execute(
            "SELECT timestamp, status, score FROM detections"
        )
        rows = cur.fetchall()

    total = 0
    anomalies = 0
    scores: list[float] = []

    for ts_str, status, score in rows:
        try:
            ts = datetime.fromisoformat(ts_str)
        except Exception:
            # Skip rows with unparsable timestamps
            continue

        if ts < cutoff:
            continue

        total += 1
        if status == "ANOMALY":
            anomalies += 1
        if score is not None:
            scores.append(float(score))

    avg_score = sum(scores) / len(scores) if scores else None
    anomaly_rate = (anomalies / total) if total else 0.0

    return {
        "total": total,
        "anomalies": anomalies,
        "avg_score": avg_score,
        "anomaly_rate": anomaly_rate,
        "window_minutes": last_minutes,
    }

