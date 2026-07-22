"""
benchmark/utils/timer.py

Simple high-resolution benchmark timer.
"""

import time
from datetime import datetime


class BenchmarkTimer:
    """
    High resolution timer used by the benchmark runner.
    """

    def __init__(self):

        self._start = None
        self._end = None

        self.started_at = None
        self.finished_at = None

    def start(self):
        """
        Start the benchmark timer.
        """

        self.started_at = datetime.now()
        self._start = time.perf_counter()

    def stop(self):
        """
        Stop the benchmark timer.
        """

        self.finished_at = datetime.now()
        self._end = time.perf_counter()

    @property
    def elapsed_seconds(self) -> float:
        """
        Returns elapsed benchmark time in seconds.
        """

        if self._start is None:
            return 0.0

        if self._end is None:
            return time.perf_counter() - self._start

        return self._end - self._start

    @property
    def elapsed_minutes(self) -> float:
        """
        Returns elapsed time in minutes.
        """

        return self.elapsed_seconds / 60

    @property
    def is_running(self) -> bool:
        """
        Returns True while the timer is running.
        """

        return (
            self._start is not None
            and self._end is None
        )

    def reset(self):
        """
        Reset timer state.
        """

        self._start = None
        self._end = None

        self.started_at = None
        self.finished_at = None


if __name__ == "__main__":

    timer = BenchmarkTimer()

    timer.start()

    time.sleep(2)

    timer.stop()

    print(f"Started : {timer.started_at}")
    print(f"Finished: {timer.finished_at}")
    print(f"Elapsed : {timer.elapsed_seconds:.2f} sec")