import pandas as pd

FEATURE_PATH = (
    "datas/experiments/"
    "features_affinity_zscore_hour_preference_device_affinity.parquet"
)

LABEL_PATH = (
    "datas/labels/labels.parquet"
)


def main():

    features = pd.read_parquet(
        FEATURE_PATH
    )

    labels = pd.read_parquet(
        LABEL_PATH
    )

    df = features.merge(
        labels[
            [
                "tx_id",
                "is_fraud",
                "fraud_type"
            ]
        ],
        on="tx_id",
        how="left"
    )

    velocity_cols = [
        "transaction_count_1m",
        "transaction_count_5m",
        "transaction_count_1h"
    ]

    print("\n")
    print("=" * 80)
    print("OVERALL VELOCITY DISTRIBUTION")
    print("=" * 80)

    print(
        df[
            velocity_cols
        ].describe()
    )

    for col in velocity_cols:

        print("\n")
        print("=" * 80)
        print(f"{col} VALUE COUNTS")
        print("=" * 80)

        print(
            df[col]
            .value_counts()
            .sort_index()
            .head(30)
        )

    print("\n")
    print("=" * 80)
    print("CARD TESTING ONLY")
    print("=" * 80)

    card = df[
        df["fraud_type"] == "card_testing"
    ]

    print(
        card[
            velocity_cols
        ].describe()
    )

    for col in velocity_cols:

        print("\n")
        print("=" * 80)
        print(
            f"CARD TESTING {col}"
        )
        print("=" * 80)

        print(
            card[col]
            .value_counts()
            .sort_index()
            .head(50)
        )

    print("\n")
    print("=" * 80)
    print("BEHAVIORAL MIMICRY ONLY")
    print("=" * 80)

    mimicry = df[
        df["fraud_type"] == "behavioral_mimicry"
    ]

    print(
        mimicry[
            velocity_cols
        ].describe()
    )

    print("\n")
    print("=" * 80)
    print("HIGH VELOCITY ROWS")
    print("=" * 80)

    high_velocity = df[
        (
            df["transaction_count_1m"] > 3
        )
        |
        (
            df["transaction_count_5m"] > 5
        )
    ]

    print(
        f"Rows: {len(high_velocity):,}"
    )

    print(
        high_velocity[
            [
                "fraud_type",
                "transaction_count_1m",
                "transaction_count_5m",
                "transaction_count_1h"
            ]
        ]
        .head(50)
    )

    print("\n")
    print("=" * 80)
    print("FRAUD RATE BY VELOCITY")
    print("=" * 80)

    for col in velocity_cols:

        summary = (
            df.groupby(col)
            ["is_fraud"]
            .mean()
            .reset_index()
        )

        print("\n")
        print(col)

        print(
            summary.head(20)
        )


if __name__ == "__main__":
    main()