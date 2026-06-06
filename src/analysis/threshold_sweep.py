import joblib
import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
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

scaler = joblib.load(
    SCALER_PATH
)

X = scaler.transform(
    df[FEATURE_COLUMNS]
)

proba = model.predict_proba(
    X
)[:,1]

thresholds = [

    0.50,
    0.70
]

results = []

for threshold in thresholds:

    pred = (
        proba >= threshold
    ).astype(int)

    tmp = df.copy()

    tmp["prediction"] = pred

    precision = precision_score(
        df["is_fraud"],
        pred
    )

    recall = recall_score(
        df["is_fraud"],
        pred
    )

    f1 = f1_score(
        df["is_fraud"],
        pred
    )

    tn, fp, fn, tp = (
        confusion_matrix(
            df["is_fraud"],
            pred
        ).ravel()
    )

    fraud_recalls = {}

    for fraud_type, group in (
        tmp[tmp["is_fraud"] == 1]
        .groupby("fraud_type")
    ):

        fraud_recalls[
            fraud_type
        ] = round(
            (
                group["prediction"] == 1
            ).mean(),
            4
        )

    review_rate = (
        (tp + fp)
        /
        len(df)
    )

    results.append(
        {
            "threshold": threshold,

            "precision": round(
                precision,
                4
            ),

            "recall": round(
                recall,
                4
            ),

            "f1": round(
                f1,
                4
            ),

            "review_rate": round(
                review_rate,
                4
            ),

            "ato_recall":
                fraud_recalls.get(
                    "account_takeover",
                    0
                ),

            "card_recall":
                fraud_recalls.get(
                    "card_testing",
                    0
                ),

            "mimicry_recall":
                fraud_recalls.get(
                    "behavioral_mimicry",
                    0
                ),

            "tp": tp,
            "fp": fp,
            "fn": fn
        }
    )
results = pd.DataFrame(
    results
)

from sklearn.metrics import (
    average_precision_score,
    roc_auc_score
)

print("\nMODEL QUALITY")

print(
    "ROC-AUC:",
    round(
        roc_auc_score(
            df["is_fraud"],
            proba
        ),
        4
    )
)

print(
    "PR-AUC:",
    round(
        average_precision_score(
            df["is_fraud"],
            proba
        ),
        4
    )
)

print("\n")
print("=" * 100)
print("THRESHOLD SWEEP")
print("=" * 100)

print(
    results.to_string(
        index=False
    )
)