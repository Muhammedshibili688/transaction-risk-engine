import joblib
import shap
import pandas as pd


FEATURES_PATH = (
    "datas/experiments/"
    "features_merchant_transition_score_best_features.parquet"
)

LABELS_PATH = (
    "datas/labels/labels.parquet"
)

MODEL_PATH = (
    "models/xgboost_baseline.joblib"
)

TX_ID = None
# example:
# TX_ID = "9e4f3f16-xxxx"


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

    "merchant_affinity_score",

    "device_merchant_affinity_score",

    "merchant_transition_score"
]


def main():

    features = pd.read_parquet(
        FEATURES_PATH
    )

    labels = pd.read_parquet(
        LABELS_PATH
    )

    df = features.merge(
        labels[
            [
                "tx_id",
                "is_fraud",
                "fraud_type"
            ]
        ],
        on="tx_id"
    )

    if TX_ID is None:

        sample = df[
            df["fraud_type"]
            ==
            "behavioral_mimicry"
        ].sample(
            1,
            random_state=42
        )

    else:

        sample = df[
            df["tx_id"]
            ==
            TX_ID
        ]

    tx = sample.iloc[0]

    X = sample[
        FEATURE_COLUMNS
    ]

    model = joblib.load(
        MODEL_PATH
    )

    probability = (
        model.predict_proba(X)[0][1]
    )

    explainer = shap.Explainer(
        model
    )

    shap_values = explainer(
        X
    )

    contributions = pd.DataFrame(
        {
            "feature":
            FEATURE_COLUMNS,

            "shap_value":
            shap_values.values[0],

            "feature_value":
            X.iloc[0].values
        }
    )

    contributions = (
        contributions
        .reindex(
            contributions[
                "shap_value"
            ]
            .abs()
            .sort_values(
                ascending=False
            )
            .index
        )
    )

    print("\n")
    print("=" * 80)
    print("TRANSACTION EXPLANATION")
    print("=" * 80)

    print(
        f"tx_id: {tx['tx_id']}"
    )

    print(
        f"fraud_type: {tx['fraud_type']}"
    )

    print(
        f"is_fraud: {tx['is_fraud']}"
    )

    print(
        f"fraud_probability: "
        f"{probability:.4f}"
    )

    print("\n")
    print("=" * 80)
    print("TOP FEATURE CONTRIBUTIONS")
    print("=" * 80)

    print(
        contributions.head(10)
        .round(4)
        .to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 80)
    print("POSITIVE FRAUD SIGNALS")
    print("=" * 80)

    print(
        contributions[
            contributions[
                "shap_value"
            ] > 0
        ]
        .head(10)
        .round(4)
        .to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 80)
    print("NEGATIVE FRAUD SIGNALS")
    print("=" * 80)

    print(
        contributions[
            contributions[
                "shap_value"
            ] < 0
        ]
        .head(10)
        .round(4)
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()