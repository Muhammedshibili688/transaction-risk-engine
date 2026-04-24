import json
import random
import uuid
import time
import sys
from datetime import datetime, timedelta

# SHARED IMPORTS - This makes it production-grade
from src.configuration.redis_connection import RedisClient
from src.constants import COUNTRY_PROFILES, MERCHANTS, STREAM_NAME
from src.logger import logging
from src.exception import FraudException


class TransactionSimulator:
    def __init__(self):
        try:
            self.redis_client = RedisClient().client
            # 1. Load the path from our Production Entity
            self.config = DataIngestionConfig()
            
            # 2. Ensure the directory exists (Prevent crash)
            self.config.local_raw_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.users = [User(f"USR_{i:04d}") for i in range(2500)]
            logging.info(f"Simulator ready. Writing to: {self.config.local_raw_path}")
        except Exception as e:
            raise FraudException(e, sys)

    def _save_local(self, tx):
        """Helper to append transaction to local JSONL landing zone."""
        try:
            with open(self.config.local_raw_path, "a") as f:
                f.write(json.dumps(tx) + "\n")
        except Exception as e:
            logging.error(f"Local write failed for TX {tx['tx_id']}")

    def stream_tx(self, tx):
        """Emits raw event to both Redis and Local Disk."""
        try:
            # 1. Real-time Stream
            self.redis_client.xadd(
                STREAM_NAME, 
                {"data": json.dumps(tx)}, 
                maxlen=400000, 
                approximate=True
            )
            # 2. Historical Landing Zone (The part you asked about)
            self._save_local(tx)
        except Exception as e:
            logging.error(f"Failed to process transaction {tx['tx_id']}")

    def run(self):
        logging.info("Starting real-time production...")
        try:
            while True:
                for user in random.sample(self.users, 200):
                    prob = 0.6 if user.fraud_state in ["PROBING", "EXPLOITING"] else 0.08
                    if random.random() < prob:
                        tx = user.generate_raw_tx()
                        if tx:
                            self.stream_tx(tx) # Handles both Redis and File

                            # BURST LOGIC: Ensure bursts are ALSO saved to file
                            if user.fraud_state == "EXPLOITING":
                                for _ in range(random.randint(1, 3)):
                                    btx = user.generate_raw_tx()
                                    if btx: self.stream_tx(btx) 
                
                time.sleep(0.2)
        except KeyboardInterrupt:
            logging.info("Simulator stopped.")
# ----------------------------------------------------------------
# Internal User Class (Stays in simulator as it's the "Behavior Engine")
# ----------------------------------------------------------------
class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.home_country = random.choice(list(COUNTRY_PROFILES.keys()))
        self.profile = COUNTRY_PROFILES[self.home_country]
        self.base_spend_usd = random.uniform(15, 120) * self.profile["ppp"]
        self.known_devices = [f"dev_{uuid.uuid4().hex[:8]}"]
        self.card_type = random.choice(["Visa_Debit", "Mastercard_Gold", "Amex_Platinum"])
        self.tx_history_usd = []
        self.is_fraud_target = random.random() < 0.05
        self.fraud_state = "CLEAN" 
        self.fraud_session_start = None
        self.fraud_device = None
        self.current_ip = f"{self.profile['ip_prefix']}.{random.randint(0,255)}.{random.randint(0,255)}"
        self.current_lat = random.uniform(*self.profile["lat_range"])
        self.current_lon = random.uniform(*self.profile["lon_range"])

    def generate_raw_tx(self):
        override_country = None
        fraud_label = "legit"

        # --- State Machine ---
        if self.is_fraud_target:
            if self.fraud_state == "BURNED":
                if (datetime.utcnow() - self.fraud_session_start).total_seconds() > 300:
                    self.fraud_state = "CLEAN"
                else: return None

            if self.fraud_state == "CLEAN" and random.random() < 0.01:
                self.fraud_state, self.fraud_session_start = "PROBING", datetime.utcnow()
                self.fraud_device = f"atk_{uuid.uuid4().hex[:5]}"
            elif self.fraud_state == "PROBING" and (datetime.utcnow() - self.fraud_session_start).total_seconds() > 5:
                self.fraud_state = "EXPLOITING"
            elif self.fraud_state == "EXPLOITING" and random.random() < 0.2:
                self.fraud_state, self.fraud_session_start = "BURNED", datetime.utcnow()

        # --- Logic ---
        if self.fraud_state == "PROBING":
            usd_amt, fraud_label = random.uniform(0.5, 5.0), "card_test"
        elif self.fraud_state == "EXPLOITING":
            usd_amt, fraud_label = random.uniform(1500, 8000), "takeover"
            if random.random() < 0.6: override_country = random.choice(list(COUNTRY_PROFILES.keys()))
        else:
            avg = sum(self.tx_history_usd)/len(self.tx_history_usd) if self.tx_history_usd else self.base_spend_usd
            usd_amt = random.uniform(avg * 0.7, avg * 1.3)

        tx_country = override_country if override_country else self.home_country
        cp = COUNTRY_PROFILES[tx_country]
        
        # IP and Geo logic
        ip = f"{cp['ip_prefix']}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        lat = random.uniform(*cp["lat_range"])
        lon = random.uniform(*cp["lon_range"])

        tx = {
            "tx_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": self.user_id,
            "amount": round(usd_amt * cp["ex_rate"], 2),
            "amount_usd": round(usd_amt, 2),
            "currency": cp["currency"],
            "country": tx_country,
            "lat": round(lat, 5), "lon": round(lon, 5),
            "ip": ip,
            "device_id": self.fraud_device if self.fraud_state in ["PROBING", "EXPLOITING"] else self.known_devices[0],
            "merchant_category": random.choice(list(MERCHANTS.keys())),
            "card_type": self.card_type,
            "is_fraud": 1 if self.fraud_state != "CLEAN" else 0,
            "pattern": fraud_label
        }
        self.tx_history_usd.append(usd_amt)
        return tx

if __name__ == "__main__":
    sim = TransactionSimulator()
    sim.run()