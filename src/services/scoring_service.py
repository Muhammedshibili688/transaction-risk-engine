import json
import os
import time
from datetime import datetime
import random
from dotenv import load_dotenv
load_dotenv()

from src.logger import logging
from src.configuration.redis_connection import RedisClient
from src.feature_store.online_feature_store import OnlineFeatureStore
from src.features.online_feature_engineering import OnlineFeatureEngineer
from src.serving.inference_service import InferenceService


SCORED_STREAM = os.getenv("SCORED_STREAM", "scored_transactions")
STREAM_MAXLEN = int(os.getenv("STREAM_MAXLEN", 400000))

class ScoringService:
    def __init__(
        self,
        config_path="config/rules/baseline.yaml"
    ):

        self.redis = RedisClient().client

        self.inference_service = InferenceService(
            model_path="models/xgboost_baseline.joblib",
            redis_client=self.redis
        )

        self.feature_store = OnlineFeatureStore()
        self.feature_engineer = OnlineFeatureEngineer()

        logging.info(
            f"Hot-path scoring initialized with config={config_path}"
        )

    def process_transaction(self, tx):

        state = self.feature_store.fetch_full_state(tx)

        enriched_tx = self.feature_engineer.compute(
            tx,
            state
        )

        processed_record = {
            **tx,
            **enriched_tx
        }

        prediction = (
            self.inference_service
            .score_transaction(
                tx_id=tx["tx_id"],
                user_id=tx["user_id"],
                feature_vector=processed_record
            )
        )

        self.feature_store.update_state(
            tx,
            state
        )

        event = {
            "features": processed_record,
            "prediction": prediction
        }

        self.redis.xadd(
            SCORED_STREAM,
            {
                "data": json.dumps(event)
            },
            maxlen=STREAM_MAXLEN,
            approximate = True
        )

        return prediction