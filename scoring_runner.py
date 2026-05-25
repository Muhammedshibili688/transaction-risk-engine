import argparse
from src.pipeline.scoring_pipeline import run_scoring

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        required=True,
        help="Path to features jsonl"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Rule config yaml"
    )

    args = parser.parse_args()

    run_scoring(
        input_path=args.data,
        config_path=args.config
    )