from src.pipeline.scoring_pipeline import run_scoring

if __name__ == "__main__":
    input_path = "datas/processed/features.jsonl"

    run_scoring(input_path)