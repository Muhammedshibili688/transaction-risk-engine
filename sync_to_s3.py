import os
import sys
import pandas as pd
import shutil
from pathlib import Path
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig

from src.exception import FraudException
from src.logger import logging
from src.entity.config_entity import DataIngestionConfig
from src.configuration.aws_connection import S3Connection
from src.constants import MAX_RECORDS_TO_KEEP

load_dotenv()
TRAINING_BUCKET_NAME = os.getenv("TRAINING_BUCKET_NAME")


def move_root_files_to_data_dir(config, s3):
    mapping = {
        "transactions.jsonl": config.local_fresh_path,
        "features.jsonl": config.local_processed_path
    }
    for file_name, target_path in mapping.items():
        root_file = config.project_root / file_name
        if root_file.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(root_file), str(target_path))
            logging.info(f"Relocated {file_name} to {target_path}")


def process_sliding_window(s3, landing_zone: Path, s3_key: str) -> pd.DataFrame:
    temp_file = "temp_download.parquet"
    try:
        new_df = pd.read_json(landing_zone, lines=True)

        try:
            s3.s3_client.download_file(TRAINING_BUCKET_NAME, s3_key, temp_file)
            s3_df = pd.read_parquet(temp_file)
            combined_df = pd.concat([s3_df, new_df], ignore_index=True)
            logging.info(f"Merging {len(new_df)} new records with {len(s3_df)} existing records.")
        except Exception:
            logging.info(f"S3 Key {s3_key} not found. Starting fresh.")
            combined_df = new_df

        combined_df.drop_duplicates(subset=['tx_id'], keep='first', inplace=True)
        if len(combined_df) > MAX_RECORDS_TO_KEEP:
            logging.info(f"Trimming window: {len(combined_df)} -> {MAX_RECORDS_TO_KEEP}")
            combined_df = combined_df.tail(MAX_RECORDS_TO_KEEP)

        return combined_df

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def sync_data_to_s3(config, s3):
    transfer_config = TransferConfig(
        multipart_threshold=10 * 1024 * 1024,
        multipart_chunksize=10 * 1024 * 1024,
        max_concurrency=2,
        use_threads=True
    )

    # 1. Fresh Zone
    if config.local_fresh_path.exists() and os.path.getsize(config.local_fresh_path) > 0:
        final_fresh = process_sliding_window(s3, config.local_fresh_path, config.s3_raw_backup_key)
        final_fresh.to_parquet("temp_fresh.parquet", index=False)
        s3.s3_client.upload_file("temp_fresh.parquet", TRAINING_BUCKET_NAME, config.s3_raw_backup_key, Config=transfer_config)
        os.remove("temp_fresh.parquet")
        with open(config.local_fresh_path, 'w') as f: pass
        logging.info("Raw Fresh Zone synced to S3.")

    # 2. Processed Zone
    if config.local_processed_path.exists() and os.path.getsize(config.local_processed_path) > 0:
        final_processed = process_sliding_window(s3, config.local_processed_path, config.s3_processed_key)
        final_processed.to_parquet("temp_processed.parquet", index=False)
        s3.s3_client.upload_file("temp_processed.parquet", TRAINING_BUCKET_NAME, config.s3_processed_key, Config=transfer_config)
        os.remove("temp_processed.parquet")
        with open(config.local_processed_path, 'w') as f: pass
        logging.info("Enriched Processed Zone synced to S3.")


if __name__ == "__main__":
    config = DataIngestionConfig()
    s3 = S3Connection()
    move_root_files_to_data_dir(config, s3)
    sync_data_to_s3(config, s3)
    print("Sync complete.")