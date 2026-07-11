import json
from redis import Redis
from src.configuration.redis_connection import RedisClient
from src.monitoring.feature_drift_monitor import (
    FeatureDriftMonitor,
)


BASELINE_PATH = (
    "reports/baselines/"
    "feature_baseline.json"
)


class DriftDetector:

    def __init__(
        self,
        redis_client: Redis,
        baseline_path: str = BASELINE_PATH,
        drift_threshold: float = 0.10,
    ):

        self.redis_client = redis_client

        self.baseline_path = baseline_path

        self.drift_threshold = drift_threshold

        self.feature_monitor = (
            FeatureDriftMonitor(
                redis_client=redis_client
            )
        )

    def load_baseline(self) -> dict:

        with open(
            self.baseline_path,
            "r",
        ) as f:

            return json.load(f)

    def detect_drift(self) -> dict:

        baseline = self.load_baseline()

        current_metrics = (
            self.feature_monitor
            .get_metrics()
        )

        if not current_metrics:

            return {
                "status":
                "No live feature statistics found."
            }

        results = {}

        # Merchant Affinity

        affinity_baseline = (
            baseline[
                "merchant_affinity_score"
            ]["mean"]
        )

        affinity_current = (
            current_metrics[
                "merchant_affinity_mean"
            ]
        )

        affinity_difference = round(
            abs(
                affinity_current
                -
                affinity_baseline
            ),
            4,
        )

        results[
            "merchant_affinity_score"
        ] = {

            "baseline_mean":
            affinity_baseline,

            "current_mean":
            affinity_current,

            "difference":
            affinity_difference,

            "drift_detected":
            (
                affinity_difference
                >
                self.drift_threshold
            ),
        }

        # Merchant Transition

        transition_baseline = (
            baseline[
                "merchant_transition_score"
            ]["mean"]
        )

        transition_current = (
            current_metrics[
                "merchant_transition_mean"
            ]
        )

        transition_difference = round(
            abs(
                transition_current
                -
                transition_baseline
            ),
            4,
        )

        results[
            "merchant_transition_score"
        ] = {

            "baseline_mean":
            transition_baseline,

            "current_mean":
            transition_current,

            "difference":
            transition_difference,

            "drift_detected":
            (
                transition_difference
                >
                self.drift_threshold
            ),
        }

        return results


if __name__ == "__main__":

    redis_client = RedisClient().client

    detector = DriftDetector(
        redis_client=redis_client
    )

    results = detector.detect_drift()

    print(
        "\nFeature Drift Results\n"
    )

    for feature, stats in results.items():

        print(
            f"\n{feature}"
        )

        print(
            "-" * len(feature)
        )

        if isinstance(
            stats,
            dict,
        ):

            for key, value in stats.items():

                print(
                    f"{key}: {value}"
                )

        else:

            print(stats)
