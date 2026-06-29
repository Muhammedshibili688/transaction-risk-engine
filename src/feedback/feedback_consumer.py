import os
import json

from dotenv import load_dotenv
from redis import Redis

from src.logger import logging
from src.configuration.redis_connection import (
    RedisClient
)

load_dotenv()

STREAM_NAME = os.getenv(
    "MONITORING_STREAM",
    "monitoring_events"
)

GROUP_NAME = "feedback_group"

CONSUMER_NAME = "feedback_worker1"

EVALUATION_KEY = "evaluation:metrics"


class FeedbackConsumer:

    def __init__(
        self,
        redis_client: Redis
    ):

        self.redis_client = redis_client

    def process_event(
        self,
        fields: dict
    ):

        data = json.loads(
            fields["data"]
        )

        prediction = int(
            data["prediction"]
        )

        actual = int(
            data["actual_label"]
        )

        pipe = self.redis_client.pipeline()

        pipe.hincrby(
            EVALUATION_KEY,
            "total_predictions",
            1
        )

        if prediction == 1 and actual == 1:

            pipe.hincrby(
                EVALUATION_KEY,
                "tp",
                1
            )

        elif prediction == 1 and actual == 0:

            pipe.hincrby(
                EVALUATION_KEY,
                "fp",
                1
            )

        elif prediction == 0 and actual == 0:

            pipe.hincrby(
                EVALUATION_KEY,
                "tn",
                1
            )

        else:

            pipe.hincrby(
                EVALUATION_KEY,
                "fn",
                1
            )

        pipe.execute()


def main():

    redis_client = RedisClient().client

    consumer = FeedbackConsumer(
        redis_client
    )

    try:

        redis_client.xgroup_create(
            STREAM_NAME,
            GROUP_NAME,
            id="0",
            mkstream=True
        )

    except Exception as e:

        if "BUSYGROUP" not in str(e):
            raise

    print(
        f"Feedback consumer started: {CONSUMER_NAME}"
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

                        print(e)

    except KeyboardInterrupt:

        logging.info(
            "Feedback consumer stopped."
        )


if __name__ == "__main__":

    main()