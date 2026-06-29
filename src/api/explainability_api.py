import json
import joblib
import shap
import pandas as pd

from redis import Redis
from fastapi import FastAPI, HTTPException


app = FastAPI()

redis_client = Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


class ExplainabilityService:

    def __init__(self):

        self.model = joblib.load(
            "models/xgboost_baseline.joblib"
        )

        self.explainer = shap.TreeExplainer(
            self.model
        )

        self.feature_names = list(
            self.model.feature_names_in_
        )

    def explain(
        self,
        feature_vector
    ):

        X = pd.DataFrame(
            [feature_vector]
        )[self.feature_names]

        shap_values = self.explainer(
            X
        )

        contributions = []

        for feature, shap_value in zip(
            self.feature_names,
            shap_values.values[0]
        ):

            contributions.append(
                {
                    "feature": feature,
                    "impact": round(
                        float(shap_value),
                        4
                    )
                }
            )

        contributions = sorted(
            contributions,
            key=lambda x:
            abs(x["impact"]),
            reverse=True
        )

        return contributions[:10]


explainer = ExplainabilityService()


@app.get(
    "/user/{user_id}"
)
def get_user_transactions(
    user_id: str
):

    tx_ids = redis_client.zrevrange(
        f"user_transactions:{user_id}",
        0,
        -1
    )

    recent_transactions = []

    for tx_id in tx_ids:

        raw = redis_client.get(
            f"tx_features:{tx_id}"
        )

        if raw is None:
            continue

        tx = json.loads(raw)

        recent_transactions.append(
            {
                "tx_id":
                    tx["tx_id"],

                "fraud_probability":
                    tx["fraud_probability"],

                "decision":
                    tx["decision"],

                "timestamp":
                    tx["timestamp"]
            }
        )

    return {

        "user_id":
            user_id,

        "transaction_count":
            len(tx_ids),

        "recent_transactions":
            recent_transactions
    }


@app.get(
    "/transaction/{tx_id}"
)
def explain_transaction(
    tx_id: str
):

    raw = redis_client.get(
        f"tx_features:{tx_id}"
    )

    if raw is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    tx_data = json.loads(raw)

    top_signals = explainer.explain(
        tx_data["features"]
    )

    return {

        "tx_id":
            tx_data["tx_id"],

        "user_id":
            tx_data["user_id"],

        "fraud_probability":
            tx_data["fraud_probability"],

        "decision":
            tx_data["decision"],

        "timestamp":
            tx_data["timestamp"],

        "top_signals":
            top_signals
    }

@app.get("/review_queue")
def review_queue(
    limit: int = 20
):

    records = redis_client.xrevrange(
        "risk_decisions:review",
        count=limit
    )

    pending_reviews = []

    for _, fields in records:

        tx_id = fields["tx_id"]

        raw = redis_client.get(
            f"tx_features:{tx_id}"
        )

        if raw is None:
            continue

        tx_data = json.loads(raw)

        top_signals = explainer.explain(
            tx_data["features"]
        )

        pending_reviews.append(
            {

                "tx_id":
                    tx_data["tx_id"],

                "user_id":
                    tx_data["user_id"],

                "fraud_probability":
                    tx_data["fraud_probability"],

                "decision":
                    tx_data["decision"],

                "timestamp":
                    tx_data["timestamp"],

                "top_signals":
                    top_signals

            }
        )

    return {

        "review_count":
            len(pending_reviews),

        "pending_reviews":
            pending_reviews

    }
