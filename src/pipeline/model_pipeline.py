import os
import pandas as pd
import joblib
import mlflow
import dagshub
from dotenv import load_dotenv
load_dotenv()
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from src.components.model.model_training import ModelTraining
from src.components.model.model_evaluation import ModelEvaluation

FEATURES_PATH = (
    "datas/experiments/features_affinity_zscore_hour_preference_device_affinity.parquet"
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

    "hour_preference_score",

    "merchant_affinity_score",

    "device_merchant_affinity_score"
]

load_dotenv()

# repo_owner = os.getenv(
#     "DAGSHUB_USERNAME"
# )

# repo_name = os.getenv(
#     "DAGSHUB_REPO_NAME"
# )

# mlflow_password = os.getenv(
#     "MLFLOW_TRACKING_PASSWORD"
# )

# os.environ[
#     "MLFLOW_TRACKING_USERNAME"
# ] = repo_owner

# os.environ[
#     "MLFLOW_TRACKING_PASSWORD"
# ] = mlflow_password

# dagshub.init(
#     repo_owner=repo_owner,
#     repo_name=repo_name,
#     mlflow=True
# )

# mlflow.set_tracking_uri(
#     f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow"
# )

# mlflow.set_experiment(
#     "Fraud_Model_Training"
# )

# print(
#     "Tracking URI:",
#     mlflow.get_tracking_uri()
# )


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

    tx_ids = df[
        "tx_id"
    ]

    (
        X_train,
        X_test,
        y_train,
        y_test,
        tx_train,
        tx_test
    ) = train_test_split(
        X,
        y,
        tx_ids,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    scaler = StandardScaler()

    X_train_scaled = (
        scaler.fit_transform(
            X_train
        )
    )

    X_test_scaled = (
        scaler.transform(
            X_test
        )
    )

    trainer = ModelTraining()

    model, best_params = (
        trainer.train(
            X_train_scaled,
            y_train
        )
    )

    trainer.save_model(
        model,
        MODEL_PATH
    )

    trainer.save_scaler(
        scaler,
        SCALER_PATH
    )

    evaluator = ModelEvaluation()

    metrics, predictions, probabilities = evaluator.evaluate(
        model,
        X_test_scaled,
        y_test
    )

    evaluator.save_predictions(
        tx_ids=tx_test,
        y_true=y_test,
        predictions=predictions,
        probabilities=probabilities,
        output_path=
        "datas/predictions/"
        "logreg_v5_affinity_zscore_hour_device_affinity.parquet"
    )

    # with mlflow.start_run(
    #     run_name ="logistic_regression_v5_affinity_zscire_hour_prefrence_device_affinity"
    # ):

    #     mlflow.log_param(
    #         "model_type",
    #         "logistic_regression"
    #     )

    #     mlflow.log_param(
    #         "best_c",
    #         best_params["C"]
    #     )

    #     mlflow.log_param(
    #         "class_weight",
    #         "balanced"
    #     )

    #     mlflow.log_param(
    #         "feature_count",
    #         len(FEATURE_COLUMNS)
    #     )

    #     mlflow.log_param(
    #         "features",
    #         ",".join(FEATURE_COLUMNS)
    #     )

    #     for metric_name, metric_value in metrics.items():

    #         if isinstance(
    #             metric_value,
    #             (int, float)
    #         ):

    #             mlflow.log_metric(
    #                 metric_name,
    #                 metric_value
    #             )

    #     mlflow.log_artifact(
    #         MODEL_PATH
    #     )

    #     mlflow.log_artifact(
    #         SCALER_PATH
    #     )

    evaluator.show_metrics(
        metrics
    )

    evaluator.show_coefficients(
        model,
        FEATURE_COLUMNS
    )


if __name__ == "__main__":
    main()