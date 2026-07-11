from redis import Redis
from prometheus_client import (
    Gauge,
    start_http_server
)

from src.configuration.redis_connection import RedisClient
redis_client = RedisClient().client

import time


# ===========================
# Prediction Metrics
# ===========================

transactions_processed = Gauge(
    "transactions_processed_total",
    "Total processed transactions"
)

review_rate = Gauge(
    "review_rate",
    "Review rate"
)

fraud_rate = Gauge(
    "fraud_rate",
    "Fraud rate"
)

average_probability = Gauge(
    "average_probability",
    "Average fraud probability"
)

# ===========================
# Warmup Metrics/Cold Start Metrics
# ===========================

warmup_progress = Gauge(
    "warmup_progress",
    "Warmup Progress"
)

system_stage = Gauge(
    "system_stage",
    "Current system stage"
)


# ===========================
# Feature Drift Metrics
# ===========================

merchant_affinity_mean = Gauge(
    "merchant_affinity_mean",
    "Merchant affinity mean"
)

merchant_transition_mean = Gauge(
    "merchant_transition_mean",
    "Merchant transition mean"
)

new_ip_rate = Gauge(
    "new_ip_rate",
    "New IP rate"
)


# ===========================
# Latency Metrics
# ===========================

avg_scoring_latency = Gauge(
    "avg_scoring_latency_ms",
    "Average scoring latency"
)

max_scoring_latency = Gauge(
    "max_scoring_latency_ms",
    "Maximum scoring latency"
)


# ===========================
# Feedback Metrics
# ===========================

precision = Gauge(
    "feedback_precision",
    "Precision"
)

recall = Gauge(
    "feedback_recall",
    "Recall"
)

false_positive_rate = Gauge(
    "feedback_false_positive_rate",
    "False Positive Rate"
)


# ===========================
# Queue Metrics
# ===========================

review_queue = Gauge(
    "review_queue_size",
    "Review Queue Size"
)

transaction_stream = Gauge(
    "transaction_stream_size",
    "Transactions Stream"
)

scored_stream = Gauge(
    "scored_stream_size",
    "Scored Stream"
)


def safe_float(value):

    if value is None:
        return 0.0

    return float(value)


def safe_int(value):

    if value is None:
        return 0

    return int(value)


def update_metrics():

    prediction = redis_client.hgetall(
        "monitoring:predictions"
    )

    latency = redis_client.hgetall(
        "monitoring:latency"
    )

    feedback = redis_client.hgetall(
        "evaluation:metrics"
    )


    # -------------------------
    # Prediction
    # -------------------------

    total = safe_int(
        prediction.get(
            "total_predictions"
        )
    )

    fraud = safe_int(
        prediction.get(
            "fraud_predictions"
        )
    )

    review = safe_int(
        prediction.get(
            "review_predictions"
        )
    )

    probability_sum = safe_float(
        prediction.get(
            "probability_sum"
        )
    )

    affinity_sum = safe_float(
        prediction.get(
            "merchant_affinity_sum"
        )
    )

    transition_sum = safe_float(
        prediction.get(
            "merchant_transition_sum"
        )
    )

    new_ip = safe_int(
        prediction.get(
            "new_ip_count"
        )
    )

    transactions_processed.set(
        total
    )

    # -------------------------
    # Warmup stage
    # -------------------------

    WARMUP_TARGET = 300000

    warmup_progress.set(
        min(
            total / WARMUP_TARGET,
            1.0
        )
    )

    if total < 100000:

        system_stage.set(0)

    elif total < 300000:

        system_stage.set(1)

    else:

        system_stage.set(2)

    if total > 0:

        review_rate.set(
            review / total
        )

        fraud_rate.set(
            fraud / total
        )

        average_probability.set(
            probability_sum / total
        )

        merchant_affinity_mean.set(
            affinity_sum / total
        )

        merchant_transition_mean.set(
            transition_sum / total
        )

        new_ip_rate.set(
            new_ip / total
        )

    # -------------------------
    # Latency
    # -------------------------

    requests = safe_int(
        latency.get(
            "total_requests"
        )
    )

    if requests > 0:

        avg_scoring_latency.set(

            safe_float(
                latency.get(
                    "scoring_ms_sum"
                )
            ) / requests

        )

    max_scoring_latency.set(

        safe_float(
            latency.get(
                "max_scoring_ms"
            )
        )

    )

    # -------------------------
    # Feedback
    # -------------------------

    tp = safe_int(
        feedback.get("tp")
    )

    fp = safe_int(
        feedback.get("fp")
    )

    fn = safe_int(
        feedback.get("fn")
    )

    if tp + fp > 0:

        precision.set(
            tp / (tp + fp)
        )

    if tp + fn > 0:

        recall.set(
            tp / (tp + fn)
        )

    tn = safe_int(
        feedback.get("tn")
    )

    if fp + tn > 0:

        false_positive_rate.set(
            fp / (fp + tn)
        )

    # -------------------------
    # Streams
    # -------------------------

    review_queue.set(

        redis_client.xlen(
            "risk_decisions:review"
        )

    )

    transaction_stream.set(

        redis_client.xlen(
            "transactions"
        )

    )

    scored_stream.set(

        redis_client.xlen(
            "scored_transactions"
        )

    )


if __name__ == "__main__":

    start_http_server(
        9101
    )

    print(
        "Prometheus exporter running on :9101"
    )

    while True:

        update_metrics()

        time.sleep(5)