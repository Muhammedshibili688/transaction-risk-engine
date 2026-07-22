"""
benchmark/report.py

Benchmark report generator.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from benchmark.models.benchmark_result import BenchmarkResult


class BenchmarkReport:
    """
    Responsible for presenting benchmark results.

    - Console report
    - JSON report
    """

    def __init__(self, result: BenchmarkResult):

        self.result = result

    # --------------------------------------------------
    # Console
    # --------------------------------------------------

    def print_console(self):

        r = self.result

        print()
        print("=" * 70)
        print("TRANSACTION RISK ENGINE BENCHMARK")
        print("=" * 70)

        print(f"Started At              : {r.started_at}")
        print(f"Finished At             : {r.finished_at}")
        print(f"Duration                : {r.benchmark_duration:.2f} sec")

        print()

        print("TRANSACTIONS")

        print(f"  Processed             : {r.transactions_processed:,}")
        print(f"  Throughput            : {r.throughput_tps:.2f} TPS")

        print()

        print("LATENCY")

        print(
            f"  Average Scoring       : "
            f"{r.average_scoring_latency_ms:.2f} ms"
        )

        print(
            f"  Maximum Scoring       : "
            f"{r.maximum_scoring_latency_ms:.2f} ms"
        )

        print()

        print("MODEL")

        print(f"  Fraud Rate            : {r.fraud_rate:.4f}")
        print(f"  Review Rate           : {r.review_rate:.4f}")
        print(f"  Average Probability   : {r.average_probability:.4f}")

        print()

        print("EVALUATION")

        print(f"  Precision             : {r.precision:.4f}")
        print(f"  Recall                : {r.recall:.4f}")
        print(
            f"  False Positive Rate   : "
            f"{r.false_positive_rate:.4f}"
        )

        print()

        print("QUEUES")

        print(
            f"  Transaction Stream    : "
            f"{r.transaction_stream_size:,}"
        )

        print(
            f"  Scored Stream         : "
            f"{r.scored_stream_size:,}"
        )

        print(
            f"  Review Queue          : "
            f"{r.review_queue_size:,}"
        )

        print()

        print("RESOURCE USAGE")

        print(
            f"  Average CPU           : "
            f"{r.average_cpu_percent:.2f}%"
        )

        print(
            f"  Peak CPU              : "
            f"{r.peak_cpu_percent:.2f}%"
        )

        print(
            f"  Average Memory        : "
            f"{r.average_memory_mb:.2f} MB"
        )

        print(
            f"  Peak Memory           : "
            f"{r.peak_memory_mb:.2f} MB"
        )

        print()

        print("SYSTEM")

        print(
            f"  Redis Connected       : "
            f"{r.redis_connected}"
        )

        print(
            f"  Docker Connected      : "
            f"{r.docker_connected}"
        )

        print("=" * 70)

    # --------------------------------------------------
    # JSON
    # --------------------------------------------------

    def save_json(
        self,
        directory: str = "benchmark/reports",
        filename: str | None = None,
    ) -> Path:

        Path(directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        if filename is None:

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            filename = f"benchmark_{timestamp}.json"

        output = Path(directory) / filename

        with output.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.result.to_dict(),
                f,
                indent=4,
            )

        return output