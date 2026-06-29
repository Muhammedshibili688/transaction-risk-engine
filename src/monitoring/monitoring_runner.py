from redis import Redis

from src.monitoring.prediction_monitor import (
    PredictionMonitor,
)

from src.monitoring.feature_drift_monitor import (
    FeatureDriftMonitor,
)

from src.monitoring.drift_detector import (
    DriftDetector,
)

from src.monitoring.latency_monitor import (
    LatencyMonitor,
)


def print_section(
    title: str,
) -> None:

    print("\n")
    print("=" * 80)

    print(title)

    print("=" * 80)


def main():

    redis_client = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    prediction_monitor = (
        PredictionMonitor(
            redis_client
        )
    )

    feature_monitor = (
        FeatureDriftMonitor(
            redis_client
        )
    )

    drift_detector = (
        DriftDetector(
            redis_client
        )
    )

    latency_monitor = (
        LatencyMonitor(
            redis_client
        )
    )

    print_section(
        "PREDICTION MONITORING"
    )

    prediction_metrics = (
        prediction_monitor
        .get_metrics()
    )

    if prediction_metrics:

        for key, value in (
            prediction_metrics.items()
        ):

            print(
                f"{key}: {value}"
            )

    else:

        print(
            "No prediction metrics found."
        )

    print_section(
        "FEATURE STATISTICS"
    )

    feature_metrics = (
        feature_monitor
        .get_metrics()
    )

    if feature_metrics:

        for key, value in (
            feature_metrics.items()
        ):

            print(
                f"{key}: {value}"
            )

    else:

        print(
            "No feature statistics found."
        )

    print_section(
        "FEATURE DRIFT DETECTION"
    )

    drift_results = (
        drift_detector
        .detect_drift()
    )

    if drift_results:

        for (
            feature,
            stats
        ) in drift_results.items():

            print(
                f"\n{feature}"
            )

            if isinstance(
                stats,
                dict,
            ):

                for (
                    key,
                    value
                ) in stats.items():

                    print(
                        f"  {key}: {value}"
                    )

            else:

                print(
                    stats
                )

    else:

        print(
            "No drift information found."
        )

    print_section(
        "LATENCY MONITORING"
    )

    latency_metrics = (
        latency_monitor
        .get_metrics()
    )

    if latency_metrics:

        for key, value in (
            latency_metrics.items()
        ):

            print(
                f"{key}: {value}"
            )

    else:

        print(
            "No latency metrics found."
        )

    print("\n")
    print("=" * 80)

    print(
        "MONITORING SNAPSHOT COMPLETE"
    )

    print("=" * 80)


if __name__ == "__main__":

    main()

