import os
import pandas as pd

from src.logger import logging

FEATURE_COLUMNS = [
    "risk_score",
    "amount_ratio",
    "user_country_ratio",
    "geo_speed",
    "transaction_count_1m",
    "transaction_count_5m",
    "transaction_count_1h",
    "transaction_count_24h",
    "merchant_repeat_count",
    "small_amount_burst",
    "z_score",
    "merchant_affinity_score"
]

PREDICTIONS_PATH = (
    "datas/predictions/"
    "v1.0_geo800_amt2.5_sw5_dev40_ip5_cc40_imp10.parquet"
)

LABELS_PATH = (
    "datas/labels/labels.parquet"
)

FATURES_PATH = (
    "datas/experiments/features_affinity_zscore_hour_preference.parquet"
    )

REPORT_DIR = "reports"


def load_data():

    predictions = pd.read_parquet(
        PREDICTIONS_PATH
    )

    labels = pd.read_parquet(
        LABELS_PATH
    )

    features = pd.read_parquet(
        FATURES_PATH
        )

    logging.info(
        f"Predictions={len(predictions):,}"
    )

    logging.info(
        f"Labels={len(labels):,}"
    )

    return predictions, labels, features


def build_analysis_frame(
    predictions,
    labels,
    features
):

    df = (
        predictions
            .merge(
                labels,
                on="tx_id",
                suffixes=(
                    "_pred",
                    "_label"
                )
            )
            .merge(
                features,
                on="tx_id"
            )
    )
    

    print(df[
        [
            "is_fraud_pred",
            "is_fraud_label"
        ]
    ].head())

    if "is_fraud_label" in df.columns:
        df["is_fraud"] = df["is_fraud_label"]

    elif "is_fraud" in df.columns:
        pass

    else:
        raise ValueError(
            "Ground truth label column not found"
        )
    
    if "fraud_type_label" in df.columns:
        df["fraud_type"] = df["fraud_type_label"]

    elif "fraud_type" in df.columns:
        pass

    else:
        raise ValueError(
            "fraud_type column not found"
        )

    logging.info(
        f"Merged={len(df):,}"
    )

    return df


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
            if total > 0
            else 0
        )

        results.append(
            {
                "fraud_type": fraud_type,
                "total_frauds": total,
                "caught_frauds": caught,
                "missed_frauds": missed,
                "recall": round(
                    recall,
                    4
                )
            }
        )

    summary = pd.DataFrame(
        results
    )

    summary.sort_values(
        by="recall",
        ascending=True,
        inplace=True
    )

    return summary


def false_negative_analysis(df):

    missed = df[
        (df["is_fraud"] == 1)
        &
        (df["prediction"] == 0)
    ].copy()

    summary = (
        missed["fraud_type"]
        .value_counts()
        .reset_index()
    )

    summary.columns = [
        "fraud_type",
        "missed_count"
    ]

    return missed, summary

def fraud_type_describe_reports(df):

    frauds = df[
        df["is_fraud"] == 1
    ]

    for fraud_type, group in frauds.groupby(
        "fraud_type"
    ):

        path = (
            f"{REPORT_DIR}/"
            f"{fraud_type}_describe.csv"
        )

        group[
            FEATURE_COLUMNS
        ].describe().to_csv(path)

        logging.info(
            f"Saved {path}"
        )

def missed_fraud_describe_reports(df):

    missed = df[
        (df["is_fraud"] == 1)
        &
        (df["prediction"] == 0)
    ]

    for fraud_type, group in missed.groupby(
        "fraud_type"
    ):

        path = (
            f"{REPORT_DIR}/"
            f"missed_{fraud_type}_describe.csv"
        )

        group[
            FEATURE_COLUMNS
        ].describe().to_csv(path)

        logging.info(
            f"Saved {path}"
        )

def fraud_comparison_reports(df):

    frauds = df[
        df["is_fraud"] == 1
    ]

    for fraud_type, group in frauds.groupby(
        "fraud_type"
    ):

        caught = group[
            group["prediction"] == 1
        ]

        missed = group[
            group["prediction"] == 0
        ]

        rows = []

        for feature in FEATURE_COLUMNS:

            rows.append(
                {
                    "feature": feature,

                    "caught_mean":
                        round(
                            caught[feature].mean(),
                            4
                        ),

                    "missed_mean":
                        round(
                            missed[feature].mean(),
                            4
                        ),

                    "difference":
                        round(
                            caught[feature].mean()
                            -
                            missed[feature].mean(),
                            4
                        )
                }
            )

        comparison = pd.DataFrame(rows)

        comparison.sort_values(
            by="difference",
            ascending=False,
            inplace=True
        )

        path = (
            f"{REPORT_DIR}/"
            f"{fraud_type}_comparison.csv"
        )

        comparison.to_csv(
            path,
            index=False
        )

        logging.info(
            f"Saved {path}"
        )

def risk_score_analysis(df):

    frauds = df[
        df["is_fraud"] == 1
    ]

    rows = []

    for fraud_type, group in frauds.groupby(
        "fraud_type"
    ):

        rows.append(
            {
                "fraud_type": fraud_type,

                "mean_score":
                    round(
                        group["risk_score"].mean(),
                        2
                    ),

                "median_score":
                    round(
                        group["risk_score"].median(),
                        2
                    ),

                "min_score":
                    round(
                        group["risk_score"].min(),
                        2
                    ),

                "max_score":
                    round(
                        group["risk_score"].max(),
                        2
                    )
            }
        )

    pd.DataFrame(rows).to_csv(
        f"{REPORT_DIR}/risk_score_by_fraud_type.csv",
        index=False
    )


def save_reports(
    fraud_type_summary,
    missed_frauds,
    missed_summary
):

    os.makedirs(
        REPORT_DIR,
        exist_ok=True
    )

    fraud_type_summary.to_csv(
        f"{REPORT_DIR}/fraud_type_recall.csv",
        index=False
    )

    missed_summary.to_csv(
        f"{REPORT_DIR}/missed_fraud_summary.csv",
        index=False
    )

    missed_frauds.to_parquet(
        f"{REPORT_DIR}/missed_frauds.parquet",
        index=False
    )

    logging.info(
        "Fraud gap reports saved"
    )


def print_summary(
    fraud_type_summary,
    missed_summary
):

    print("\n")
    print("=" * 80)
    print("FRAUD TYPE RECALL")
    print("=" * 80)

    print(
        fraud_type_summary.to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 80)
    print("MOST MISSED FRAUD TYPES")
    print("=" * 80)

    print(
        missed_summary.head(10)
        .to_string(index=False)
    )


def main():

    predictions, labels, features = load_data()

    df = build_analysis_frame(
        predictions,
        labels,
        features
    )
    print(df.columns.tolist())

    print(df.shape)

    print(df["is_fraud"].value_counts())

    print(df["prediction"].value_counts())

    print(df["fraud_type"].value_counts(dropna=False).head())

    fraud_type_summary = (
        fraud_type_recall(df)
    )

    missed_frauds, missed_summary = (
        false_negative_analysis(df)
    )

    fraud_type_describe_reports(df)

    missed_fraud_describe_reports(df)

    fraud_comparison_reports(df)

    risk_score_analysis(df)

    save_reports(
        fraud_type_summary,
        missed_frauds,
        missed_summary
    )

    print_summary(
        fraud_type_summary,
        missed_summary
    )


if __name__ == "__main__":
    main()