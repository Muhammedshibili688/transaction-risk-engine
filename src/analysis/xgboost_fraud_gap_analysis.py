import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


FEATURES_PATH = (
    "datas/experiments/features_affinity_zscore_hour_preference_device_affinity.parquet"
)

LABELS_PATH = (
    "datas/labels/labels.parquet"
)

MODEL_PATH = (
    "models/xgboost_baseline.joblib"
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
    
    "merchant_affinity_score",

    "device_merchant_affinity_score"
]


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

model = joblib.load(
    MODEL_PATH
)

X = df[
    FEATURE_COLUMNS
]

y = df[
    "is_fraud"
]

proba = model.predict_proba(
    X
)[:, 1]

prediction = (
    proba >= 0.50
).astype(int)

df["prediction"] = prediction
df["fraud_probability"] = proba

print("\n")
print("=" * 80)
print("OVERALL METRICS")
print("=" * 80)

print(
    "Accuracy :",
    round(
        accuracy_score(
            y,
            prediction
        ),
        4
    )
)

print(
    "Precision:",
    round(
        precision_score(
            y,
            prediction
        ),
        4
    )
)

print(
    "Recall   :",
    round(
        recall_score(
            y,
            prediction
        ),
        4
    )
)

print(
    "F1       :",
    round(
        f1_score(
            y,
            prediction
        ),
        4
    )
)

print("\n")
print("=" * 80)
print("FRAUD TYPE RECALL")
print("=" * 80)

results = []

for fraud_type in sorted(
    df["fraud_type"]
    .dropna()
    .unique()
):

    subset = df[
        df["fraud_type"]
        == fraud_type
    ]

    total_frauds = len(
        subset
    )

    caught_frauds = (
        subset[
            "prediction"
        ]
        .sum()
    )

    missed_frauds = (
        total_frauds
        -
        caught_frauds
    )

    recall = (
        caught_frauds
        /
        total_frauds
    )

    results.append(
        {
            "fraud_type":
            fraud_type,

            "total_frauds":
            total_frauds,

            "caught_frauds":
            caught_frauds,

            "missed_frauds":
            missed_frauds,

            "recall":
            round(
                recall,
                4
            )
        }
    )

results = pd.DataFrame(
    results
)

print(
    results.to_string(
        index=False
    )
)

print("\n")
print("=" * 80)
print("MOST MISSED FRAUD TYPES")
print("=" * 80)

print(
    results[
        [
            "fraud_type",
            "missed_frauds"
        ]
    ]
    .sort_values(
        "missed_frauds",
        ascending=False
    )
    .to_string(
        index=False
    )
)

print("\n")
print("=" * 80)
print("FRAUD PROBABILITY BY TYPE")
print("=" * 80)

probability_summary = (
    df[
        df["is_fraud"] == 1
    ]
    .groupby(
        "fraud_type"
    )[
        "fraud_probability"
    ]
    .agg(
        [
            "mean",
            "median"
        ]
    )
    .reset_index()
)

probability_summary.columns = [

    "fraud_type",

    "mean_probability",

    "median_probability"
]

print(
    probability_summary
    .round(4)
    .to_string(
        index=False
    )
)