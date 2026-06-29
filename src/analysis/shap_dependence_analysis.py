import os
import joblib
import shap
import pandas as pd
import matplotlib.pyplot as plt


FEATURES_PATH = (
    "datas/experiments/"
    "features_merchant_transition_score_best_features.parquet"
)

MODEL_PATH = (
    "models/xgboost_baseline.joblib"
)

OUTPUT_DIR = (
    "datas/analysis/shap"
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

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    model = joblib.load(
        MODEL_PATH
    )
    print(type(model))

    features = pd.read_parquet(
        FEATURES_PATH
    )

    X = features[
        FEATURE_COLUMNS
    ]

    # sample for speed
    X_sample = X.sample(
        n=min(10000, len(X)),
        random_state=42
    )

    print(
        f"Rows used: {len(X_sample):,}"
    )

    explainer = shap.TreeExplainer(
        model
    )

    shap_values = explainer(
        X_sample
    )

    # ====================================
    # Affinity score
    # ====================================

    plt.figure()

    plt.figure(figsize=(10, 6))

    shap.dependence_plot(
        "merchant_affinity_score",
        shap_values.values,
        X_sample,
        show=False
    )

    plt.tight_layout()

    plt.savefig(
        f"{OUTPUT_DIR}/shap_dependence_affinity.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # ====================================
    # Transition score
    # ====================================

    plt.figure(figsize=(10, 6))

    shap.dependence_plot(
        "merchant_transition_score",
        shap_values.values,
        X_sample,
        show=False
    )

    plt.tight_layout()

    plt.savefig(
        f"{OUTPUT_DIR}/shap_dependence_transition.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # ====================================
    # Geo speed
    # ====================================

    plt.figure(figsize=(10, 6))

    shap.dependence_plot(
        "geo_speed",
        shap_values.values,
        X_sample,
        show=False
    )

    plt.tight_layout()

    plt.savefig(
        f"{OUTPUT_DIR}/shap_dependence_geo_speed.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # ====================================
    # Amount ratio
    # ====================================

    plt.figure(figsize=(10, 6))

    shap.dependence_plot(
        "amount_ratio",
        shap_values.values,
        X_sample,
        show=False
    )

    plt.tight_layout()

    plt.savefig(
        f"{OUTPUT_DIR}/shap_dependence_amount_ratio.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Saved:"
    )

    print(
        f"{OUTPUT_DIR}/shap_dependence_affinity.png"
    )

    print(
        f"{OUTPUT_DIR}/shap_dependence_transition.png"
    )

    print(
        f"{OUTPUT_DIR}/shap_dependence_geo_speed.png"
    )

    print(
        f"{OUTPUT_DIR}/shap_dependence_amount_ratio.png"
    )

if __name__ == "__main__":
    main()
