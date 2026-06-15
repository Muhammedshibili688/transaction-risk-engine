import json
import time
import joblib

from redis import Redis


THRESHOLD = 0.40


class InferenceService:

    def __init__(
        self,
        model_path: str,
        redis_client: Redis,
    ):

        self.model = joblib.load(
            model_path
        )

        self.redis_client = redis_client

    def score_transaction(
        self,
        tx_id: str,
        user_id: str,
        feature_vector,
    ) -> dict:

        start_time = time.perf_counter()

        probability = float(
            self.model
            .predict_proba(feature_vector)[0][1]
        )

        decision = (
            "REVIEW"
            if probability >= THRESHOLD
            else "APPROVE"
        )

        result = {

            "tx_id":
            tx_id,

            "user_id":
            user_id,

            "fraud_probability":
            probability,

            "threshold":
            THRESHOLD,

            "decision":
            decision,

            "timestamp":
            time.time(),
        }

        self.redis_client.xadd(
            "risk_decisions",
            {
                k: json.dumps(v)
                if isinstance(
                    v,
                    (dict, list)
                )
                else str(v)
                for k, v in result.items()
            }
        )

        if decision == "REVIEW":

            self.redis_client.xadd(
                "risk_decisions:review",
                {
                    "tx_id": tx_id,
                    "probability": probability,
                }
            )

        else:

            self.redis_client.xadd(
                "risk_decisions:approved",
                {
                    "tx_id": tx_id,
                    "probability": probability,
                }
            )

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        result[
            "latency_ms"
        ] = round(
            latency_ms,
            3
        )

        return result
