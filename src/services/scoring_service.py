import json
import os
import time
from datetime import datetime
import random
from dotenv import load_dotenv
load_dotenv()
from src.components.model.scorer import FraudScorer
from src.components.model.decision_engine import DecisionEngine
from src.entity.config_entity import DecisionConfig
from src.pipeline.scoring_pipeline import load_rule_config
from src.logger import logging
from src.configuration.redis_connection import RedisClient
from src.feature_store.online_feature_store import OnlineFeatureStore
from src.features.online_feature_engineering import OnlineFeatureEngineer

SCORED_STREAM = os.getenv("SCORED_STREAM", "scored_transactions")
STREAM_MAXLEN = int(os.getenv("STREAM_MAXLEN", 400000))

class ScoringService:
    def __init__(
        self,
        config_path="config/rules/baseline.yaml"
    ):
        rule_config = load_rule_config(config_path)

        self.scorer = FraudScorer(rule_config)
        self.decider = DecisionEngine(DecisionConfig())

        self.feature_store = OnlineFeatureStore()
        self.feature_engineer = OnlineFeatureEngineer()

        self.redis = RedisClient().client

        logging.info(
            f"Hot-path scoring initialized with config={config_path}"
        )

    def process_transaction(self, tx):

        t0 = time.time()

        state = self.feature_store.fetch_full_state(tx)

        t1 = time.time()

        enriched_tx = self.feature_engineer.compute(
            tx,
            state
        )
        t2 = time.time()

        processed_record = {
            **tx,
            **enriched_tx
        }

        score = self.scorer.calculate_heuristic_score(
            processed_record
        )

        verdict = self.decider.get_verdict(score)
        t3 = time.time()

        prediction = {
            "tx_id": tx["tx_id"],
            "timestamp": tx["timestamp"],
            "user_id": tx["user_id"],
            "risk_score": score,
            "verdict": verdict,
            "is_fraud": tx.get("is_fraud"),
            "fraud_type": tx.get("fraud_type"),
            "campaign_id": tx.get("campaign_id")
        }

        self.feature_store.update_state(
            tx,
            state
        )
        t4 = time.time()

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