"""
benchmark/collectors/system_collector.py

System health collector.

Performs pre-benchmark health checks.

This collector DOES NOT measure performance.
It only verifies that required services are available.
"""

from typing import Dict

from src.configuration.redis_connection import RedisClient

from benchmark.collectors.docker_collector import DockerCollector


class SystemCollector:
    """
    Performs environment health checks.
    """

    REQUIRED_REDIS_KEYS = [
        "monitoring:predictions",
        "monitoring:latency",
        "evaluation:metrics",
    ]

    def __init__(self):

        self.redis = RedisClient().client
        self.docker = DockerCollector()

    # --------------------------------------------------
    # Redis
    # --------------------------------------------------

    def redis_connected(self) -> bool:

        try:
            return self.redis.ping()

        except Exception:
            return False

    def redis_keys_exist(self) -> Dict[str, bool]:

        result = {}

        for key in self.REQUIRED_REDIS_KEYS:

            try:
                result[key] = self.redis.exists(key) == 1

            except Exception:
                result[key] = False

        return result

    # --------------------------------------------------
    # Docker
    # --------------------------------------------------

    def docker_connected(self) -> bool:

        try:
            self.docker.client.ping()
            return True

        except Exception:
            return False

    def running_container_count(self) -> int:

        try:
            return len(
                self.docker._containers()
            )

        except Exception:
            return 0

    # --------------------------------------------------
    # Overall Health
    # --------------------------------------------------

    def health_report(self) -> Dict:

        redis_ok = self.redis_connected()

        docker_ok = self.docker_connected()

        keys = self.redis_keys_exist()

        containers = self.running_container_count()

        return {

            "redis_connected":
                redis_ok,

            "docker_connected":
                docker_ok,

            "running_containers":
                containers,

            "redis_keys":
                keys,

            "system_ready":

                redis_ok
                and docker_ok
                and all(keys.values())
                and containers > 0

        }


if __name__ == "__main__":

    collector = SystemCollector()

    report = collector.health_report()

    print()

    print("===== System Health =====")

    print(
        f"Redis Connected    : {report['redis_connected']}"
    )

    print(
        f"Docker Connected   : {report['docker_connected']}"
    )

    print(
        f"Running Containers : {report['running_containers']}"
    )

    print()

    print("Redis Keys")

    for key, exists in report["redis_keys"].items():

        print(f"  {key:<30} {exists}")

    print()

    print(
        f"System Ready       : {report['system_ready']}"
    )