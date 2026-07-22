"""
benchmark/utils/calculations.py

Reusable mathematical helper functions for benchmark metrics.
"""

from typing import Iterable
import statistics


def calculate_delta(
    start_value: float | int,
    end_value: float | int,
) -> float:
    """
    Returns the difference between two cumulative counters.
    """

    return max(0.0, end_value - start_value)


def calculate_throughput(
    transactions_processed: int,
    duration_seconds: float,
) -> float:
    """
    Transactions Per Second (TPS)
    """

    if duration_seconds <= 0:
        return 0.0

    return transactions_processed / duration_seconds


def calculate_average(
    values: Iterable[float],
) -> float:
    """
    Average of a collection.
    """

    values = list(values)

    if not values:
        return 0.0

    return statistics.mean(values)


def calculate_peak(
    values: Iterable[float],
) -> float:
    """
    Maximum value of a collection.
    """

    values = list(values)

    if not values:
        return 0.0

    return max(values)


def calculate_rate(
    numerator: float,
    denominator: float,
) -> float:
    """
    Generic rate calculation.

    Example:
        fraud_rate
        review_rate
        precision
        recall
    """

    if denominator <= 0:
        return 0.0

    return numerator / denominator


def calculate_percentage(
    numerator: float,
    denominator: float,
) -> float:
    """
    Returns percentage (0-100).
    """

    return calculate_rate(
        numerator,
        denominator,
    ) * 100.0


def calculate_average_latency(
    latency_sum_ms: float,
    request_count: int,
) -> float:
    """
    Average latency from cumulative latency sum.
    """

    if request_count <= 0:
        return 0.0

    return latency_sum_ms / request_count


def safe_round(
    value: float,
    digits: int = 2,
) -> float:
    """
    Safe rounding helper.
    """

    try:
        return round(value, digits)
    except Exception:
        return 0.0


if __name__ == "__main__":

    print(
        "Delta:",
        calculate_delta(
            1000,
            2500,
        )
    )

    print(
        "TPS:",
        calculate_throughput(
            125000,
            60,
        )
    )

    print(
        "Average:",
        calculate_average(
            [10, 20, 30, 40]
        )
    )

    print(
        "Peak:",
        calculate_peak(
            [10, 20, 30, 40]
        )
    )

    print(
        "Rate:",
        calculate_rate(
            25,
            100,
        )
    )

    print(
        "Percentage:",
        calculate_percentage(
            25,
            100,
        )
    )

    print(
        "Latency:",
        calculate_average_latency(
            250000,
            50000,
        )
    )