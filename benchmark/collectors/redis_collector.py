"""
benchmark/collectors/redis_collector.py

Redis collector for benchmark metrics.

Read-only collector.

Collects:
- Prediction metrics
- Latency metrics
- Evaluation metrics
- Queue metrics
"""

from typing import Dict

from src.configuration.redis_connection import RedisClient


class RedisCollector:
    """
    Read-only Redis benchmark collector.
    """

    def __init__(self):

        self.redis = RedisClient().client

    # --------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------

    @staticmethod
    def _safe_int(value):

        if value is None:
            return 0

        return int(value)

    @staticmethod
    def _safe_float(value):

        if value is None:
            return 0.0

        return float(value)

    # --------------------------------------------------
    # Prediction Metrics
    # --------------------------------------------------

    def prediction_metrics(self) -> Dict:

        prediction = self.redis.hgetall(
            "monitoring:predictions"
        )

        return {

            "total_predictions":
                self._safe_int(
                    prediction.get(
                        "total_predictions"
                    )
                ),

            "fraud_predictions":
                self._safe_int(
                    prediction.get(
                        "fraud_predictions"
                    )
                ),

            "review_predictions":
                self._safe_int(
                    prediction.get(
                        "review_predictions"
                    )
                ),

            "probability_sum":
                self._safe_float(
                    prediction.get(
                        "probability_sum"
                    )
                ),

            "merchant_affinity_sum":
                self._safe_float(
                    prediction.get(
                        "merchant_affinity_sum"
                    )
                ),

            "merchant_transition_sum":
                self._safe_float(
                    prediction.get(
                        "merchant_transition_sum"
                    )
                ),

            "new_ip_count":
                self._safe_int(
                    prediction.get(
                        "new_ip_count"
                    )
                ),
        }

    # --------------------------------------------------
    # Latency Metrics
    # --------------------------------------------------

    def latency_metrics(self) -> Dict:

        latency = self.redis.hgetall(
            "monitoring:latency"
        )

        return {

            "total_requests":
                self._safe_int(
                    latency.get(
                        "total_requests"
                    )
                ),

            "feature_generation_ms_sum":
                self._safe_float(
                    latency.get(
                        "feature_generation_ms_sum"
                    )
                ),

            "scoring_ms_sum":
                self._safe_float(
                    latency.get(
                        "scoring_ms_sum"
                    )
                ),

            "end_to_end_ms_sum":
                self._safe_float(
                    latency.get(
                        "end_to_end_ms_sum"
                    )
                ),

            "max_feature_generation_ms":
                self._safe_float(
                    latency.get(
                        "max_feature_generation_ms"
                    )
                ),

            "max_scoring_ms":
                self._safe_float(
                    latency.get(
                        "max_scoring_ms"
                    )
                ),

            "max_end_to_end_ms":
                self._safe_float(
                    latency.get(
                        "max_end_to_end_ms"
                    )
                ),
        }

    # --------------------------------------------------
    # Evaluation Metrics
    # --------------------------------------------------

    def evaluation_metrics(self) -> Dict:

        evaluation = self.redis.hgetall(
            "evaluation:metrics"
        )

        return {

            "tp":
                self._safe_int(
                    evaluation.get("tp")
                ),

            "fp":
                self._safe_int(
                    evaluation.get("fp")
                ),

            "tn":
                self._safe_int(
                    evaluation.get("tn")
                ),

            "fn":
                self._safe_int(
                    evaluation.get("fn")
                ),
        }

    # --------------------------------------------------
    # Queue Metrics
    # --------------------------------------------------

    def queue_metrics(self) -> Dict:

        return {

            "transaction_stream_size":
                self.redis.xlen(
                    "transactions"
                ),

            "scored_stream_size":
                self.redis.xlen(
                    "scored_transactions"
                ),

            "review_queue_size":
                self.redis.xlen(
                    "risk_decisions:review"
                ),
        }

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------

    def snapshot(self) -> Dict:
        """
        Returns a complete benchmark snapshot.

        Used at both the start and end of the
        benchmark window.
        """

        snapshot = {}

        snapshot.update(
            self.prediction_metrics()
        )

        snapshot.update(
            self.latency_metrics()
        )

        snapshot.update(
            self.evaluation_metrics()
        )

        snapshot.update(
            self.queue_metrics()
        )

        return snapshot


if __name__ == "__main__":

    collector = RedisCollector()

    snapshot = collector.snapshot()

    print()

    for key, value in snapshot.items():

        print(f"{key:35} : {value}")