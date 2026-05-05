import os
import yaml
import shutil
import mlflow
import dagshub
from dotenv import load_dotenv
from datetime import datetime

from src.pipeline.scoring_pipeline import run_scoring
from src.components.model.model_evaluation import FraudModelEvaluator


# -----------------------------
# CONFIG SPACE (EDIT THIS ONLY)
# -----------------------------
CONFIGS = [
    {
        "name": "baseline",
        "thresholds": {
            "geo_speed_limit": 1050,
            "amount_ratio_limit": 3.0,
            "switch_count_limit": 3
        },
        "weights": {
            "impossible_travel": 70,
            "new_device": 20,
            "high_risk_merchant": 20
        }
    },
    {
        "name": "geo_aggressive",
        "thresholds": {
            "geo_speed_limit": 900,
            "amount_ratio_limit": 3.0,
            "switch_count_limit": 3
        },
        "weights": {
            "impossible_travel": 85,
            "new_device": 15,
            "high_risk_merchant": 15
        }
    },
    {
        "name": "device_focus",
        "thresholds": {
            "geo_speed_limit": 1050,
            "amount_ratio_limit": 3.0,
            "switch_count_limit": 2
        },
        "weights": {
            "impossible_travel": 60,
            "new_device": 30,
            "high_risk_merchant": 20
        }
    },
    {
        "name": "balanced",
        "thresholds": {
            "geo_speed_limit": 1000,
            "amount_ratio_limit": 2.5,
            "switch_count_limit": 3
        },
        "weights": {
            "impossible_travel": 65,
            "new_device": 25,
            "high_risk_merchant": 25
        }
    }
]


FEATURE_PATH = "datas/processed/features.jsonl"
SCORING_PATH = "datas/scoring/latest.jsonl"
RULE_PATH = "config/rules.yaml"


# -----------------------------
# HELPERS
# -----------------------------
def write_rule_config(config):
    rule_config = {
        "experiment_name": "Heuristic_Experiment",
        "rule_version": config["name"],
        "thresholds": config["thresholds"],
        "weights": config["weights"]
    }

    with open(RULE_PATH, "w") as f:
        yaml.dump(rule_config, f)


def find_best_threshold(data, evaluator):
    thresholds = range(30, 91, 5)
    results = []

    for t in thresholds:
        metrics = evaluator.compute_metrics(data, threshold=t)
        metrics["threshold"] = t
        results.append(metrics)

    best = min(results, key=lambda x: x["total_cost_usd"])
    return best, results


# -----------------------------
# MAIN EXPERIMENT LOOP
# -----------------------------
def run_experiments():

    # MLflow setup
    load_dotenv()
    repo_owner = os.getenv("DAGSHUB_USERNAME")
    repo_name = os.getenv("DAGSHUB_REPO_NAME")

    dagshub.init(repo_owner=repo_owner, repo_name=repo_name)
    mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")
    mlflow.set_experiment("Rule_Optimization")

    evaluator = FraudModelEvaluator()
    final_results = []

    for cfg in CONFIGS:

        print(f"\n=== Running Config: {cfg['name']} ===")

        # 1. write config
        write_rule_config(cfg)

        # 2. run scoring
        run_scoring(FEATURE_PATH)

        # 3. load data
        data = evaluator.load_data(FEATURE_PATH, SCORING_PATH)

        # 4. threshold optimization
        best, all_results = find_best_threshold(data, evaluator)

        # 5. MLflow logging
        with mlflow.start_run(run_name=cfg["name"]):

            # params
            mlflow.log_params(cfg["weights"])
            mlflow.log_params(cfg["thresholds"])

            # best metrics
            mlflow.log_metric("best_threshold", best["threshold"])
            mlflow.log_metric("total_cost", best["total_cost_usd"])
            mlflow.log_metric("expected_loss", best["expected_loss_usd"])
            mlflow.log_metric("precision", best["precision"])
            mlflow.log_metric("recall", best["recall"])

        final_results.append({
            "config": cfg["name"],
            "threshold": best["threshold"],
            "total_cost": best["total_cost_usd"],
            "expected_loss": best["expected_loss_usd"]
        })

    # -----------------------------
    # FINAL RANKING
    # -----------------------------
    final_results = sorted(final_results, key=lambda x: x["total_cost"])

    print("\n=== FINAL RANKING ===")
    for r in final_results:
        print(r)

    print("\nBEST CONFIG:")
    print(final_results[0])


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    run_experiments()