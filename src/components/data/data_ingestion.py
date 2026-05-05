import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from src.exception import FraudException
from src.logger import logging
from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact
from src.configuration.aws_connection import S3Connection

load_dotenv()
TRAINING_BUCKET_NAME = os.getenv("TRAINING_BUCKET_NAME")


class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        try:
            self.config = config
            self.s3 = S3Connection()
            logging.info("Data Ingestion Component Initialized.")
        except Exception as e:
            raise FraudException(e, sys)

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        try:
            logging.info("Downloading Gold Snapshot from S3 for training...")
            self.config.ingested_train_dir.mkdir(parents=True, exist_ok=True)

            target_path = self.config.training_file_path

            self.s3.s3_client.download_file(
                TRAINING_BUCKET_NAME,
                self.config.s3_processed_key,
                str(target_path)
            )

            if target_path.stat().st_size == 0:
                raise Exception("Downloaded snapshot is empty — aborting pipeline")

            logging.info(f"Gold Snapshot downloaded to {target_path}")

            return DataIngestionArtifact(
                trained_file_path=target_path,
                s3_sync_status=True
            )

        except Exception as e:
            raise FraudException(e, sys)


if __name__ == "__main__":
    config = DataIngestionConfig()
    ingestion = DataIngestion(config)
    artifact = ingestion.initiate_data_ingestion()
    print(f"Ingestion Artifact: {artifact}")