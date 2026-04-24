import json
import sys
import time
from prometheus_client import start_http_server, Counter, Gauge, Histogram

from src.configuration.redis_connection import RedisClient
from src.constants import STREAM_NAME
from src.logger import logging
from src.exception import FraudException
from src.entity.config_entity import DataIngestionConfig, DecisionConfig

# COMPONENT IMPORTS
from src.components.data.data_transformation import FraudFeatureEngineer
from src.components.model.scorer import FraudScorer
from src.components.model.decision_engine import DecisionEngine

# ----------------------------------------------------------------
# 1. TELEMETRY (Prometheus)
# ----------------------------------------------------------------
TRANSACTION_COUNT = Counter('tx_total', 'Total Transactions Processed')
FRAUD_COUNT = Counter('fraud_detected_total', 'Total Fraudulent Transactions Flagged')
DECISION_LATENCY = Histogram('tx_decision_seconds', 'Time taken to reach a decision')
REDIS_LAG = Gauge('redis_stream_lag', 'Pending records in transaction stream')

def consume():
    try:
        # Initialize Clients and Engines
        redis_client = RedisClient().client
        config = DataIngestionConfig()
        decision_config = DecisionConfig()
        
        feature_engineer = FraudFeatureEngineer()
        scorer = FraudScorer()
        decider = DecisionEngine(decision_config)
        
        start_http_server(8000)
        logging.info("Consumer Engine Online. Port 8000 metrics active.")

        # CHECKPOINT: Resume from persistent Redis bookmark
        last_id = redis_client.get("consumer_checkpoint") or "0-0"
        processed_count = int(redis_client.get("total_processed_count") or 0)

        while True:
            # Update Lag Metric
            total_produced = redis_client.xlen(STREAM_NAME)
            REDIS_LAG.set(max(0, total_produced - processed_count))

            # Batch Read (500 per gulp for clearing backlogs)
            streams = redis_client.xread({STREAM_NAME: last_id}, count=500, block=2000)
            if not streams: continue

            for stream_name, messages in streams:
                for msg_id, data in messages:
                    with DECISION_LATENCY.time(): # Measure per-tx speed
                        
                        tx = json.loads(data['data'])
                        
                        # 1. FETCH STATE
                        user_state = redis_client.hgetall(f"user:{tx['user_id']}")
                        country_state = redis_client.hgetall(f"country:{tx['country']}")

                        # 2. FEATURE ENGINEERING (The 11 Columns)
                        enriched_features = feature_engineer.compute_enriched_features(tx, user_state, country_state)
                        enriched_tx = {**tx, **enriched_features}

                        # 3. SCORING (The "Brain")
                        # Calculates a risk score 0-100
                        risk_score = scorer.calculate_heuristic_score(enriched_tx)
                        enriched_tx["risk_score"] = risk_score

                        # 4. DECISIONING (The "Verdict")
                        # Returns ALLOW, BLOCK, or CHALLENGE
                        verdict = decider.get_verdict(risk_score)
                        enriched_tx["verdict"] = verdict

                        # 5. PERSIST ENRICHED DATA (Snapshot for ML Training)
                        # We use the config path to save to data/processed
                        with open(config.local_processed_path, "a") as f:
                            f.write(json.dumps(enriched_tx) + "\n")

                        # 6. OUTPUT ROUTING (Push verdict to new stream)
                        redis_client.xadd(
                            decision_config.verdict_stream_name, 
                            {"data": json.dumps(enriched_tx)}, 
                            maxlen=100000
                        )

                        # 7. UPDATE SYSTEM STATE
                        _update_redis_state(redis_client, enriched_tx, user_state, country_state)

                        last_id = msg_id
                        processed_count += 1
                        TRANSACTION_COUNT.inc()
                        if verdict == "BLOCK": FRAUD_COUNT.inc()

            # COMMIT CHECKPOINT
            redis_client.set("consumer_checkpoint", last_id)
            redis_client.set("total_processed_count", processed_count)

    except Exception as e:
        raise FraudException(e, sys)

def _update_redis_state(r, record, user_state, country_state):
    """Saves the current tx data to Redis to build user history for the next tx."""
    user_id = record['user_id']
    country = record['country']
    
    tx_count = int(user_state.get('tx_count', 0)) + 1
    old_avg = float(user_state.get('avg_amount', record['amount_usd']))
    new_avg = (old_avg * (tx_count-1) + record['amount_usd']) / tx_count
    
    devices = json.loads(user_state.get('devices', '[]'))
    if record['device_id'] not in devices:
        devices.append(record['device_id'])
        r.hincrby(f"user:{user_id}", "device_switch_count", 1)
    
    ips = json.loads(user_state.get('ips', '[]'))
    if record['ip'] not in ips:
        ips.append(record['ip'])
        r.hincrby(f"user:{user_id}", "ip_switch_count", 1)

    r.hset(f"user:{user_id}", mapping={
        "last_lat": record['lat'], "last_lon": record['lon'],
        "last_time": record['timestamp'], "avg_amount": new_avg,
        "tx_count": tx_count, "last_country": country,
        "devices": json.dumps(devices[-10:]), "ips": json.dumps(ips[-10:])
    })

    r.hincrby(f"country:{country}", "tx_count", 1)
    r.hset(f"country:{country}", "total_amount", float(country_state.get('total_amount', 0)) + record['amount_usd'])

if __name__ == "__main__":
    consume()