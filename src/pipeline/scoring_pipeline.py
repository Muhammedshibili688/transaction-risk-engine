import json
import os
from datetime import datetime
import yaml

from src.components.model.scorer import FraudScorer
from src.components.model.decision_engine import DecisionEngine
from src.entity.config_entity import DecisionConfig


# -------------------------
# LOAD YAML CONFIG
# -------------------------
def load_rule_config(path="config/rules/baseline.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


# -------------------------
# EXTRACT METADATA
# -------------------------
def extract_metadata(rule_config: dict):
    experiment = rule_config.get("experiment_name", "experiment")
    version = rule_config.get("rule_version", "v0")

    # sanitize for filenames
    experiment = experiment.replace(" ", "_")
    version = version.replace(".", "_")

    return experiment, version


# -------------------------
# AUTO RUN NUMBER
# -------------------------
def get_next_run_number(base_dir, experiment, version):
    existing = [
        f for f in os.listdir(base_dir)
        if f.startswith(f"{experiment}_{version}")
    ]

    runs = []
    for f in existing:
        parts = f.split("_")
        for p in parts:
            if p.startswith("run"):
                try:
                    runs.append(int(p.replace("run", "")))
                except:
                    pass

    return max(runs, default=0) + 1


# -------------------------
# MAIN PIPELINE
# -------------------------
def run_scoring(input_path: str):

    rule_config = load_rule_config()
    scorer = FraudScorer(rule_config)
    decider = DecisionEngine(DecisionConfig())

    base_dir = "datas/scoring"
    os.makedirs(base_dir, exist_ok=True)

    experiment, version = extract_metadata(rule_config)
    run_number = get_next_run_number(base_dir, experiment, version)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = os.path.join(
        base_dir,
        f"{experiment}_{version}_run{run_number}_{timestamp}.jsonl"
    )

    processed = 0

    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        for line in fin:
            tx = json.loads(line)

            score = scorer.calculate_heuristic_score(tx)
            verdict = decider.get_verdict(score)

            result = {
                "tx_id": tx["tx_id"],
                "risk_score": score,
                "verdict": verdict
            }

            fout.write(json.dumps(result) + "\n")
            processed += 1

    print(f"Run {run_number} complete → {output_path}")
    print(f"Processed: {processed} records")