import os
import sys
import pandas as pd
import yaml
from src.exception import FraudException
from src.logger import logging
from src.entity.config_entity import DataValidationConfig
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact

class DataValidation:
    def __init__(self, ingestion_artifact: DataIngestionArtifact, config: DataValidationConfig):
        try:
            self.ingestion_artifact = ingestion_artifact
            self.config = config
            with open(self.config.schema_file_path, 'r') as f:
                self.schema = yaml.safe_load(f)
        except Exception as e:
            raise FraudException(e, sys)

    def validate_schema(self, df: pd.DataFrame) -> bool:
        try:
            # Check 1: Column Count
            expected_cols = self.schema['columns'].keys()
            if len(df.columns) != len(expected_cols):
                logging.error(f"Column count mismatch. Expected {len(expected_cols)}, got {len(df.columns)}")
                return False
            
            # Check 2: Column Names & Types
            for col in expected_cols:
                if col not in df.columns:
                    logging.error(f"Missing column: {col}")
                    return False
            
            return True
        except Exception as e:
            raise FraudException(e, sys)

    def initiate_validation(self) -> DataValidationArtifact:
        try:
            logging.info("Starting schema validation...")
            df = pd.read_json(self.ingestion_artifact.trained_file_path, lines=True)
            
            status = self.validate_schema(df)
            
            self.config.report_dir.mkdir(parents=True, exist_ok=True)
            report_path = self.config.report_dir / self.config.report_file_name
            
            with open(report_path, "w") as f:
                yaml.dump({"validation_status": status}, f)
            
            logging.info(f"Validation complete. Status: {status}")
            return DataValidationArtifact(validation_status=status, report_file_path=report_path)
        except Exception as e:
            raise FraudException(e, sys)