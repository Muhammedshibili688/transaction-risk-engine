"""
benchmark/collectors/docker_collector.py

Docker resource collector.

Collects CPU and Memory usage from all running
Transaction Risk Engine containers.

Read-only collector.
"""

from typing import Dict, List

import docker


class DockerCollector:
    """
    Collects CPU and Memory statistics
    from all running project containers.
    """

    def __init__(self):

        self.client = docker.from_env()

        # Prefix used by docker compose
        self.project_name = "transaction-risk-engine"

    # --------------------------------------------------
    # Internal
    # --------------------------------------------------

    def _containers(self):

        return [

            container

            for container in self.client.containers.list()

            if self.project_name
            in container.name

        ]

    @staticmethod
    def _cpu_percent(stats):

        cpu_delta = (

            stats["cpu_stats"]["cpu_usage"]["total_usage"]

            -

            stats["precpu_stats"]["cpu_usage"]["total_usage"]

        )

        system_delta = (

            stats["cpu_stats"]["system_cpu_usage"]

            -

            stats["precpu_stats"]["system_cpu_usage"]

        )

        if cpu_delta <= 0 or system_delta <= 0:

            return 0.0

        cpus = len(

            stats["cpu_stats"]["cpu_usage"].get(
                "percpu_usage",
                []
            )

        )

        if cpus == 0:

            cpus = 1

        return (

            cpu_delta
            / system_delta
            * cpus
            * 100.0

        )

    @staticmethod
    def _memory_mb(stats):

        usage = stats["memory_stats"].get(
            "usage",
            0
        )

        return usage / (1024 * 1024)

    # --------------------------------------------------
    # Public
    # --------------------------------------------------

    def snapshot(self) -> Dict:
        """
        Returns aggregated CPU and memory
        usage across all running containers.
        """

        cpu_values: List[float] = []
        memory_values: List[float] = []

        for container in self._containers():

            try:

                stats = container.stats(
                    stream=False
                )

                cpu_values.append(

                    self._cpu_percent(
                        stats
                    )

                )

                memory_values.append(

                    self._memory_mb(
                        stats
                    )

                )

            except Exception:

                continue

        return {

            "cpu_percent":

                sum(cpu_values),

            "memory_mb":

                sum(memory_values),

            "container_count":

                len(cpu_values)

        }


if __name__ == "__main__":

    collector = DockerCollector()

    metrics = collector.snapshot()

    print()

    print(

        f"Running Containers : {metrics['container_count']}"

    )

    print(

        f"CPU Usage          : {metrics['cpu_percent']:.2f}%"

    )

    print(

        f"Memory Usage       : {metrics['memory_mb']:.2f} MB"

    )