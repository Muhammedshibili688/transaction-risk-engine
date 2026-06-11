import argparse
import json
import redis

from src.configuration.redis_connection import RedisClient
from src.services.scoring_service import ScoringService
from src.logger import logging

STREAM_NAME = "transactions"
GROUP_NAME = "fraud_scoring_group"


def ensure_group(redis_client):
    try:
        redis_client.xgroup_create(
            STREAM_NAME,
            GROUP_NAME,
            id="0",
            mkstream=True
        )

        logging.info(
            f"Created consumer group: {GROUP_NAME}"
        )

    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logging.info(
                f"Consumer group already exists: {GROUP_NAME}"
            )
        else:
            raise


def main(config_path, consumer_name):
    redis_client = RedisClient().client

    ensure_group(redis_client)

    scoring_service = ScoringService(
        config_path=config_path
    )

    logging.info(
        f"Consumer started: {consumer_name}"
    )

    try:
        while True:
            messages = redis_client.xreadgroup(
                GROUP_NAME,
                consumer_name,
                {STREAM_NAME: ">"},
                count=100,
                block=2000
            )

            if not messages:
                continue

            for _, events in messages:
                for msg_id, payload in events:
                    try:
                        tx = json.loads(payload["data"])

                        scoring_service.process_transaction(tx)

                        redis_client.xack(
                            STREAM_NAME,
                            GROUP_NAME,
                            msg_id
                        )

                    except Exception as e:
                        logging.exception(
                            f"Failed processing transaction", e
                        )
    except KeyboardInterrupt:
        logging.info(
            f"Consumer stopped: {consumer_name}"
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        required=True
    )

    parser.add_argument(
        "--consumer",
        required=True
    )

    args = parser.parse_args()

    main(
        args.config,
        args.consumer
    )