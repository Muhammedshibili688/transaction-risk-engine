# analyze_live_features.py

import json
import pandas as pd
from redis import Redis

r = Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

records = r.xrevrange(
    "scored_transactions",
    count=100000
)

rows = []

for _, fields in records:

    event = json.loads(
        fields["data"]
    )

    features = event["features"]

    rows.append({

        "merchant_affinity_score":
            features[
                "merchant_affinity_score"
            ],

        "merchant_transition_score":
            features[
                "merchant_transition_score"
            ],

        "hour_preference_score":
            features[
                "hour_preference_score"
            ]
    })

df = pd.DataFrame(rows)

print(df.describe())