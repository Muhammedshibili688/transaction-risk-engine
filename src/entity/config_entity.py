from dataclasses import dataclass
from pathlib import Path
import os
from src.constants import PROJECT_ROOT

@dataclass
class DataIngestionConfig:
    """Config for syncing local stream snapshots to the S3 Data Lake."""
    data_dir: Path = PROJECT_ROOT / "datas"
    local_raw_path: Path = data_dir / "fresh" / "transactions.jsonl"
    local_processed_path: Path = data_dir / "processed" / "features.jsonl"
    training_file_path: Path = data_dir / "raw" / "train_snapshot.jsonl"
    s3_processed_key: str = "data/processed/features.jsonl"

@dataclass
class DataValidationConfig:
    """Config for schema enforcement and data quality checks."""
    schema_file_path: Path = PROJECT_ROOT / "config" / "schema.yaml"
    report_dir: Path = PROJECT_ROOT / "reports" / "data_validation"
    report_file_name: str = "status.yaml"

@dataclass
class DataTransformationConfig:
    """Config for feature engineering, scaling, and SMOTE logic."""
    transformed_dir: Path = PROJECT_ROOT / "datas" / "transformed"
    transformed_train_path: Path = transformed_dir / "train.npy"
    transformed_test_path: Path = transformed_dir / "test.npy"
    preprocessor_path: Path = transformed_dir / "preprocessor.pkl"
    # Behavioral features only (dropping unique IDs and 'Cheat' codes)
    drop_columns: tuple = ("tx_id", "user_id", "timestamp", "ip", "device_id", "pattern", "currency")
    target_column: str = "is_fraud"

@dataclass
class ModelTrainerConfig:
    """Config for XGBoost training parameters."""
    model_dir: Path = PROJECT_ROOT / "models" / "ml"
    trained_model_path: Path = model_dir / "fraud_model.pkl"
    expected_accuracy: float = 0.8  # Threshold to push to production
    model_config_path: Path = PROJECT_ROOT / "config" / "model.yaml"

@dataclass
class DecisionConfig:
    """THE DECISION ENGINE CONFIG (Real-time Verdicts)."""
    # Thresholds for the 0-100 Risk Score
    high_risk_threshold: int = 80    # Score >= 80 -> BLOCK
    medium_risk_threshold: int = 50  # Score >= 50 -> CHALLENGE (OTP)
    # Output Stream for bank notifications
    verdict_stream_name: str = "fraud_verdicts"