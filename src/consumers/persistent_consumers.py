import json
import os

from src.configuration.redis_connection import RedisClient
from src.logger import logging

STREAM_NAME = "scored_transactions"


def main():
    redis_client = RedisClient().client

    os.makedirs("datas/processed", exist_ok=True)
    os.makedirs("datas/predictions", exist_ok=True)

    features_writer = open(
        "datas/processed/features.jsonl",
        "a",
        buffering=1
    )

    predictions_writer = open(
        "datas/predictions/live_predictions.jsonl",
        "a",
        buffering=1
    )

    last_id = "$"

    logging.info("Persistence consumer started")

    while True:
        messages = redis_client.xread(
            {STREAM_NAME: last_id},
            count=500,
            block=5000
        )

        if not messages:
            continue

        for _, events in messages:
            for msg_id, payload in events:
                try:
                    obj = json.loads(payload["data"])

                    features_writer.write(
                        json.dumps(obj["features"]) + "\n"
                    )

                    predictions_writer.write(
                        json.dumps(obj["prediction"]) + "\n"
                    )

                    last_id = msg_id

                except Exception:
                    logging.exception(
                        "Persistence write failed"
                    )


if __name__ == "__main__":
    main()