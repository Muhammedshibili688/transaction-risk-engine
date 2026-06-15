import pandas as pd
import os


ZSCORE_PATH = (
    "datas/experiments/features_z_score.parquet"
)

HOUR_PATH = (
    "datas/experiments/features_hour_preference.parquet"
)

OUTPUT_PATH = (
    "datas/experiments/features_zscore_hour_preference.parquet"
)


def merge_features():

    zscore_df = pd.read_parquet(
        ZSCORE_PATH
    )

    hour_df = pd.read_parquet(
        HOUR_PATH
    )

    hour_feature = hour_df[
        [
            "tx_id",
            "hour_preference_score"
        ]
    ]

    merged_df = zscore_df.merge(
        hour_feature,
        on="tx_id",
        how="left"
    )

    print(
        f"Rows: {len(merged_df):,}"
    )

    print(
        "Missing hour_preference_score:",
        merged_df[
            "hour_preference_score"
        ].isna().sum()
    )

    os.makedirs(
        "datas/experiments",
        exist_ok=True
    )

    merged_df.to_parquet(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"Saved -> {OUTPUT_PATH}"
    )


if __name__ == "__main__":

    merge_features()