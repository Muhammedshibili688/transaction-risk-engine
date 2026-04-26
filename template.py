import os
from pathlib import Path

project_name = "src"

list_of_files = [
    f"{project_name}/__init__.py",
    # 1. DATA LAYER (Real-time & Batch)
    f"{project_name}/components/data/__init__.py",
    f"{project_name}/components/data/data_ingestion.py",      # S3 Sync / Snapshotting
    f"{project_name}/components/data/data_validation.py",     # Schema enforcement
    f"{project_name}/components/data/data_transformation.py", # Feature Engine
    
    # 2. MODEL LAYER (Scoring & Training)
    f"{project_name}/components/model/__init__.py",
    f"{project_name}/components/model/scorer.py",            # Risk score (0-100)
    f"{project_name}/components/model/decision_engine.py",   # ALLOW/BLOCK/OTP
    f"{project_name}/components/model/model_trainer.py",     
    f"{project_name}/components/model/model_evaluation.py",
    
    # 3. INFRASTRUCTURE & CONFIG
    f"{project_name}/configuration/__init__.py",
    f"{project_name}/configuration/aws_connection.py",
    f"{project_name}/configuration/redis_connection.py",
    f"{project_name}/constants/__init__.py",
    f"{project_name}/entity/config_entity.py",
    f"{project_name}/entity/artifact_entity.py",
    f"{project_name}/exception/__init__.py",
    f"{project_name}/logger/__init__.py",
    f"{project_name}/pipeline/training_pipeline.py",
    f"{project_name}/pipeline/prediction_pipeline.py",
    
    # 4. ROOT LEVEL
    "app.py",                    # FastAPI Entrypoint
    "simulator.py",              # Producer
    "consumer.py",               # Coordinator
    "requirements.txt",
    "Dockerfile",
    "prometheus.yaml",            # Monitoring Config
    "config/schema.yaml",
    "config/rules.yaml",
    "dvc.yaml"

]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)
    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass