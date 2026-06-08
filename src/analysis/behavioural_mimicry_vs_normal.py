import pandas as pd

FEATURE_PATH = (
    "datas/experiments/"
    "features_affinity_zscore_hour_preference.parquet"
)

LABEL_PATH = (
    "datas/labels/labels.parquet"
)

FEATURE_COLUMNS = [

    "geo_speed",

    "amount_ratio",

    "user_country_ratio",

    "transaction_count_1m",
    "transaction_count_5m",
    "transaction_count_1h",
    "transaction_count_24h",

    "small_amount_burst",

    "merchant_repeat_count",

    "is_new_device",
    "is_new_ip",

    "country_change",

    "z_score",

    "hour_preference_score",

    "merchant_affinity_score"
]


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
        how="inner"
    )

    mimicry = df[
        df["fraud_type"]
        ==
        "behavioral_mimicry"
    ]

    normal = df[
        df["is_fraud"]
        ==
        0
    ]

    rows = []

    for feature in FEATURE_COLUMNS:

        rows.append(
            {
                "feature":
                    feature,

                "normal_mean":
                    round(
                        normal[
                            feature
                        ].mean(),
                        4
                    ),

                "mimicry_mean":
                    round(
                        mimicry[
                            feature
                        ].mean(),
                        4
                    ),

                "difference":
                    round(
                        mimicry[
                            feature
                        ].mean()
                        -
                        normal[
                            feature
                        ].mean(),
                        4
                    )
            }
        )

    summary = pd.DataFrame(
        rows
    )

    summary["abs_diff"] = (
        summary["difference"]
        .abs()
    )

    summary = (
        summary
        .sort_values(
            "abs_diff",
            ascending=False
        )
    )

    print("\n")
    print("=" * 80)
    print("BEHAVIORAL MIMICRY VS NORMAL")
    print("=" * 80)

    print(
        summary[
            [
                "feature",
                "normal_mean",
                "mimicry_mean",
                "difference"
            ]
        ]
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()