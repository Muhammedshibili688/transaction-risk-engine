import json
import os
import io
import shutil
import pandas as pd

from src.configuration.redis_connection import RedisClient
from src.configuration.aws_connection import S3Connection
from src.logger import logging

S3_BUCKET = os.getenv("TRAINING_BUCKET_NAME")

if not S3_BUCKET:
    raise ValueError(
        "TRAINING_BUCKET_NAME environment variable not set"
    )

SCORED_STREAM = os.getenv(
    "SCORED_STREAM",
    "scored_transactions"
)

STREAM_BATCH_SIZE = 5000
TMP_DIR = "tmp/export_snapshot"


RAW_COLUMNS = [
    "tx_id",
    "timestamp",
    "user_id",
    "amount_usd",
    "merchant",
    "country",
    "lat",
    "lon",
    "device_id",
    "ip"
]

LABEL_COLUMNS = [
    "tx_id",
    "is_fraud",
    "fraud_type",
    "campaign_id"
]

def ensure_tmp():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)

    os.makedirs(TMP_DIR, exist_ok=True)


def tmp_file(name):
    return os.path.join(TMP_DIR, name)


def read_scored_stream(redis_client):
    last_id = "0-0"

    raw_path = tmp_file("raw.jsonl")
    labels_path = tmp_file("labels.jsonl")

    count = 0

    with open(raw_path, "w", encoding="utf-8") as raw_f, \
         open(labels_path, "w", encoding="utf-8") as label_f:

        logging.info(
            f"Reading Redis stream: {SCORED_STREAM}"
        )

        while True:
            messages = redis_client.xread(
                {SCORED_STREAM: last_id},
                count=STREAM_BATCH_SIZE,
                block=1000
            )

            if not messages:
                break

            for _, events in messages:
                for msg_id, payload in events:
                    try:
                        obj = json.loads(payload["data"])

                        record = obj["features"]

                        raw_row = {
                            col: record.get(col)
                            for col in RAW_COLUMNS
                        }

                        label_row = {
                            col: record.get(col)
                            for col in LABEL_COLUMNS
                        }

                        raw_f.write(
                            json.dumps(raw_row) + "\n"
                        )

                        label_f.write(
                            json.dumps(label_row) + "\n"
                        )

                        count += 1
                        last_id = msg_id

                    except Exception:
                        logging.exception(
                            "Failed parsing scored event"
                        )

    logging.info(f"Exported {count} records to temp")


def upload_df_to_s3(df, s3_client, bucket, key):
    buffer = io.BytesIO()

    df.to_parquet(
        buffer,
        index=False,
        engine="pyarrow"
    )

    buffer.seek(0)

    s3_client.upload_fileobj(
        buffer,
        bucket,
        key
    )

    logging.info(
        f"Uploaded s3://{bucket}/{key}"
    )


def convert_and_upload():

    if os.path.getsize(tmp_file("raw.jsonl")) == 0:
        logging.warning(
            "No transactions found in scored stream"
        )
        return

    s3 = S3Connection()

    raw_df = pd.read_json(
        tmp_file("raw.jsonl"),
        lines=True
    )

    label_df = pd.read_json(
        tmp_file("labels.jsonl"),
        lines=True
    )

    raw_df.drop_duplicates(
        subset=["tx_id"],
        inplace=True
    )

    label_df.drop_duplicates(
        subset=["tx_id"],
        inplace=True
    )

    if len(raw_df) != len(label_df):
        raise ValueError(
            f"Row mismatch: raw={len(raw_df)} labels={len(label_df)}"
        )

    logging.info(
        f"Snapshot size={len(raw_df):,} transactions"
    )

    upload_df_to_s3(
        raw_df,
        s3.s3_client,
        S3_BUCKET,
        "raw/raw.parquet"
    )

    upload_df_to_s3(
        label_df,
        s3.s3_client,
        S3_BUCKET,
        "labels/labels.parquet"
    )

def cleanup():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)

    logging.info("Temporary files cleaned")


def main():
    redis_client = RedisClient().client

    ensure_tmp()

    try:
        read_scored_stream(redis_client)
        convert_and_upload()

    finally:
        cleanup()


if __name__ == "__main__":
    main()