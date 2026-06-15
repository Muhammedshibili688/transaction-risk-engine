import json
import os

import pandas as pd


FEATURES_PATH = (
    "datas/experiments/"
    "features_merchant_transition_score_best_features.parquet"
)

OUTPUT_PATH = (
    "reports/baselines/"
    "feature_baseline.json"
)


FEATURES_TO_MONITOR = [

    "merchant_affinity_score",

    "merchant_transition_score",

]


def main():

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True,
    )

    df = pd.read_parquet(
        FEATURES_PATH
    )

    baseline = {}

    for feature in FEATURES_TO_MONITOR:

        baseline[feature] = {

            "mean":
            round(
                float(df[feature].mean()),
                6,
            ),

            "min":
            round(
                float(df[feature].min()),
                6,
            ),

            "max":
            round(
                float(df[feature].max()),
                6,
            ),

            "std":
            round(
                float(df[feature].std()),
                6,
            ),

        }

    with open(
        OUTPUT_PATH,
        "w",
    ) as f:

        json.dump(
            baseline,
            f,
            indent=4,
        )

    print(
        "\nFeature baseline saved:"
    )

    print(
        OUTPUT_PATH
    )

    print(
        "\nBaseline Statistics\n"
    )

    print(
        json.dumps(
            baseline,
            indent=4,
        )
    )


if __name__ == "__main__":

    main()
