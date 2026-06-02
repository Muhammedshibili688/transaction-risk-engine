import os
from pathlib import Path

from dotenv import load_dotenv

from src.configuration.aws_connection import S3Connection
from src.logger import logging

load_dotenv()

S3_BUCKET = os.getenv("TRAINING_BUCKET_NAME")

if not S3_BUCKET:
    raise ValueError(
        "TRAINING_BUCKET_NAME environment variable not set"
    )

DATASETS = {
    "raw/raw.parquet":
        "datas/raw/raw.parquet",

    "features/features.parquet":
        "datas/features/features.parquet",

    "labels/labels.parquet":
        "datas/labels/labels.parquet"
}


class DataIngestion:

    def __init__(self):
        self.s3 = S3Connection()

    def create_directories(self):

        for local_path in DATASETS.values():

            Path(local_path).parent.mkdir(
                parents=True,
                exist_ok=True
            )

    def download_dataset(
        self,
        s3_key,
        local_path
    ):

        logging.info(
            f"Downloading {s3_key}"
        )

        self.s3.s3_client.download_file(
            S3_BUCKET,
            s3_key,
            local_path
        )

        logging.info(
            f"Saved {local_path}"
        )

    def run(self):

        self.create_directories()

        for s3_key, local_path in DATASETS.items():

            self.download_dataset(
                s3_key,
                local_path
            )

        logging.info(
            "Data ingestion completed"
        )


if __name__ == "__main__":

    ingestion = DataIngestion()

    ingestion.run()