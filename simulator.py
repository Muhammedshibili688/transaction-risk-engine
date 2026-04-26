import os
import json
import random
import uuid
import time
import sys
from datetime import datetime, timedelta

from src.configuration.redis_connection import RedisClient
from src.constants import COUNTRY_PROFILES, MERCHANTS
from src.entity.config_entity import DataIngestionConfig
from src.logger import logging
from src.exception import FraudException

STREAM_NAME = os.getenv("STREAM_NAME", "transactions_stream")


class TransactionSimulator:
    def __init__(self):
        try:
            self.redis_client = RedisClient().client
            self.config = DataIngestionConfig()

            self.config.local_fresh_path.parent.mkdir(parents=True, exist_ok=True)

            self.users = [User(f"USR_{i:05d}") for i in range(3000)]

            logging.info(f"Simulator ready. Writing to: {self.config.local_fresh_path}")

        except Exception as e:
            raise FraudException(e, sys)

    def _save_local(self, tx):
        try:
            with open(self.config.local_fresh_path, "a") as f:
                f.write(json.dumps(tx) + "\n")
        except:
            pass

    def stream_tx(self, tx):
        try:
            self.redis_client.xadd(
                STREAM_NAME,
                {"data": json.dumps(tx)},
                maxlen=400000,
                approximate=True
            )
            self._save_local(tx)
        except:
            pass

    def run(self):
        logging.info("Starting real-time production...")

        try:
            while True:
                for user in random.sample(self.users, 200):

                    prob = 0.6 if user.fraud_state in ["PROBING", "EXPLOITING", "MULE"] else 0.1

                    if random.random() < prob:
                        tx = user.generate_raw_tx()

                        if tx:
                            self.stream_tx(tx)

                            if user.fraud_state == "EXPLOITING":
                                for _ in range(random.randint(2, 5)):
                                    btx = user.generate_raw_tx()
                                    if btx:
                                        self.stream_tx(btx)

                time.sleep(0.2)

        except KeyboardInterrupt:
            logging.info("Simulator stopped.")


class User:
    def __init__(self, user_id):
        self.user_id = user_id

        self.home_country = random.choice(list(COUNTRY_PROFILES.keys()))
        self.profile = COUNTRY_PROFILES[self.home_country]

        self.current_lat = random.uniform(*self.profile["lat_range"])
        self.current_lon = random.uniform(*self.profile["lon_range"])

        self.devices = [f"dev_{uuid.uuid4().hex[:6]}"]
        self.ips = [f"{self.profile['ip_prefix']}.{random.randint(0,255)}.{random.randint(0,255)}"]

        self.avg_amount = random.uniform(20, 150)

        self.last_tx_time = datetime.utcnow()

        self.is_fraud_target = random.random() < 0.05
        self.fraud_state = "NORMAL"
        self.fraud_timer = 0

    def _update_fraud_state(self):
        if not self.is_fraud_target:
            return

        if self.fraud_state == "NORMAL" and random.random() < 0.01:
            self.fraud_state = "PROBING"
            self.fraud_timer = random.randint(3, 10)

        elif self.fraud_state == "PROBING":
            self.fraud_timer -= 1
            if self.fraud_timer <= 0:
                self.fraud_state = "EXPLOITING"
                self.fraud_timer = random.randint(5, 15)

        elif self.fraud_state == "EXPLOITING":
            # 🔥 ADD MULE TRANSITION
            if random.random() < 0.2:
                self.fraud_state = "MULE"
                self.fraud_timer = random.randint(5, 15)
            else:
                self.fraud_timer -= 1
                if self.fraud_timer <= 0:
                    self.fraud_state = "NORMAL"

        elif self.fraud_state == "MULE":
            self.fraud_timer -= 1
            if self.fraud_timer <= 0:
                self.fraud_state = "NORMAL"

    def generate_raw_tx(self):
        self._update_fraud_state()

        now = self.last_tx_time + timedelta(seconds=random.randint(5, 300))
        self.last_tx_time = now

        # ------------------------
        # NORMAL
        # ------------------------
        if self.fraud_state == "NORMAL":
            amount = random.uniform(self.avg_amount * 0.7, self.avg_amount * 1.5)
            device = random.choice(self.devices)
            ip = random.choice(self.ips)

            lat = self.current_lat + random.uniform(-0.02, 0.02)
            lon = self.current_lon + random.uniform(-0.02, 0.02)
            country = self.home_country

        # ------------------------
        # PROBING
        # ------------------------
        elif self.fraud_state == "PROBING":
            amount = random.uniform(1, 20)
            device = f"new_{uuid.uuid4().hex[:6]}"
            ip = f"{self.profile['ip_prefix']}.{random.randint(0,255)}.{random.randint(0,255)}"

            lat = self.current_lat
            lon = self.current_lon
            country = self.home_country

        # ------------------------
        # EXPLOITING
        # ------------------------
        elif self.fraud_state == "EXPLOITING":
            amount = random.uniform(self.avg_amount * 5, self.avg_amount * 20)
            device = f"atk_{uuid.uuid4().hex[:6]}"
            ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

            fraud_country = random.choice(list(COUNTRY_PROFILES.keys()))
            cp = COUNTRY_PROFILES[fraud_country]

            lat = random.uniform(*cp["lat_range"])
            lon = random.uniform(*cp["lon_range"])
            country = fraud_country

        # ------------------------
        # MULE (laundering)
        # ------------------------
        else:
            amount = random.uniform(self.avg_amount * 2, self.avg_amount * 6)
            device = random.choice(self.devices)
            ip = random.choice(self.ips)

            mule_country = random.choice(list(COUNTRY_PROFILES.keys()))
            cp = COUNTRY_PROFILES[mule_country]

            lat = random.uniform(*cp["lat_range"])
            lon = random.uniform(*cp["lon_range"])
            country = mule_country

        # Update profile
        self.avg_amount = (self.avg_amount * 0.9) + (amount * 0.1)

        # Missing values
        if random.random() < 0.01:
            ip = None
        if random.random() < 0.02:
            device = None

        # ------------------------
        # LABELS (CRITICAL)
        # ------------------------
        fraud_type = "none"
        is_fraud = 0

        if self.fraud_state == "PROBING":
            fraud_type = "card_testing"
            is_fraud = 1
        elif self.fraud_state == "EXPLOITING":
            fraud_type = "account_takeover"
            is_fraud = 1
        elif self.fraud_state == "MULE":
            fraud_type = "money_laundering"
            is_fraud = 1

        return {
            "tx_id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "user_id": self.user_id,
            "amount_usd": round(amount, 2),
            "country": country,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "device_id": device,
            "ip": ip,
            "is_fraud": is_fraud,
            "fraud_type": fraud_type
        }


if __name__ == "__main__":
    sim = TransactionSimulator()
    sim.run()