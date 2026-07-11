from redis import Redis
from src.configuration.redis_connection import RedisClient

class PredictionMonitor:

    MONITORING_KEY = "monitoring:predictions"

    def __init__(
        self,
        redis_client: Redis,
    ):

        self.redis_client = redis_client

    def get_metrics(self) -> dict:

        metrics = self.redis_client.hgetall(
            self.MONITORING_KEY
        )

        if not metrics:

            return {
                "total_predictions": 0,
                "fraud_rate": 0.0,
                "review_rate": 0.0,
                "average_probability": 0.0,
                "merchant_affinity_score_mean": 0.0,
                "merchant_transition_score_mean": 0.0,
                "new_ip_rate": 0.0,
            }

        total_predictions = int(
            metrics.get(
                "total_predictions",
                0,
            )
        )

        if total_predictions == 0:

            return {
                "total_predictions": 0,
                "fraud_rate": 0.0,
                "review_rate": 0.0,
                "average_probability": 0.0,
                "merchant_affinity_score_mean": 0.0,
                "merchant_transition_score_mean": 0.0,
                "new_ip_rate": 0.0,
            }

        fraud_predictions = int(
            metrics.get(
                "fraud_predictions",
                0,
            )
        )

        review_predictions = int(
            metrics.get(
                "review_predictions",
                0,
            )
        )

        probability_sum = float(
            metrics.get(
                "probability_sum",
                0.0,
            )
        )

        merchant_affinity_sum = float(
            metrics.get(
                "merchant_affinity_sum",
                0.0,
            )
        )

        merchant_transition_sum = float(
            metrics.get(
                "merchant_transition_sum",
                0.0,
            )
        )

        new_ip_count = int(
            metrics.get(
                "new_ip_count",
                0,
            )
        )

        return {

            "total_predictions":
            total_predictions,

            "fraud_rate":
            round(
                fraud_predictions
                / total_predictions,
                4,
            ),

            "review_rate":
            round(
                review_predictions
                / total_predictions,
                4,
            ),

            "average_probability":
            round(
                probability_sum
                / total_predictions,
                4,
            ),

            "merchant_affinity_score_mean":
            round(
                merchant_affinity_sum
                / total_predictions,
                4,
            ),

            "merchant_transition_score_mean":
            round(
                merchant_transition_sum
                / total_predictions,
                4,
            ),

            "new_ip_rate":
            round(
                new_ip_count
                / total_predictions,
                4,
            ),
        }


if __name__ == "__main__":

    redis_client = RedisClient().client

    monitor = PredictionMonitor(
        redis_client=redis_client
    )

    metrics = monitor.get_metrics()

    print("\nPrediction Monitoring Metrics\n")

    for key, value in metrics.items():

        print(
            f"{key}: {value}"
        )

