"""
benchmark/benchmark.py

Transaction Risk Engine Benchmark

Entry point for running benchmark measurements.
"""

from __future__ import annotations

import argparse
import sys

from benchmark.runner import BenchmarkRunner
from benchmark.report import BenchmarkReport


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Transaction Risk Engine Benchmark"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Benchmark duration in seconds (default: 60)",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Docker sampling interval in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Save benchmark report as JSON",
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    try:

        print()
        print("=" * 70)
        print("TRANSACTION RISK ENGINE BENCHMARK")
        print("=" * 70)
        print(f"Duration          : {args.duration} sec")
        print(f"Sample Interval   : {args.interval} sec")
        print()

        runner = BenchmarkRunner(
            duration_seconds=args.duration,
            sample_interval=args.interval,
        )

        result = runner.run()

        report = BenchmarkReport(result)

        report.print_console()

        if args.json:

            output = report.save_json()

            print()
            print(f"JSON report saved to: {output}")

        print()
        print("Benchmark completed successfully.")

    except KeyboardInterrupt:

        print()
        print("Benchmark interrupted by user.")
        sys.exit(130)

    except Exception as exc:

        print()
        print("Benchmark failed.")
        print(f"Reason: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()