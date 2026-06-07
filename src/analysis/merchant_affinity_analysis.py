import pandas as pd


FEATURE_PATH = (
    "datas/experiments/features_merchant_affinity.parquet"
)

LABEL_PATH = (
    "datas/labels/labels.parquet"
)


features = pd.read_parquet(
    FEATURE_PATH
)

labels = pd.read_parquet(
    LABEL_PATH
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

print("\nOVERALL")

print(

    df[
        "merchant_affinity_score"
    ].describe()

)

print("\nFRAUD")

print(

    df[
        df["is_fraud"] == 1
    ][
        "merchant_affinity_score"
    ].describe()

)

print("\nNON FRAUD")

print(

    df[
        df["is_fraud"] == 0
    ][
        "merchant_affinity_score"
    ].describe()

)

for fraud_type in [

    "account_takeover",

    "card_testing",

    "behavioral_mimicry"

]:

    print("\n")
    print("=" * 80)
    print(fraud_type)
    print("=" * 80)

    print(

        df[
            df["fraud_type"]
            ==
            fraud_type
        ][
            "merchant_affinity_score"
        ].describe()

    )