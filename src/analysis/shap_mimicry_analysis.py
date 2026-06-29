import joblib
import shap
import pandas as pd
import matplotlib.pyplot as plt


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
                "fraud_type",
                "is_fraud"
            ]
        ],
        on="tx_id"
    )

    mimicry = df[
        df["fraud_type"]
        ==
        "behavioral_mimicry"
    ].copy()

    print(
        f"Mimicry Rows: {len(mimicry):,}"
    )

    X = mimicry[
        FEATURE_COLUMNS
    ]

    model = joblib.load(
        MODEL_PATH
    )

    explainer = shap.Explainer(
        model
    )

    shap_values = explainer(
        X
    )

    print(
        "\nComputing mean SHAP values..."
    )

    importance = pd.DataFrame(
        {
            "feature":
            FEATURE_COLUMNS,

            "mean_abs_shap":
            abs(
                shap_values.values
            ).mean(axis=0)
        }
    )

    importance = (
        importance
        .sort_values(
            "mean_abs_shap",
            ascending=False
        )
    )

    print(
        importance.to_string(
            index=False
        )
    )

    plt.figure(
        figsize=(10, 6)
    )

    shap.plots.bar(
        shap_values,
        max_display=15,
        show=False
    )

    plt.tight_layout()

    plt.savefig(
        "datas/analysis/"
        "shap_mimicry_bar.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    plt.figure(
        figsize=(10, 8)
    )

    shap.summary_plot(
        shap_values.values,
        X,
        show=False
    )

    plt.tight_layout()

    plt.savefig(
        "datas/analysis/"
        "shap_mimicry_summary.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "\nSaved:"
    )

    print(
        "datas/analysis/"
        "shap_mimicry_bar.png"
    )

    print(
        "datas/analysis/"
        "shap_mimicry_summary.png"
    )


if __name__ == "__main__":
    main()