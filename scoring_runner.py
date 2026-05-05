# from src.pipeline.scoring_pipeline import run_scoring

# if __name__ == "__main__":
#     input_path = "datas/processed/features.jsonl"

#     run_scoring(input_path)


import argparse
from src.pipeline.scoring_pipeline import run_scoring

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to input parquet file")
    args = parser.parse_args()

    run_scoring(args.data)