import mlflow
import yaml
import pandas as pd
from src.components.model.scorer import FraudScorer
from sklearn.metrics import recall_score, precision_score

def run_heuristic_experiment(config_path: str, data_path: str):
    # 1. Load Rule Config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # 2. Start MLflow Run
    mlflow.set_experiment(config['experiment_name'])
    
    with mlflow.start_run(run_name=f"Trial_{config['rule_version']}"):
        # LOG PARAMS (The rules themselves)
        mlflow.log_params(config['weights'])
        mlflow.log_params(config['thresholds'])

        # 3. RUN EVALUATION
        df = pd.read_json(data_path, lines=True)
        scorer = FraudScorer(config)
        df['risk_score'] = df.apply(lambda x: scorer.calculate_score(x), axis=1)
        df['prediction'] = df['risk_score'].apply(lambda x: 1 if x >= 60 else 0)

        # 4. LOG METRICS
        rec = recall_score(df['is_fraud'], df['prediction'])
        prec = precision_score(df['is_fraud'], df['prediction'])
        
        mlflow.log_metric("recall", rec)
        mlflow.log_metric("precision", prec)

        # 5. TAGGING (The "Best" logic)
        if rec > 0.95 and prec > 0.80:
            mlflow.set_tag("candidate_status", "CHAMPION")
        else:
            mlflow.set_tag("candidate_status", "FAILED")

        print(f"Exp {config['rule_version']} complete. Recall: {rec}")