import time
from dataclasses import dataclass, field


@dataclass
class Metrics:
    total_messages: int = 0
    total_batches: int = 0
    total_anomalies: int = 0
    total_latency_sec: float = 0.0

    last_updated: float = field(default_factory=time.time)

    def record_batch(self, num_msgs: int, batch_latency_sec: float, num_anomalies: int) -> None:
        self.total_messages += num_msgs
        self.total_batches += 1
        self.total_anomalies += num_anomalies
        self.total_latency_sec += batch_latency_sec
        self.last_updated = time.time()

    def snapshot(self) -> dict:
        avg_latency = (
            self.total_latency_sec / self.total_batches
            if self.total_batches > 0
            else 0.0
        )
        anomaly_rate = (
            self.total_anomalies / self.total_messages
            if self.total_messages > 0
            else 0.0
        )

        return {
            "total_messages": self.total_messages,
            "total_batches": self.total_batches,
            "total_anomalies": self.total_anomalies,
            "avg_batch_latency_sec": avg_latency,
            "anomaly_rate": anomaly_rate,
            "last_updated": self.last_updated,
        }


METRICS = Metrics()

