import json
import os
import time
import random

from src.components.model.scorer import FraudScorer
from src.components.model.decision_engine import DecisionEngine
from src.entity.config_entity import DecisionConfig
from src.pipeline.scoring_pipeline import load_rule_config
from src.logger import logging
from src.entity.config_entity import DataIngestionConfig
from src.configuration.redis_connection import RedisClient
from src.feature_store.online_feature_store import OnlineFeatureStore
from src.features.online_feature_engineering import OnlineFeatureEngineer


class ScoringService:
    def __init__(
        self,
        config_path="config/rules/baseline.yaml",
        consumer_name="worker1"
    ):
        rule_config = load_rule_config(config_path)

        self.scorer = FraudScorer(rule_config)
        self.decider = DecisionEngine(DecisionConfig())

        self.feature_store = OnlineFeatureStore()
        self.feature_engineer = OnlineFeatureEngineer()

        self.config = DataIngestionConfig()
        self.redis = RedisClient().client

        os.makedirs(
            self.config.local_processed_path.parent,
            exist_ok=True
        )

        processed_path = (
            f"datas/processed/{consumer_name}_features.jsonl"
        )

        prediction_path = (
            f"datas/evaluation/{consumer_name}_predictions.jsonl"
        )

        os.makedirs(
            "datas/processed",
            exist_ok=True
        )

        os.makedirs(
            "datas/evaluation",
            exist_ok=True
        )

        self.pred_writer = open(
            prediction_path,
            "a",
            buffering=1
        )

        logging.info("Hot-path scoring service initialized")

    # def _save_processed(self, record):
    #     try:
    #         self.processed_writer.write(
    #             json.dumps(record) + "\n"
    #         )
    #     except Exception:
    #         logging.exception(
    #             "Failed saving processed snapshot"
    #         )

    def _save_prediction(self, record):
        if not self.pred_writer:
            return

        try:
            self.pred_writer.write(
                json.dumps(record) + "\n"
            )
        except Exception:
            logging.exception(
                "Failed saving prediction"
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

        if random.random() < 0.01:
            logging.info(
                f"fetch={t1-t0:.4f}s "
                f"compute={t2-t1:.4f}s "
                f"score={t3-t2:.4f}s "
                f"update={t4-t3:.4f}s"
            )

        event = {
            "features": processed_record,
            "prediction": prediction
        }

        self.redis.xadd(
            "scored_transactions",
            {
                "data": json.dumps(event)
            },
            maxlen = 400000,
            approximate = True
        )

        return prediction