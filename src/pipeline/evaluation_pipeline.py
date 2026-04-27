import os
import json
from datetime import datetime
import mlflow

from src.components.model.model_evaluation import FraudModelEvaluator


def run_evaluation(feature_path, scoring_path):
    evaluator = FraudModelEvaluator()

    data = evaluator.load_data(feature_path, scoring_path)
    metrics = evaluator.compute_metrics(data)

    os.makedirs("reports/model_evaluation", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"reports/model_evaluation/eval_{timestamp}.json"

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"Evaluation saved to: {output_path}")
    print(metrics)

    with mlflow.start_run(run_name=f"eval_{timestamp}"):

        # Log metrics (important: flatten properly)
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)

        # Log metadata (VERY useful later)
        mlflow.log_param("feature_path", feature_path)
        mlflow.log_param("scoring_path", scoring_path)

        # Log evaluation file
        mlflow.log_artifact(output_path)

        print("Metrics logged to MLflow")