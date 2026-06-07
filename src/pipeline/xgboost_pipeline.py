import os
import mlflow
import dagshub
import pandas as pd

from dotenv import load_dotenv

from sklearn.model_selection import (
    train_test_split
)

from src.components.model.xgboost_training import XGBoostTraining


from src.components.model.model_evaluation import ModelEvaluation


load_dotenv()

repo_owner = os.getenv(
    "DAGSHUB_USERNAME"
)

repo_name = os.getenv(
    "DAGSHUB_REPO_NAME"
)

mlflow_password = os.getenv(
    "MLFLOW_TRACKING_PASSWORD"
)

os.environ[
    "MLFLOW_TRACKING_USERNAME"
] = repo_owner

os.environ[
    "MLFLOW_TRACKING_PASSWORD"
] = mlflow_password

dagshub.init(
    repo_owner=repo_owner,
    repo_name=repo_name,
    mlflow=True
)

mlflow.set_tracking_uri(
    f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow"
)

mlflow.set_experiment(
    "Fraud_Model_Training"
)


FEATURES_PATH = (
    "datas/experiments/features_zscore_hour_preference.parquet"
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

    "hour_preference_score"
]


def main():

    features = pd.read_parquet(
        FEATURES_PATH
    )
    print(features.columns.tolist())

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
        on="tx_id",
        how="inner"
    )

    print(
        f"Dataset Loaded: {len(df):,}"
    )

    X = df[
        FEATURE_COLUMNS
    ]

    y = df[
        "is_fraud"
    ]

    (
        X_train,
        X_test,
        y_train,
        y_test
    ) = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    trainer = XGBoostTraining()

    model, params = (
        trainer.train(
            X_train,
            y_train
        )
    )

    trainer.save_model(
        model,
        MODEL_PATH
    )

    evaluator = ModelEvaluation()

    metrics = evaluator.evaluate(
        model,
        X_test,
        y_test
    )

    with mlflow.start_run(
        run_name=
        "xgboost_baseline_v1"
    ):

        mlflow.log_param(
            "model_type",
            "xgboost"
        )

        for key, value in params.items():

            mlflow.log_param(
                key,
                value
            )

        mlflow.log_param(
            "feature_count",
            len(FEATURE_COLUMNS)
        )

        mlflow.log_param(
            "features",
            ",".join(
                FEATURE_COLUMNS
            )
        )

        for metric_name, metric_value in metrics.items():

            if isinstance(
                metric_value,
                (
                    int,
                    float
                )
            ):

                mlflow.log_metric(
                    metric_name,
                    metric_value
                )

        mlflow.log_artifact(
            MODEL_PATH
        )

    evaluator.show_metrics(
        metrics
    )

    evaluator.show_feature_importance(
        model,
        FEATURE_COLUMNS
    )


if __name__ == "__main__":
    main()