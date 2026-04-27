from src.pipeline.evaluation_pipeline import run_evaluation

FEATURE_PATH = "datas/processed/features.jsonl"
SCORING_PATH = "datas/scoring/Heuristic_Discovery_v1_0_run1_20260426_224537.jsonl"

if __name__ == "__main__":
    run_evaluation(FEATURE_PATH, SCORING_PATH)