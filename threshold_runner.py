import yaml
import os
from src.components.model.model_evaluation import FraudModelEvaluator

FEATURE_PATH = "datas/processed/features.jsonl"
SCORING_PATH = "datas/scoring/latest.jsonl"

THRESHOLDS = range(30, 91, 5)

evaluator = FraudModelEvaluator()
data = evaluator.load_data(FEATURE_PATH, SCORING_PATH)

results = []

for t in THRESHOLDS:
    metrics = evaluator.compute_metrics(data, threshold=t)
    metrics["threshold"] = t
    results.append(metrics)

# find best threshold
best = min(results, key=lambda x: x["total_cost_usd"])

print("\n=== Threshold Optimization ===")
for r in results:
    print(f"T={r['threshold']} → Cost={r['total_cost_usd']}")

print("\nBest Threshold:", best["threshold"])
print("Min Cost:", best["total_cost_usd"])

# update decision.yaml
decision_path = "reports/threshold_optimization/best_threshold.yaml"


os.makedirs(os.path.dirname(decision_path), exist_ok=True)

if os.path.exists(decision_path):
    with open(decision_path, "r") as f:
        config = yaml.safe_load(f) or {}
else:
    config = {}

config["high_risk_threshold"] = best["threshold"]
config["medium_risk_threshold"] = int(best["threshold"] * 0.7)

with open(decision_path, "w") as f:
    yaml.dump(config, f)

print(f"\nUpdated {decision_path}")