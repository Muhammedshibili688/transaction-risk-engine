import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# FEATURES_PATH = (
#     "datas/features/features.parquet"
# )

FEATURES_PATH = (
    "datas/experiments/features_z_score.parquet"
)

LABELS_PATH = (
    "datas/labels/labels.parquet"
)

MODEL_PATH = (
    "models/logistic_regression.joblib"
)

SCALER_PATH = (
    "models/scaler.joblib"
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

    "z_score"
]


def load_data():

    features = pd.read_parquet(
        FEATURES_PATH
    )

    labels = pd.read_parquet(
        LABELS_PATH
    )

    return features, labels


def score_data(
    features
):

    model = joblib.load(
        MODEL_PATH
    )

    scaler = joblib.load(
        SCALER_PATH
    )

    X = features[
        FEATURE_COLUMNS
    ]

    X_scaled = scaler.transform(
        X
    )

    features["prediction"] = (
        model.predict(
            X_scaled
        )
    )

    features["fraud_probability"] = (
        model.predict_proba(
            X_scaled
        )[:, 1]
    )

    return features


def build_analysis_frame():

    features, labels = load_data()

    features = score_data(
        features
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

    return df


def overall_metrics(df):

    accuracy = accuracy_score(
        df["is_fraud"],
        df["prediction"]
    )

    precision = precision_score(
        df["is_fraud"],
        df["prediction"]
    )

    recall = recall_score(
        df["is_fraud"],
        df["prediction"]
    )

    f1 = f1_score(
        df["is_fraud"],
        df["prediction"]
    )

    print("\n")
    print("=" * 80)
    print("OVERALL METRICS")
    print("=" * 80)

    print(
        f"Accuracy : {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall   : {recall:.4f}"
    )

    print(
        f"F1       : {f1:.4f}"
    )


def fraud_type_recall(df):

    frauds = df[
        df["is_fraud"] == 1
    ]

    results = []

    for fraud_type, group in frauds.groupby(
        "fraud_type"
    ):

        total = len(group)

        caught = (
            group["prediction"] == 1
        ).sum()

        missed = (
            group["prediction"] == 0
        ).sum()

        recall = (
            caught / total
        )

        results.append(
            {
                "fraud_type":
                    fraud_type,

                "total_frauds":
                    total,

                "caught_frauds":
                    caught,

                "missed_frauds":
                    missed,

                "recall":
                    round(
                        recall,
                        4
                    )
            }
        )

    summary = pd.DataFrame(
        results
    )

    summary = summary.sort_values(
        by="recall",
        ascending=False
    )

    print("\n")
    print("=" * 80)
    print("FRAUD TYPE RECALL")
    print("=" * 80)

    print(
        summary.to_string(
            index=False
        )
    )

    return summary


def false_negative_analysis(df):

    missed = df[
        (df["is_fraud"] == 1)
        &
        (df["prediction"] == 0)
    ]

    summary = (
        missed["fraud_type"]
        .value_counts()
        .reset_index()
    )

    summary.columns = [
        "fraud_type",
        "missed_count"
    ]

    print("\n")
    print("=" * 80)
    print("MOST MISSED FRAUD TYPES")
    print("=" * 80)

    print(
        summary.to_string(
            index=False
        )
    )

    return missed


def probability_by_fraud_type(df):

    frauds = df[
        df["is_fraud"] == 1
    ]

    results = []

    for fraud_type, group in frauds.groupby(
        "fraud_type"
    ):

        results.append(
            {
                "fraud_type":
                    fraud_type,

                "mean_probability":
                    round(
                        group[
                            "fraud_probability"
                        ].mean(),
                        4
                    ),

                "median_probability":
                    round(
                        group[
                            "fraud_probability"
                        ].median(),
                        4
                    )
            }
        )

    summary = pd.DataFrame(
        results
    )

    print("\n")
    print("=" * 80)
    print("FRAUD PROBABILITY BY TYPE")
    print("=" * 80)

    print(
        summary.to_string(
            index=False
        )
    )


def main():

    df = build_analysis_frame()

    overall_metrics(df)

    fraud_type_recall(df)

    false_negative_analysis(df)

    probability_by_fraud_type(df)


if __name__ == "__main__":
    main()