import os
import sys
import pandas as pd
import yaml
from pathlib import Path
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
            # Logic: Check if all columns from schema.yaml exist in the dataframe
            expected_cols = list(self.schema['columns'].keys())
            actual_cols = df.columns.tolist()
            
            status = True
            for col in expected_cols:
                if col not in actual_cols:
                    logging.error(f"Validation Error: Column [{col}] is missing from data.")
                    status = False
            
            return status
        except Exception as e:
            raise FraudException(e, sys)

    def initiate_validation(self) -> DataValidationArtifact:
        try:
            logging.info("Starting schema validation stage...")
            
            # 1. Load Data
            df = pd.read_json(self.ingestion_artifact.trained_file_path, lines=True)
            
            # 2. Perform Check
            validation_status = self.validate_schema(df)
            
            # 3. CRITICAL: Create directory and write the file DVC is waiting for
            self.config.report_dir.mkdir(parents=True, exist_ok=True)
            report_path = self.config.report_dir / self.config.report_file_name
            
            report_data = {
                "validation_status": validation_status,
                "record_count": len(df),
                "file_validated": str(self.ingestion_artifact.trained_file_path)
            }
            
            with open(report_path, "w") as f:
                yaml.dump(report_data, f)
            
            logging.info(f"Validation report saved at: {report_path}")
            
            return DataValidationArtifact(
                validation_status=validation_status,
                report_file_path=report_path
            )
        except Exception as e:
            raise FraudException(e, sys)

# --- ADD THIS BLOCK FOR DVC SUPPORT ---
if __name__ == "__main__":
    from src.entity.config_entity import DataIngestionConfig
    
    # 1. Setup artifacts from the previous stage
    ing_config = DataIngestionConfig()
    ing_artifact = DataIngestionArtifact(
        trained_file_path=ing_config.training_file_path,
        s3_sync_status=True
    )
    
    # 2. Run validation
    val_config = DataValidationConfig()
    validator = DataValidation(ing_artifact, val_config)
    validator.initiate_validation()