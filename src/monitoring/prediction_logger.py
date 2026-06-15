from redis import Redis


class PredictionLogger:
    """
    Logs prediction monitoring metrics into Redis.

    Redis Key:
        monitoring:predictions
    """

    MONITORING_KEY = "monitoring:predictions"

    def __init__(self, redis_client: Redis):

        self.redis_client = redis_client

    def log_prediction(
        self,
        probability: float,
        prediction: int,
        merchant_affinity_score: float,
        merchant_transition_score: float,
        is_new_ip: int,
        threshold: float = 0.40,
    ) -> None:

        pipe = self.redis_client.pipeline()

        # Total predictions
        pipe.hincrby(
            self.MONITORING_KEY,
            "total_predictions",
            1,
        )

        # Fraud predictions
        pipe.hincrby(
            self.MONITORING_KEY,
            "fraud_predictions",
            int(prediction),
        )

        # Review predictions
        pipe.hincrby(
            self.MONITORING_KEY,
            "review_predictions",
            int(probability >= threshold),
        )

        # Probability aggregation
        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "probability_sum",
            float(probability),
        )

        # Merchant affinity aggregation
        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "merchant_affinity_sum",
            float(merchant_affinity_score),
        )

        # Merchant transition aggregation
        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "merchant_transition_sum",
            float(merchant_transition_score),
        )

        # New IP count
        pipe.hincrby(
            self.MONITORING_KEY,
            "new_ip_count",
            int(is_new_ip),
        )

        pipe.execute()


if __name__ == "__main__":

    redis_client = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    logger = PredictionLogger(
        redis_client=redis_client
    )

    logger.log_prediction(
        probability=0.82,
        prediction=1,
        merchant_affinity_score=0.15,
        merchant_transition_score=0.10,
        is_new_ip=1,
    )

    print(
        redis_client.hgetall(
            "monitoring:predictions"
        )
    )

