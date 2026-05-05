import argparse
from src.pipeline.evaluation_pipeline import run_evaluation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    FEATURE_PATH = args.data                        # ← parquet snapshot
    SCORING_PATH = "datas/scoring/latest.jsonl"

    run_evaluation(FEATURE_PATH, SCORING_PATH)