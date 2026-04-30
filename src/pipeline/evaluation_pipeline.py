# import os
# import json
# from datetime import datetime
# import mlflow
# import dagshub
# from dotenv import load_dotenv
# from src.components.model.model_evaluation import FraudModelEvaluator
# from src.pipeline.scoring_pipeline import load_rule_config


# def run_evaluation(feature_path, scoring_path):

#     load_dotenv()
#     repo_owner = os.getenv("DAGSHUB_USERNAME")
#     repo_name = os.getenv("DAGSHUB_REPO_NAME")

#     dagshub.init(repo_owner=repo_owner, repo_name=repo_name)
#     mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")

#     rule_config = load_rule_config()
#     mlflow.set_experiment(rule_config["experiment_name"])

#      # =================================================

#     evaluator = FraudModelEvaluator()

#     data = evaluator.load_data(feature_path, scoring_path)
#     metrics = evaluator.compute_metrics(data)

#     os.makedirs("reports/model_evaluation", exist_ok=True)

#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     output_path = f"reports/model_evaluation/eval_{timestamp}.json"

#     with open(output_path, "w") as f:
#         json.dump(metrics, f, indent=4)

#     print(f"Evaluation saved to: {output_path}")
#     print(metrics)

#     with mlflow.start_run(run_name=f"eval_{timestamp}"):

#         # Log metrics (important: flatten properly)
#         for key, value in metrics.items():
#             if isinstance(value, (int, float)):
#                 mlflow.log_metric(key, value)

#         # Log metadata (VERY useful later)
#         mlflow.log_param("feature_path", feature_path)
#         mlflow.log_param("scoring_path", scoring_path)

#         # Log evaluation file
#         mlflow.log_artifact(output_path)

#         print("Metrics logged to MLflow")


import os
import json
from datetime import datetime
import mlflow
import dagshub
from dotenv import load_dotenv

from src.components.model.model_evaluation import FraudModelEvaluator
from src.pipeline.scoring_pipeline import load_rule_config


def run_evaluation(feature_path, scoring_path):

    # ------------------ MLflow Setup ------------------
    load_dotenv()
    repo_owner = os.getenv("DAGSHUB_USERNAME")
    repo_name = os.getenv("DAGSHUB_REPO_NAME")

    dagshub.init(repo_owner=repo_owner, repo_name=repo_name)
    mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")

    rule_config = load_rule_config()
    mlflow.set_experiment(rule_config["experiment_name"])

    # ------------------ Evaluation ------------------
    evaluator = FraudModelEvaluator()

    data = evaluator.load_data(feature_path, scoring_path)
    metrics = evaluator.compute_metrics(data)

    os.makedirs("reports/model_evaluation", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"reports/model_evaluation/eval_{timestamp}.json"

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=4)

    print(metrics)

    # ------------------ MLflow Run ------------------
    with mlflow.start_run(run_name=f"{rule_config['rule_version']}_{timestamp}"):

        #  LOG METRICS
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)

        #  LOG RULE CONFIG (CRITICAL)
        mlflow.log_param("rule_version", rule_config.get("rule_version"))

        for k, v in rule_config.get("thresholds", {}).items():
            mlflow.log_param(k, v)

        for k, v in rule_config.get("weights", {}).items():
            mlflow.log_param(k, v)

        #  LOG INPUT PATHS
        mlflow.log_param("feature_path", feature_path)
        mlflow.log_param("scoring_path", scoring_path)

        #  LOG ARTIFACT
        mlflow.log_artifact(output_path)

        print("Logged to MLflow")