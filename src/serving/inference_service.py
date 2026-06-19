import os
import json
import time
from datetime import datetime
import joblib
import numpy as np
from redis import Redis
import random
from dotenv import load_dotenv
load_dotenv()


THRESHOLD = 0.40
MONITORING_STREAM = os.getenv(
    "MONITORING_STREAM",
    "monitoring_events"
)

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

        self.feature_names = list(
            self.model.feature_names_in_
        )

    def score_transaction(
        self,
        tx_id: str,
        user_id: str,
        feature_vector,
    ) -> dict:
 
        # X = pd.DataFrame(
        # [{
        #     col: feature_vector[col]
        #     for col in self.model.feature_names_in_
        # }]

        # )
        
    
        row = [
            feature_vector[col]
            for col in self.feature_names
        ]

        X = np.array(
            [row],
            dtype=np.float32
        )
            
        # print("TRAIN FEATURES")
        # print(list(self.model.feature_names_in_))

        # print("INFERENCE FEATURES")
        # print(list(X.columns))

        start_time = time.perf_counter()

        probability = float(
            self.model
            .predict_proba(X)[0][1]
        )

        predict_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        decision = (
            "REVIEW"
            if probability >= THRESHOLD
            else "APPROVE"
        )

        # if random.random() < 0.001:
        #     print(
        #         {
        #             "user_id": user_id,
        #             "probability": round(probability, 4),
        #             "decision": decision,

        #             "tx_count":
        #                 feature_vector["transaction_count_24h"],

        #             "merchant_affinity":
        #                 feature_vector["merchant_affinity_score"],

        #             "transition":
        #                 feature_vector["merchant_transition_score"],

        #             "hour":
        #                 feature_vector["hour_preference_score"],

        #             "is_new_ip":
        #                 feature_vector["is_new_ip"],

        #             "is_new_device":
        #                 feature_vector["is_new_device"],
        #         }
        #     )

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
            datetime.now().isoformat()
        }

        payload = {
            k: json.dumps(v)
            if isinstance(
                v,
                (dict, list)
            )
            else str(v)
            for k, v in result.items()
        }

        pipe = self.redis_client.pipeline()

        redis_start = time.perf_counter()

        pipe.xadd(
            "risk_decisions",
            payload,
            maxlen=500000,
            approximate=True
        )

        if decision == "REVIEW":

            pipe.xadd(
                "risk_decisions:review",
                {
                    "tx_id": tx_id,
                    "probability": probability,
                }
            )

        else:

            pipe.xadd(
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

        if random.random() < 0.001:
            print(
                f"predict_ms={predict_ms:.3f}"
                )

        monitoring_event = {

            "probability":
                probability,

            "prediction":
                int(
                    decision == "REVIEW"
                ),

            "merchant_affinity_score":
                feature_vector.get(
                    "merchant_affinity_score",
                    0.0
                ),

            "merchant_transition_score":
                feature_vector.get(
                    "merchant_transition_score",
                    0.0
                ),

            "is_new_ip":
                feature_vector.get(
                    "is_new_ip",
                    0
                ),

            "latency_ms":
                latency_ms
        }

        pipe.xadd(
            MONITORING_STREAM,
            {
                "data":
                    json.dumps(
                        monitoring_event
                    )
            },
            maxlen=500000,
            approximate=True
        )

        result[
            "latency_ms"
        ] = round(
            latency_ms,
            3
        )

        pipe.execute()

        redis_logger_ms = (
            time.perf_counter() - redis_start
        ) * 1000

        return result
