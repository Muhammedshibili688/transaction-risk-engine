import os
import sys
import pandas as pd
import shutil
from pathlib import Path
from src.exception import FraudException
from src.logger import logging
from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact
from src.configuration.aws_connection import S3Connection
from src.constants import MAX_RECORDS_TO_KEEP

TRAINING_BUCKET_NAME = os.getenv("TRAINING_BUCKET_NAME")

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        """
        Handles the lifecycle of data from local landing zones to S3 Cloud Warehouse.
        """
        try:
            self.config = config
            self.s3 = S3Connection()
            logging.info("Data Ingestion Component Initialized.")
        except Exception as e:
            raise FraudException(e, sys)

    def _move_root_files_to_data_dir(self):
        """Cleanup: Relocates simulator/consumer output if they hit project root instead of /datas."""
        try:
            mapping = {
                "transactions.jsonl": self.config.local_fresh_path,
                "features.jsonl": self.config.local_processed_path
            }
            for file_name, target_path in mapping.items():
                root_file = self.config.project_root / file_name
                if root_file.exists():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(root_file), str(target_path))
                    logging.info(f"Relocated {file_name} to {target_path}")
        except Exception as e:
            raise FraudException(e, sys)

    def _process_sliding_window(self, landing_zone: Path, s3_key: str) -> pd.DataFrame:
        """
        1. Downloads current S3 Gold file.
        2. Merges with new Landing Zone data.
        3. Deduplicates and Trims to 400k.
        4. Wipes Landing Zone.
        """
        temp_file = "temp_download.jsonl"
        try:
            # Load NEW data
            new_df = pd.read_json(landing_zone, lines=True)

            # Try to merge with EXISTING S3 data
            try:
                self.s3.s3_client.download_file(TRAINING_BUCKET_NAME, s3_key, temp_file)
                s3_df = pd.read_json(temp_file, lines=True)
                combined_df = pd.concat([s3_df, new_df], ignore_index=True)
                logging.info(f"Merging {len(new_df)} new records with {len(s3_df)} existing records.")
            except Exception:
                logging.info(f"S3 Key {s3_key} not found. Starting fresh.")
                combined_df = new_df

            # Deduplicate and Cap at 400k
            combined_df.drop_duplicates(subset=['tx_id'], keep='first', inplace=True)
            if len(combined_df) > MAX_RECORDS_TO_KEEP:
                logging.info(f"Trimming window: {len(combined_df)} -> {MAX_RECORDS_TO_KEEP}")
                combined_df = combined_df.tail(MAX_RECORDS_TO_KEEP)

            # WIPE Landing Zone (Prevent double ingestion)
            with open(landing_zone, 'w') as f: pass
            logging.info(f"Landing zone {landing_zone.name} cleared.")

            return combined_df

        finally:
            if os.path.exists(temp_file): os.remove(temp_file)

    def sync_data_to_s3(self):
        """Synchronizes Fresh and Processed data to S3."""
        try:
            logging.info("Starting Data Sync to S3 Warehouse...")
            self._move_root_files_to_data_dir()

            # 1. Sync FRESH Zone (Raw Backup)
            if self.config.local_fresh_path.exists() and os.path.getsize(self.config.local_fresh_path) > 0:
                final_fresh = self._process_sliding_window(self.config.local_fresh_path, self.config.s3_raw_backup_key)
                
                # Save locally temporarily to upload
                final_fresh.to_json("temp_fresh.jsonl", orient='records', lines=True)
                self.s3.s3_client.upload_file("temp_fresh.jsonl", TRAINING_BUCKET_NAME, self.config.s3_raw_backup_key)
                os.remove("temp_fresh.jsonl")
                logging.info("Raw Fresh Zone synced to S3.")

            # 2. Sync PROCESSED Zone (ML Feature Snapshot)
            if self.config.local_processed_path.exists() and os.path.getsize(self.config.local_processed_path) > 0:
                final_processed = self._process_sliding_window(self.config.local_processed_path, self.config.s3_processed_key)
                
                # Save locally temporarily to upload
                final_processed.to_json("temp_processed.jsonl", orient='records', lines=True)
                self.s3.s3_client.upload_file("temp_processed.jsonl", TRAINING_BUCKET_NAME, self.config.s3_processed_key)
                os.remove("temp_processed.jsonl")
                logging.info("Enriched Processed Zone synced to S3.")

        except Exception as e:
            raise FraudException(e, sys)

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        """
        Final Step: Pulls the Gold Snapshot from S3 into 'datas/raw/' 
        to be used for Validation and Training.
        """
        try:
            logging.info("Downloading Gold Snapshot from S3 for training...")
            self.config.ingested_train_dir.mkdir(parents=True, exist_ok=True)
            
            target_path = self.config.training_file_path
            
            try:
                self.s3.s3_client.download_file(
                    TRAINING_BUCKET_NAME, 
                    self.config.s3_processed_key, 
                    str(target_path)
                )
                sync_status = True
            except Exception as e:
                logging.error(f"Failed to pull Gold Snapshot: {e}")
                # Create empty file so pipeline doesn't crash on first run
                with open(target_path, 'w') as f: pass
                sync_status = False

            return DataIngestionArtifact(
                trained_file_path=target_path,
                s3_sync_status=sync_status
            )
        except Exception as e:
            raise FraudException(e, sys)

if __name__ == "__main__":
    # Test script for the ingestion stage
    config = DataIngestionConfig()
    ingestion = DataIngestion(config)
    ingestion.sync_data_to_s3()
    artifact = ingestion.initiate_data_ingestion()
    print(f"Ingestion Artifact: {artifact}")