import os
import json
from dotenv import load_dotenv
from redis import Redis
from src.logger import logging
from src.configuration.redis_connection import RedisClient
from src.monitoring.prediction_logger import (
    PredictionLogger,
)

from src.monitoring.feature_drift_monitor import (
    FeatureDriftMonitor,
)

from src.monitoring.latency_monitor import (
    LatencyMonitor,
)
load_dotenv()

STREAM_NAME = os.getenv("MONITORING_STREAM")

GROUP_NAME = "monitoring_group"

CONSUMER_NAME = "monitor1"

class MonitoringConsumer:

    def __init__(
        self,
        redis_client: Redis,
    ):

        self.redis_client = redis_client

        self.prediction_logger = (
            PredictionLogger(
                redis_client
            )
        )

        self.feature_drift_monitor = (
            FeatureDriftMonitor(
                redis_client
            )
        )

        self.latency_monitor = (
            LatencyMonitor(
                redis_client
            )
        )

    def process_event(
        self,
        fields: dict,
    ) -> None:
    

        data = json.loads(
            fields["data"]
        )

        self.prediction_logger.log_prediction(
            probability=
                data["probability"],

            prediction=
                data["prediction"],

            merchant_affinity_score=
                data[
                    "merchant_affinity_score"
                ],

            merchant_transition_score=
                data[
                    "merchant_transition_score"
                ],

            is_new_ip=
                data["is_new_ip"]
        )

        self.feature_drift_monitor.update(
            merchant_affinity_score=
                data[
                    "merchant_affinity_score"
                ],

            merchant_transition_score=
                data[
                    "merchant_transition_score"
                ]
        )

        self.latency_monitor.update(
            feature_generation_ms=0,

            scoring_ms=
                data["latency_ms"],

            end_to_end_ms=
                data["latency_ms"]
        )

def main():

    redis_client = RedisClient().client

    consumer = MonitoringConsumer(
        redis_client
    )

    try:

        redis_client.xgroup_create(
            STREAM_NAME,
            GROUP_NAME,
            id="0",
            mkstream=True
        )

        print(
            f"Created group {GROUP_NAME}"
        )

    except Exception as e:

        print(e)

    print(
        f"Monitoring consumer started: {CONSUMER_NAME}"
    )

    try:

        while True:

            messages = redis_client.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={
                    STREAM_NAME: ">"
                },
                count=100,
                block=5000
            )

            if not messages:
                continue

            for _, records in messages:

                for message_id, fields in records:

                    try:

                        consumer.process_event(
                            fields
                        )

                        redis_client.xack(
                            STREAM_NAME,
                            GROUP_NAME,
                            message_id
                        )

                    except Exception as e:

                        print(
                            f"Error: {e}"
                        )

    except KeyboardInterrupt:
        logging.info(
            f"Monitoring Consumer stopped: {CONSUMER_NAME}"
        )

if __name__ == "__main__":
    main()