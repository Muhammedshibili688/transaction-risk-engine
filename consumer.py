# import json
# import os
# import sys
# import time
# import yaml
# from datetime import datetime
# from prometheus_client import start_http_server, Counter, Gauge, Histogram

# from src.configuration.redis_connection import RedisClient
# from src.constants import STREAM_NAME, PROJECT_ROOT
# from src.logger import logging
# from src.exception import FraudException
# from src.entity.config_entity import DataIngestionConfig, DecisionConfig
# from src.components.data.data_transformation import FraudFeatureEngineer
# from src.components.model.scorer import FraudScorer
# from src.components.model.decision_engine import DecisionEngine

# # 1. TELEMETRY
# TRANSACTION_COUNT = Counter('tx_total', 'Total Transactions Processed')
# FRAUD_COUNT = Counter('fraud_detected_total', 'Total Fraudulent Transactions Flagged')
# DECISION_LATENCY = Histogram('tx_decision_seconds', 'Time taken to reach a decision')
# REDIS_LAG = Gauge('redis_stream_lag', 'Pending records in transaction stream')

# # 2. SETTINGS
# GROUP_NAME = "fraud_detection_workers"
# CONSUMER_NAME = f"worker_{os.getpid()}"

# def consume():
#     try:
#         # Connect to Redis and Configs
#         redis_client = RedisClient().client
#         config = DataIngestionConfig()
#         decision_config = DecisionConfig()
        
#         # Load Rule Policy
#         rules_path = PROJECT_ROOT / "config" / "rules" / "baseline.yaml"
#         with open(rules_path, "r") as f:
#             rule_config = yaml.safe_load(f)

#         # Initialize Engines
#         feature_engineer = FraudFeatureEngineer()
#         scorer = FraudScorer(rule_config)
#         decider = DecisionEngine(decision_config)
        
#         # Setup Consumer Group
#         try:
#             redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
#         except:
#             pass # Group already exists

#         start_http_server(8000)
#         logging.info("Fraud Consumer Engine is LIVE and listening...")

#         # Load historical checkpoint from Redis
#         last_id = redis_client.get("consumer_checkpoint") or "0-0"
#         total_processed_ever = int(redis_client.get("total_processed_count") or 0)

#         while True:
#             # Update Lag Gauge
#             total_produced = redis_client.xlen(STREAM_NAME)
#             REDIS_LAG.set(max(0, total_produced - total_processed_ever))

#             # Read from Stream
#             streams = redis_client.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: ">"}, count=500, block=2000)
#             if not streams: continue

#             pipe = redis_client.pipeline(transaction=False)

#             for _, messages in streams:
#                 for msg_id, data in messages:
#                     with DECISION_LATENCY.time():
#                         tx = json.loads(data['data'])
                        
#                         # A. Feature Engineering
#                         user_state = redis_client.hgetall(f"user:{tx['user_id']}")
#                         country_state = redis_client.hgetall(f"country:{tx['country']}")
#                         enriched_features = feature_engineer.compute_enriched_features(tx, user_state, country_state)
#                         enriched_tx = {**tx, **enriched_features}
                        
#                         # B. Scoring & Decision
#                         risk_score = scorer.calculate_heuristic_score(enriched_tx)
#                         verdict = decider.get_verdict(risk_score)
                        
#                         enriched_tx["risk_score"] = risk_score
#                         enriched_tx["verdict"] = verdict

#                         # C. Persist to Disk
#                         with open(config.local_processed_path, "a") as f:
#                             f.write(json.dumps(enriched_tx) + "\n")

#                         # D. Update System state in Redis
#                         pipe.xack(STREAM_NAME, GROUP_NAME, msg_id)
                        
#                         total_processed_ever += 1
#                         TRANSACTION_COUNT.inc()
#                         if verdict == "BLOCK": FRAUD_COUNT.inc()

#             # Save progress and execute batch
#             pipe.set("consumer_checkpoint", last_id)
#             pipe.set("total_processed_count", total_processed_ever)
#             pipe.execute()

#     except Exception as e:
#         raise FraudException(e, sys)

# if __name__ == "__main__":
#     consume()


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

TRANSACTION_COUNT = Counter('tx_total', 'Total Transactions Processed')
FRAUD_COUNT = Counter('fraud_detected_total', 'Total Fraudulent Transactions Flagged')
DECISION_LATENCY = Histogram('tx_decision_seconds', 'Time taken to reach a decision')
REDIS_LAG = Gauge('redis_stream_lag', 'Pending records in transaction stream')

GROUP_NAME = "fraud_detection_workers"
CONSUMER_NAME = f"worker_{os.getpid()}"

def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

def consume():
    try:
        redis_client = RedisClient().client
        config = DataIngestionConfig()
        decision_config = DecisionConfig()
        
        rules_path = PROJECT_ROOT / "config" / "rules" / "baseline.yaml"
        with open(rules_path, "r") as f:
            rule_config = yaml.safe_load(f)

        feature_engineer = FraudFeatureEngineer()
        scorer = FraudScorer(rule_config)
        decider = DecisionEngine(decision_config)
        
        try:
            redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
        except:
            pass

        start_http_server(8000)
        logging.info("Fraud Consumer Engine is LIVE and listening...")

        last_id = redis_client.get("consumer_checkpoint") or "0-0"
        total_processed_ever = int(redis_client.get("total_processed_count") or 0)

        while True:
            total_produced = redis_client.xlen(STREAM_NAME)
            REDIS_LAG.set(max(0, total_produced - total_processed_ever))

            streams = redis_client.xreadgroup(
                GROUP_NAME, CONSUMER_NAME,
                {STREAM_NAME: ">"},
                count=500, block=2000
            )

            if not streams:
                continue

            pipe = redis_client.pipeline(transaction=False)

            for _, messages in streams:
                for msg_id, data in messages:
                    with DECISION_LATENCY.time():
                        tx = json.loads(data['data'])

                        # ------------------------
                        #  REALISTIC DATA CLEANING
                        # ------------------------
                        tx['lat'] = safe_float(tx.get('lat'))
                        tx['lon'] = safe_float(tx.get('lon'))
                        tx['amount_usd'] = safe_float(tx.get('amount_usd'))
                        tx['device_id'] = tx.get('device_id') or "unknown_device"
                        tx['ip'] = tx.get('ip') or "0.0.0.0"

                        # ------------------------
                        #  LOAD STATE
                        # ------------------------
                        user_key = f"user:{tx['user_id']}"
                        country_key = f"country:{tx['country']}"

                        user_state = redis_client.hgetall(user_key)
                        country_state = redis_client.hgetall(country_key)

                        # ------------------------
                        #  FEATURE ENGINEERING
                        # ------------------------
                        enriched_features = feature_engineer.compute_enriched_features(
                            tx, user_state, country_state
                        )

                        enriched_tx = {**tx, **enriched_features}

                        # ------------------------
                        #  SCORING
                        # ------------------------
                        # risk_score = scorer.calculate_heuristic_score(enriched_tx)
                        # verdict = decider.get_verdict(risk_score)

                        # enriched_tx["risk_score"] = risk_score
                        # enriched_tx["verdict"] = verdict

                        # ------------------------
                        #  STORE OUTPUT
                        # ------------------------
                        with open(config.local_processed_path, "a") as f:
                            f.write(json.dumps(enriched_tx) + "\n")

                        # ------------------------
                        #  UPDATE USER STATE (CRITICAL FIX)
                        # ------------------------
                        devices = json.loads(user_state.get("devices", "[]"))
                        ips = json.loads(user_state.get("ips", "[]"))

                        if tx["device_id"] not in devices:
                            devices.append(tx["device_id"])

                        if tx["ip"] not in ips:
                            ips.append(tx["ip"])

                        prev_avg = safe_float(user_state.get("avg_amount"), tx["amount_usd"])
                        new_avg = (prev_avg + tx["amount_usd"]) / 2

                        device_switch_count = int(user_state.get("device_switch_count", 0))
                        ip_switch_count = int(user_state.get("ip_switch_count", 0))

                        if enriched_features["is_new_device"]:
                            device_switch_count += 1
                        if enriched_features["is_new_ip"]:
                            ip_switch_count += 1

                        pipe.hset(user_key, mapping={
                            "last_lat": tx["lat"],
                            "last_lon": tx["lon"],
                            "last_time": tx["timestamp"],
                            "last_country": tx["country"],
                            "avg_amount": new_avg,
                            "devices": json.dumps(devices),
                            "ips": json.dumps(ips),
                            "device_switch_count": device_switch_count,
                            "ip_switch_count": ip_switch_count
                        })

                        # ------------------------
                        #  UPDATE COUNTRY STATE
                        # ------------------------
                        total_amt = safe_float(country_state.get("total_amount"), 0)
                        tx_count = int(country_state.get("tx_count", 0))

                        pipe.hset(country_key, mapping={
                            "total_amount": total_amt + tx["amount_usd"],
                            "tx_count": tx_count + 1
                        })

                        # ------------------------
                        # ACK + METRICS
                        # ------------------------
                        pipe.xack(STREAM_NAME, GROUP_NAME, msg_id)

                        total_processed_ever += 1
                        TRANSACTION_COUNT.inc()

                        # if verdict == "BLOCK":
                        #     FRAUD_COUNT.inc()

            pipe.set("consumer_checkpoint", last_id)
            pipe.set("total_processed_count", total_processed_ever)
            pipe.execute()

    except Exception as e:
        raise FraudException(e, sys)


if __name__ == "__main__":
    consume()