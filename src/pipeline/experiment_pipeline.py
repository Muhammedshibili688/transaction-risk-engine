import os
import sys
import json
import yaml
import mlflow
import dagshub
import pandas as pd

from dotenv import load_dotenv

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from src.components.model.scorer import FraudScorer
from src.logger import logging
from src.exception import FraudException


def load_rule_config(config_path):

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_dataset(
    features_path,
    labels_path
):

    features_df = pd.read_parquet(
        features_path
    )

    labels_df = pd.read_parquet(
        labels_path
    )

    df = features_df.merge(
        labels_df,
        on="tx_id",
        how="inner"
    )

    logging.info(
        f"Merged dataset size={len(df):,}"
    )

    return df


def score_dataset(
    df,
    config
):

    scorer = FraudScorer(config)

    df["risk_score"] = df.apply(
        lambda row:
        scorer.calculate_heuristic_score(
            row
        ),
        axis=1
    )

    threshold = (
        config
        .get("decision", {})
        .get("fraud_threshold", 60)
    )

    df["prediction"] = (
        df["risk_score"] >= threshold
    ).astype(int)

    return df


def evaluate_predictions(df):

    y_true = df["is_fraud"]
    y_pred = df["prediction"]

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred
    ).ravel()

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    fpr = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0
    )

    fnr = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else 0
    )

    total_transactions = len(df)

    actual_frauds = (
        tp + fn
    )

    review_rate = (
        (tp + fp)
        / total_transactions
    )

    fraud_capture_rate = recall

    fraud_detection_rate = (
        tp / actual_frauds
        if actual_frauds > 0
        else 0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,

        "false_positive_rate": fpr,
        "false_negative_rate": fnr,

        "fraud_capture_rate":
            fraud_capture_rate,

        "fraud_detection_rate":
            fraud_detection_rate,

        "review_rate":
            review_rate,

        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn)
    }


def init_mlflow():

    load_dotenv()

    username = os.getenv(
        "DAGSHUB_USERNAME"
    )

    repo_name = os.getenv(
        "DAGSHUB_REPO_NAME"
    )

    dagshub.init(
        repo_owner=username,
        repo_name=repo_name
    )

    mlflow.set_tracking_uri(
        f"https://dagshub.com/{username}/{repo_name}.mlflow"
    )


def log_experiment(
    config,
    metrics,
    predictions_df
):

    experiment_name = config.get(
        "experiment_name",
        "heuristic_rules"
    )

    rule_version = config.get(
        "rule_version",
        "unknown"
    )

    mlflow.set_experiment(
        experiment_name
    )

    thresholds = config.get(
    "thresholds",
    {}
    )

    geo_speed_limit = thresholds.get(
        "geo_speed_limit",
        "na"
    )

    amount_ratio_limit = thresholds.get(
        "amount_ratio_limit",
        "na"
    )

    switch_count_limit = thresholds.get(
        "switch_count_limit",
        "na"
    )

    with mlflow.start_run(
        run_name = (
            f"{config['rule_version']}"
            f"_geo{geo_speed_limit}"
            f"_amt{amount_ratio_limit}"
            f"_sw{switch_count_limit}"
        )
    ):

        mlflow.log_params(
            config.get(
                "thresholds",
                {}
            )
        )

        mlflow.log_params(
            config.get(
                "weights",
                {}
            )
        )

        mlflow.log_metrics(
            metrics
        )

        os.makedirs(
            "datas/predictions",
            exist_ok=True
        )

        prediction_path = (
            f"datas/predictions/"
            f"{rule_version}"
            f"_geo{geo_speed_limit}"
            f"_amt{amount_ratio_limit}"
            f"_sw{switch_count_limit}.parquet"
        )

        predictions_df[
            [
                "tx_id",
                "risk_score",
                "prediction",
                "is_fraud"
            ]
        ].to_parquet(
            prediction_path,
            index=False
        )

        mlflow.log_artifact(
            prediction_path
        )


def save_metrics(metrics):

    os.makedirs(
        "reports",
        exist_ok=True
    )

    with open(
        "reports/metrics.json",
        "w"
    ) as f:

        json.dump(
            metrics,
            f,
            indent=4
        )


def run_rule_experiment(
    config_path,
    features_path,
    labels_path
):

    try:

        config = load_rule_config(
            config_path
        )

        df = load_dataset(
            features_path,
            labels_path
        )

        df = score_dataset(
            df,
            config
        )

        metrics = evaluate_predictions(
            df
        )

        init_mlflow()

        log_experiment(
            config,
            metrics,
            df
        )

        save_metrics(
            metrics
        )

        logging.info(
            f"Precision={metrics['precision']:.4f} "
            f"Recall={metrics['recall']:.4f} "
            f"F1={metrics['f1']:.4f}"
        )

    except Exception as e:
        raise FraudException(
            e,
            sys
        )


if __name__ == "__main__":

    run_rule_experiment(
        config_path=
            "config/rules/baseline.yaml",

        features_path=
            "datas/features/features.parquet",

        labels_path=
            "datas/labels/labels.parquet"
    )