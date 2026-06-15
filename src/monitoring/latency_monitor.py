from redis import Redis


class LatencyMonitor:

    MONITORING_KEY = "monitoring:latency"

    def __init__(
        self,
        redis_client: Redis,
    ):

        self.redis_client = redis_client

    def update(
        self,
        feature_generation_ms: float,
        scoring_ms: float,
        end_to_end_ms: float,
    ) -> None:

        pipe = self.redis_client.pipeline()

        pipe.hincrby(
            self.MONITORING_KEY,
            "total_requests",
            1,
        )

        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "feature_generation_ms_sum",
            float(feature_generation_ms),
        )

        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "scoring_ms_sum",
            float(scoring_ms),
        )

        pipe.hincrbyfloat(
            self.MONITORING_KEY,
            "end_to_end_ms_sum",
            float(end_to_end_ms),
        )

        current_feature_max = self.redis_client.hget(
            self.MONITORING_KEY,
            "max_feature_generation_ms",
        )

        current_scoring_max = self.redis_client.hget(
            self.MONITORING_KEY,
            "max_scoring_ms",
        )

        current_end_to_end_max = self.redis_client.hget(
            self.MONITORING_KEY,
            "max_end_to_end_ms",
        )

        if (
            current_feature_max is None
            or feature_generation_ms
            > float(current_feature_max)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "max_feature_generation_ms",
                feature_generation_ms,
            )

        if (
            current_scoring_max is None
            or scoring_ms
            > float(current_scoring_max)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "max_scoring_ms",
                scoring_ms,
            )

        if (
            current_end_to_end_max is None
            or end_to_end_ms
            > float(current_end_to_end_max)
        ):
            pipe.hset(
                self.MONITORING_KEY,
                "max_end_to_end_ms",
                end_to_end_ms,
            )

        pipe.execute()

    def get_metrics(self) -> dict:

        metrics = self.redis_client.hgetall(
            self.MONITORING_KEY
        )

        if not metrics:

            return {}

        total_requests = int(
            metrics.get(
                "total_requests",
                0,
            )
        )

        if total_requests == 0:

            return {}

        feature_generation_sum = float(
            metrics.get(
                "feature_generation_ms_sum",
                0.0,
            )
        )

        scoring_sum = float(
            metrics.get(
                "scoring_ms_sum",
                0.0,
            )
        )

        end_to_end_sum = float(
            metrics.get(
                "end_to_end_ms_sum",
                0.0,
            )
        )

        return {

            "total_requests":
            total_requests,

            "avg_feature_generation_ms":
            round(
                feature_generation_sum
                / total_requests,
                3,
            ),

            "avg_scoring_ms":
            round(
                scoring_sum
                / total_requests,
                3,
            ),

            "avg_end_to_end_ms":
            round(
                end_to_end_sum
                / total_requests,
                3,
            ),

            "max_feature_generation_ms":
            float(
                metrics.get(
                    "max_feature_generation_ms",
                    0.0,
                )
            ),

            "max_scoring_ms":
            float(
                metrics.get(
                    "max_scoring_ms",
                    0.0,
                )
            ),

            "max_end_to_end_ms":
            float(
                metrics.get(
                    "max_end_to_end_ms",
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

    monitor = LatencyMonitor(
        redis_client=redis_client
    )

    monitor.update(
        feature_generation_ms=12.4,
        scoring_ms=2.7,
        end_to_end_ms=18.3,
    )

    monitor.update(
        feature_generation_ms=14.8,
        scoring_ms=3.1,
        end_to_end_ms=22.5,
    )

    print(
        monitor.get_metrics()
    )
