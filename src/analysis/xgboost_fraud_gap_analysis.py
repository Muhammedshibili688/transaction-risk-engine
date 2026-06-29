import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


FEATURES_PATH = (
    "datas/experiments/features_merchant_transition_score_best_features.parquet"
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

    "device_merchant_affinity_score",

    "merchant_transition_score"
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

df["fraud_probability"] = proba

THRESHOLDS = [
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60
]

print("\n")
print("=" * 100)
print("THRESHOLD ANALYSIS")
print("=" * 100)

for threshold in THRESHOLDS:

    prediction = (
        proba >= threshold
    ).astype(int)

    accuracy = accuracy_score(
        y,
        prediction
    )

    precision = precision_score(
        y,
        prediction
    )

    recall = recall_score(
        y,
        prediction
    )

    f1 = f1_score(
        y,
        prediction
    )

    review_rate = (
        prediction.mean()
    )

    print(
        f"Threshold={threshold:.2f} | "
        f"Precision={precision:.4f} | "
        f"Recall={recall:.4f} | "
        f"F1={f1:.4f} | "
        f"ReviewRate={review_rate:.4f}"
    )


print("\n")
print("=" * 100)
print("BEHAVIORAL MIMICRY RECALL")
print("=" * 100)

mimicry = df[
    df["fraud_type"]
    ==
    "behavioral_mimicry"
]


for threshold in THRESHOLDS:

    prediction = (
        mimicry[
            "fraud_probability"
        ]
        >= threshold
    ).astype(int)

    recall = prediction.mean()

    print(
        f"Threshold={threshold:.2f} | "
        f"Mimicry Recall={recall:.4f}"
    )