import json
import os
import sys
import time
import yaml
from datetime import datetime
from prometheus_client import start_http_server, Counter, Gauge, Histogram

from src.configuration.redis_connection import RedisClient
from src.constants import STREAM_NAME, PROJECT_ROOT
from src.logger import logging
from src.exception import FraudException
from src.entity.config_entity import DataIngestionConfig, DecisionConfig
from src.components.data.data_transformation import FraudFeatureEngineer
from src.components.model.scorer import FraudScorer
from src.components.model.decision_engine import DecisionEngine

# 1. TELEMETRY
TRANSACTION_COUNT = Counter('tx_total', 'Total Transactions Processed')
FRAUD_COUNT = Counter('fraud_detected_total', 'Total Fraudulent Transactions Flagged')
DECISION_LATENCY = Histogram('tx_decision_seconds', 'Time taken to reach a decision')
REDIS_LAG = Gauge('redis_stream_lag', 'Pending records in transaction stream')

# 2. SETTINGS
GROUP_NAME = "fraud_detection_workers"
CONSUMER_NAME = f"worker_{os.getpid()}"

def consume():
    try:
        # Connect to Redis and Configs
        redis_client = RedisClient().client
        config = DataIngestionConfig()
        decision_config = DecisionConfig()
        
        # Load Rule Policy
        rules_path = PROJECT_ROOT / "config" / "rules" / "baseline.yaml"
        with open(rules_path, "r") as f:
            rule_config = yaml.safe_load(f)

        # Initialize Engines
        feature_engineer = FraudFeatureEngineer()
        scorer = FraudScorer(rule_config)
        decider = DecisionEngine(decision_config)
        
        # Setup Consumer Group
        try:
            redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
        except:
            pass # Group already exists

        start_http_server(8000)
        logging.info("Fraud Consumer Engine is LIVE and listening...")

        # Load historical checkpoint from Redis
        last_id = redis_client.get("consumer_checkpoint") or "0-0"
        total_processed_ever = int(redis_client.get("total_processed_count") or 0)

        while True:
            # Update Lag Gauge
            total_produced = redis_client.xlen(STREAM_NAME)
            REDIS_LAG.set(max(0, total_produced - total_processed_ever))

            # Read from Stream
            streams = redis_client.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: ">"}, count=500, block=2000)
            if not streams: continue

            pipe = redis_client.pipeline(transaction=False)

            for _, messages in streams:
                for msg_id, data in messages:
                    with DECISION_LATENCY.time():
                        tx = json.loads(data['data'])
                        
                        # A. Feature Engineering
                        user_state = redis_client.hgetall(f"user:{tx['user_id']}")
                        country_state = redis_client.hgetall(f"country:{tx['country']}")
                        enriched_features = feature_engineer.compute_enriched_features(tx, user_state, country_state)
                        enriched_tx = {**tx, **enriched_features}
                        
                        # B. Scoring & Decision
                        risk_score = scorer.calculate_heuristic_score(enriched_tx)
                        verdict = decider.get_verdict(risk_score)
                        
                        enriched_tx["risk_score"] = risk_score
                        enriched_tx["verdict"] = verdict

                        # C. Persist to Disk
                        with open(config.local_processed_path, "a") as f:
                            f.write(json.dumps(enriched_tx) + "\n")

                        # D. Update System state in Redis
                        pipe.xack(STREAM_NAME, GROUP_NAME, msg_id)
                        
                        total_processed_ever += 1
                        TRANSACTION_COUNT.inc()
                        if verdict == "BLOCK": FRAUD_COUNT.inc()

            # Save progress and execute batch
            pipe.set("consumer_checkpoint", last_id)
            pipe.set("total_processed_count", total_processed_ever)
            pipe.execute()

    except Exception as e:
        raise FraudException(e, sys)

if __name__ == "__main__":
    consume()