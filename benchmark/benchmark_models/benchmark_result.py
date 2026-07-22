"""
benchmark/models/benchmark_result.py

Benchmark result model.

Stores all benchmark metrics collected during a benchmark window.
This class intentionally contains no business logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class BenchmarkResult:
    """
    Stores the complete benchmark output.
    """

    # --------------------------------------------------
    # Benchmark Information
    # --------------------------------------------------

    benchmark_name: str = "Transaction Risk Engine Benchmark"
    benchmark_duration: int = 60

    started_at: datetime | None = None
    finished_at: datetime | None = None

    # --------------------------------------------------
    # Transaction Metrics
    # --------------------------------------------------

    transactions_processed: int = 0
    throughput_tps: float = 0.0

    # --------------------------------------------------
    # Latency Metrics (milliseconds)
    # --------------------------------------------------

    average_scoring_latency_ms: float = 0.0
    maximum_scoring_latency_ms: float = 0.0

    # --------------------------------------------------
    # Prediction Metrics
    # --------------------------------------------------

    fraud_rate: float = 0.0
    review_rate: float = 0.0
    average_probability: float = 0.0

    # --------------------------------------------------
    # Model Evaluation Metrics
    # --------------------------------------------------

    precision: float = 0.0
    recall: float = 0.0
    false_positive_rate: float = 0.0

    # --------------------------------------------------
    # Queue Metrics
    # --------------------------------------------------

    transaction_stream_size: int = 0
    scored_stream_size: int = 0
    review_queue_size: int = 0

    # --------------------------------------------------
    # Resource Usage
    # --------------------------------------------------

    cpu_samples: List[float] = field(default_factory=list)
    memory_samples_mb: List[float] = field(default_factory=list)

    average_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0

    average_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0

    # --------------------------------------------------
    # Health
    # --------------------------------------------------

    redis_connected: bool = False
    docker_connected: bool = False

    # --------------------------------------------------
    # Optional Metadata
    # --------------------------------------------------

    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convert the benchmark result into a JSON serializable dictionary.
        """

        return {
            "benchmark_name": self.benchmark_name,
            "benchmark_duration": self.benchmark_duration,
            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),

            "transactions_processed": self.transactions_processed,
            "throughput_tps": round(self.throughput_tps, 2),

            "average_scoring_latency_ms":
                round(self.average_scoring_latency_ms, 3),

            "maximum_scoring_latency_ms":
                round(self.maximum_scoring_latency_ms, 3),

            "fraud_rate":
                round(self.fraud_rate, 6),

            "review_rate":
                round(self.review_rate, 6),

            "average_probability":
                round(self.average_probability, 6),

            "precision":
                round(self.precision, 6),

            "recall":
                round(self.recall, 6),

            "false_positive_rate":
                round(self.false_positive_rate, 6),

            "transaction_stream_size":
                self.transaction_stream_size,

            "scored_stream_size":
                self.scored_stream_size,

            "review_queue_size":
                self.review_queue_size,

            "average_cpu_percent":
                round(self.average_cpu_percent, 2),

            "peak_cpu_percent":
                round(self.peak_cpu_percent, 2),

            "average_memory_mb":
                round(self.average_memory_mb, 2),

            "peak_memory_mb":
                round(self.peak_memory_mb, 2),

            "cpu_samples":
                self.cpu_samples,

            "memory_samples_mb":
                self.memory_samples_mb,

            "redis_connected":
                self.redis_connected,

            "docker_connected":
                self.docker_connected,

            "metadata":
                self.metadata,
        }