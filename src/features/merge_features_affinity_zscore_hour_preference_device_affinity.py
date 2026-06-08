import pandas as pd
import os


ZSCORE_PATH = (
    "datas/experiments/features_z_score.parquet"
)

HOUR_PATH = (
    "datas/experiments/features_hour_preference.parquet"
)

AFFINITY_PATH = (
    "datas/experiments/features_merchant_affinity.parquet"
)

DEVICE_AFFINITY = (
    "datas/experiments/features_device_merchant_affinity.parquet"
)

OUTPUT_PATH = (
    "datas/experiments/features_affinity_zscore_hour_preference_device_affinity.parquet"
)


def merge_features():

    zscore_df = pd.read_parquet(
        ZSCORE_PATH
    )

    hour_df = pd.read_parquet(
        HOUR_PATH
    )

    affinity_df = pd.read_parquet(
        AFFINITY_PATH
    )

    device_affinity_df = pd.read_parquet(
        DEVICE_AFFINITY
    )

    hour_feature = hour_df[
        [
            "tx_id",
            "hour_preference_score"
        ]
    ]

    affinity_feature = affinity_df[
        [
            "tx_id",
            "merchant_affinity_score"
        ]
    ]

    device_affinity_feature = device_affinity_df[
        [
            "tx_id",
            "device_merchant_affinity_score"
        ]
    ]

    merged_df = (
        zscore_df
        .merge(
            hour_feature,
            on="tx_id",
            how="left"
        )
        .merge(
            affinity_feature,
            on="tx_id",
            how="left"
        )
        .merge(
            device_affinity_feature,
            on="tx_id",
            how="left"
        )
    )


    print(
        f"Rows: {len(merged_df):,}"
    )

    print(merged_df.columns.tolist())

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