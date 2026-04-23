from dataclasses import dataclass
from pathlib import Path

@dataclass
class DataIngestionArtifact:
    trained_file_path: Path
    s3_sync_status: bool

@dataclass
class DataValidationArtifact:
    validation_status: bool
    report_file_path: Path

@dataclass
class DataTransformationArtifact:
    transformed_train_path: Path
    transformed_test_path: Path
    preprocessor_path: Path

@dataclass
class ModelTrainerArtifact:
    model_path: Path
    precision: float
    recall: float
    f1_score: float

@dataclass
class DecisionArtifact:
    """The final result of a real-time transaction check."""
    tx_id: str
    risk_score: int
    verdict: str  # ALLOW, BLOCK, or CHALLENGE