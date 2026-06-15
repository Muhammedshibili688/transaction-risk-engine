from redis import Redis


class FeatureDriftMonitor:

    MONITORING_KEY = "monitoring:feature_drift"

    def __init__(
        self,
        redis_client: Redis,
    ):

        self.redis_client = redis_client

    def update(
        self,
        merchant_affinity_score: float,
        merchant_transition_score: float,
    ) -> None:

        pipe = self.redis_client.pipeline()

        pipe.hincrby(
            self.MONITORING_KEY,
            "total_observations",
            1,
        )

        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "merchant_affinity_sum",
            float(merchant_affinity_score),
        )

        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "merchant_transition_sum",
            float(merchant_transition_score),
        )

        current_affinity_min = self.redis_client.hget(
            self.MONITORING_KEY,
            "merchant_affinity_min",
        )

        current_affinity_max = self.redis_client.hget(
            self.MONITORING_KEY,
            "merchant_affinity_max",
        )

        current_transition_min = self.redis_client.hget(
            self.MONITORING_KEY,
            "merchant_transition_min",
        )

        current_transition_max = self.redis_client.hget(
            self.MONITORING_KEY,
            "merchant_transition_max",
        )

        if (
            current_affinity_min is None
            or merchant_affinity_score
            < float(current_affinity_min)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "merchant_affinity_min",
                merchant_affinity_score,
            )

        if (
            current_affinity_max is None
            or merchant_affinity_score
            > float(current_affinity_max)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "merchant_affinity_max",
                merchant_affinity_score,
            )

        if (
            current_transition_min is None
            or merchant_transition_score
            < float(current_transition_min)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "merchant_transition_min",
                merchant_transition_score,
            )

        if (
            current_transition_max is None
            or merchant_transition_score
            > float(current_transition_max)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "merchant_transition_max",
                merchant_transition_score,
            )

        pipe.execute()

    def get_metrics(self) -> dict:

        metrics = self.redis_client.hgetall(
            self.MONITORING_KEY
        )

        if not metrics:

            return {}

        total = int(
            metrics.get(
                "total_observations",
                0,
            )
        )

        if total == 0:

            return {}

        affinity_sum = float(
            metrics.get(
                "merchant_affinity_sum",
                0.0,
            )
        )

        transition_sum = float(
            metrics.get(
                "merchant_transition_sum",
                0.0,
            )
        )

        return {

            "total_observations":
            total,

            "merchant_affinity_mean":
            round(
                affinity_sum / total,
                4,
            ),

            "merchant_affinity_min":
            float(
                metrics.get(
                    "merchant_affinity_min",
                    0.0,
                )
            ),

            "merchant_affinity_max":
            float(
                metrics.get(
                    "merchant_affinity_max",
                    0.0,
                )
            ),

            "merchant_transition_mean":
            round(
                transition_sum / total,
                4,
            ),

            "merchant_transition_min":
            float(
                metrics.get(
                    "merchant_transition_min",
                    0.0,
                )
            ),

            "merchant_transition_max":
            float(
                metrics.get(
                    "merchant_transition_max",
                    0.0,
                )
            ),
        }


if __name__ == "__main__":

    redis_client = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    monitor = FeatureDriftMonitor(
        redis_client=redis_client
    )

    monitor.update(
        merchant_affinity_score=0.42,
        merchant_transition_score=0.33,
    )

    monitor.update(
        merchant_affinity_score=0.87,
        merchant_transition_score=0.65,
    )

    print(
        monitor.get_metrics()
    )

