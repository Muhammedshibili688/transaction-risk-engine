import mlflow
import yaml
import pandas as pd
import os
import sys
import json
from src.components.model.scorer import FraudScorer
from sklearn.metrics import recall_score, precision_score
from src.logger import logging
from src.exception import FraudException
import dagshub
from dotenv import load_dotenv

def run_heuristic_experiment(config_path: str, data_path: str):
    try:
        # 1. LOAD ENVIRONMENT & AUTHENTICATE (Crucial for DVC)
        load_dotenv()
        repo_owner = os.getenv("DAGSHUB_USERNAME")
        repo_name = os.getenv("DAGSHUB_REPO_NAME")
        
        # This line "unlocks" the door to Dagshub
        dagshub.init(repo_owner=repo_owner, repo_name=repo_name)
        mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")

        # 2. Load Rule Config
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # 3. Now set_experiment will work because we are authenticated
        mlflow.set_experiment(config['experiment_name'])

        # 1. Load Rule Config
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # 2. Start MLflow Run (Connects to Dagshub automatically if initialized)
        mlflow.set_experiment(config['experiment_name'])
        
        with mlflow.start_run(run_name=f"Heuristic_Trial_{config['rule_version']}"):
            # Log Parameters from YAML
            mlflow.log_params(config['weights'])
            mlflow.log_params(config['thresholds'])

            # 3. RUN EVALUATION
            logging.info(f"Evaluating heuristic rules on {data_path}...")
            df = pd.read_json(data_path, lines=True)
            
            scorer = FraudScorer(config)
            # Apply the scoring logic
            df['risk_score'] = df.apply(lambda x: scorer.calculate_heuristic_score(x), axis=1)
            df['prediction'] = df['risk_score'].apply(lambda x: 1 if x >= 60 else 0)

            # 4. CALCULATE METRICS
            rec = recall_score(df['is_fraud'], df['prediction'], zero_division=0)
            prec = precision_score(df['is_fraud'], df['prediction'], zero_division=0)
            
            # Log to MLflow
            mlflow.log_metric("recall", rec)
            mlflow.log_metric("precision", prec)

            # 5. OUTPUT FOR DVC
            # DVC needs a physical file to track metrics
            metrics = {
                "recall": float(rec),
                "precision": float(prec),
                "rule_version": config['rule_version']
            }
            
            os.makedirs("reports", exist_ok=True)
            with open("reports/metrics.json", "w") as f:
                json.dump(metrics, f, indent=4)

            logging.info(f"Baseline complete. Recall: {rec:.4f} | Precision: {prec:.4f}")

    except Exception as e:
        raise FraudException(e, sys)

if __name__ == "__main__":
    # DVC execution paths
    CONFIG_FILE = "config/rules/baseline.yaml"
    DATA_FILE = "datas/raw/train_snapshot.jsonl"
    
    run_heuristic_experiment(CONFIG_FILE, DATA_FILE)