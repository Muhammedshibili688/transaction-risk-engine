"""
benchmark/runner.py

Benchmark runner.

Coordinates:
- System health checks
- Redis metric collection
- Docker resource sampling
- Benchmark timing
- Result calculation
"""

from __future__ import annotations

import time

from benchmark.collectors.redis_collector import RedisCollector
from benchmark.collectors.docker_collector import DockerCollector
from benchmark.collectors.system_collector import SystemCollector

from benchmark.benchmark_models.benchmark_result import BenchmarkResult

from benchmark.utils.timer import BenchmarkTimer
from benchmark.utils.calculations import (
    calculate_delta,
    calculate_throughput,
    calculate_average,
    calculate_peak,
    calculate_average_latency,
    calculate_rate,
)

from benchmark.report import BenchmarkReport


class BenchmarkRunner:
    """
    Executes a benchmark over a fixed observation window.
    """

    def __init__(
        self,
        duration_seconds: int = 60,
        sample_interval: float = 1.0,
    ):

        self.duration = duration_seconds
        self.sample_interval = sample_interval

        self.redis = RedisCollector()
        self.docker = DockerCollector()
        self.system = SystemCollector()

    # --------------------------------------------------
    # Run Benchmark
    # --------------------------------------------------

    def run(self) -> BenchmarkResult:

        # -------------------------
        # Health Check
        # -------------------------

        health = self.system.health_report()

        if not health["system_ready"]:
            raise RuntimeError(
                "System health checks failed."
            )

        result = BenchmarkResult()

        result.redis_connected = health["redis_connected"]
        result.docker_connected = health["docker_connected"]

        timer = BenchmarkTimer()

        # -------------------------
        # Initial Snapshot
        # -------------------------

        start = self.redis.snapshot()

        cpu_samples = []
        memory_samples = []

        timer.start()

        # -------------------------
        # Observation Window
        # -------------------------

        while timer.elapsed_seconds < self.duration:

            docker = self.docker.snapshot()

            cpu_samples.append(
                docker["cpu_percent"]
            )

            memory_samples.append(
                docker["memory_mb"]
            )

            time.sleep(
                self.sample_interval
            )

        timer.stop()

        # -------------------------
        # Final Snapshot
        # -------------------------

        end = self.redis.snapshot()

        # --------------------------------------------------
        # Transaction Metrics
        # --------------------------------------------------

        processed = int(
            calculate_delta(
                start["total_predictions"],
                end["total_predictions"],
            )
        )

        result.transactions_processed = processed

        result.throughput_tps = calculate_throughput(
            processed,
            timer.elapsed_seconds,
        )

        # --------------------------------------------------
        # Latency
        # --------------------------------------------------

        request_delta = int(
            calculate_delta(
                start["total_requests"],
                end["total_requests"],
            )
        )

        latency_sum = calculate_delta(
            start["scoring_ms_sum"],
            end["scoring_ms_sum"],
        )

        result.average_scoring_latency_ms = (
            calculate_average_latency(
                latency_sum,
                request_delta,
            )
        )

        result.maximum_scoring_latency_ms = max(
            start["max_scoring_ms"],
            end["max_scoring_ms"],
        )

        # --------------------------------------------------
        # Prediction Metrics
        # --------------------------------------------------

        fraud_delta = calculate_delta(
            start["fraud_predictions"],
            end["fraud_predictions"],
        )

        review_delta = calculate_delta(
            start["review_predictions"],
            end["review_predictions"],
        )

        probability_delta = calculate_delta(
            start["probability_sum"],
            end["probability_sum"],
        )

        result.fraud_rate = calculate_rate(
            fraud_delta,
            processed,
        )

        result.review_rate = calculate_rate(
            review_delta,
            processed,
        )

        result.average_probability = (
            calculate_rate(
                probability_delta,
                processed,
            )
        )

        # --------------------------------------------------
        # Evaluation Metrics
        # --------------------------------------------------

        tp = end["tp"]
        fp = end["fp"]
        fn = end["fn"]
        tn = end["tn"]

        result.precision = calculate_rate(
            tp,
            tp + fp,
        )

        result.recall = calculate_rate(
            tp,
            tp + fn,
        )

        result.false_positive_rate = calculate_rate(
            fp,
            fp + tn,
        )

        # --------------------------------------------------
        # Queue Metrics
        # --------------------------------------------------

        result.transaction_stream_size = (
            end["transaction_stream_size"]
        )

        result.scored_stream_size = (
            end["scored_stream_size"]
        )

        result.review_queue_size = (
            end["review_queue_size"]
        )

        # --------------------------------------------------
        # Docker Resources
        # --------------------------------------------------

        result.cpu_samples = cpu_samples
        result.memory_samples_mb = memory_samples

        result.average_cpu_percent = (
            calculate_average(cpu_samples)
        )

        result.peak_cpu_percent = (
            calculate_peak(cpu_samples)
        )

        result.average_memory_mb = (
            calculate_average(memory_samples)
        )

        result.peak_memory_mb = (
            calculate_peak(memory_samples)
        )

        # --------------------------------------------------
        # Timing
        # --------------------------------------------------

        result.started_at = timer.started_at
        result.finished_at = timer.finished_at
        result.benchmark_duration = timer.elapsed_seconds

        return result


if __name__ == "__main__":

    runner = BenchmarkRunner(
        duration_seconds=60
    )

    result = runner.run()

    report = BenchmarkReport(result)

    report.print_console()

    path = report.save_json()

    print()
    print(f"Benchmark report saved to: {path}")