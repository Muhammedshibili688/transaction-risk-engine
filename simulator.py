from typing import Dict, List
from dataclasses import dataclass
import copy
import os
import json
import random
import uuid
import time
import sys
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from src.configuration.redis_connection import RedisClient
from src.constants import COUNTRY_PROFILES, MERCHANTS
from src.entity.config_entity import DataIngestionConfig
from src.logger import logging
from src.exception import FraudException
from src.services.scoring_service import ScoringService
from src.pipeline.scoring_pipeline import load_rule_config

STREAM_NAME = os.getenv("STREAM_NAME", "transactions")

@dataclass
class UserPersona:
        spender_type: str
        tx_per_day: int
        preferred_categories: List[str]
        night_owl_score: float
        travel_frequency: float
        device_stability: float
        avg_amount: float
        amount_variance: float
        hour_mean: int
        hour_std: int

PERSONA_TEMPLATES: Dict[str, UserPersona] = {
        "budget": UserPersona(
            spender_type="budget",
            tx_per_day=3,
            preferred_categories=["standard", "digital"],
            night_owl_score=0.3,
            travel_frequency=0.05,
            device_stability=0.92,
            avg_amount=22.0,
            amount_variance=8.0,
            hour_mean=19,
            hour_std=2
        ),

        "average": UserPersona(
            spender_type="average",
            tx_per_day=5,
            preferred_categories=["standard", "digital"],
            night_owl_score=0.4,
            travel_frequency=0.15,
            device_stability=0.85,
            avg_amount=90.0,
            amount_variance=35.0,
            hour_mean=14,
            hour_std=4
        ),

        "luxury": UserPersona(
            spender_type="luxury",
            tx_per_day=4,
            preferred_categories=["luxury", "high_risk"],
            night_owl_score=0.5,
            travel_frequency=0.40,
            device_stability=0.75,
            avg_amount=420.0,
            amount_variance=180.0,
            hour_mean=20,
            hour_std=3
        ),

        "subscription": UserPersona(
            spender_type="subscription",
            tx_per_day=2,
            preferred_categories=["digital"],
            night_owl_score=0.7,
            travel_frequency=0.05,
            device_stability=0.95,
            avg_amount=14.0,
            amount_variance=5.0,
            hour_mean=22,
            hour_std=2
        ),
    }

def random_persona() -> UserPersona:
        weights = {
            "budget": 6.00,
            "average": 0.45,
            "luxury": 0.10,
            "subscription": 0.15,
        }

        selected = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
            k=1
        )[0]

        return copy.deepcopy(PERSONA_TEMPLATES[selected])


def persona_amount(persona: UserPersona) -> float:
        amount = abs(
            np.random.normal(
                persona.avg_amount,
                persona.amount_variance
            )
        )

        return max(1.0, round(amount, 2))


def persona_merchant(persona: UserPersona) -> str:
        if random.random() < 0.75:
            category = random.choice(persona.preferred_categories)

            if category in MERCHANTS:
                return random.choice(MERCHANTS[category])

        all_merchants = []

        for merchant_group in MERCHANTS.values():
            all_merchants.extend(merchant_group)

        return random.choice(all_merchants)


def merchant_category(merchant: str) -> str:
        for category, merchant_list in MERCHANTS.items():
            if merchant in merchant_list:
                return category

        return "standard"

class TransactionSimulator:
    def __init__(self, n_users=5000):
        
        try:
            self.redis_client = RedisClient().client
            self.redis_client.ping()
            self.config = DataIngestionConfig()

            self.scoring_service = ScoringService()

            self.config.local_fresh_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self.users = [
                User(f"USR_{i:05d}")
                for i in range(n_users)
            ]

            self.sim_clock = datetime.utcnow()

            self.active_campaign = None
            self.campaign_users = []

            self.raw_writer = open(
                str(self.config.local_fresh_path),
                "a",
                buffering=1
            )

            logging.info(
                f"Simulator ready with {n_users} users. "
                f"Writing to: {self.config.local_fresh_path}"
            )

            rule_config = load_rule_config()

            experiment = rule_config.get(
                "experiment_name",
                "rules"
            ).replace(" ", "_")

            version = rule_config.get(
                "rule_version",
                "v1"
            ).replace(".", "_")

            eval_dir = self.config.data_dir / "evaluation"

            os.makedirs(
                eval_dir,
                exist_ok=True
            )

            existing = [
                f for f in os.listdir(eval_dir)
                if f.startswith(f"{experiment}_{version}")
            ]

            run_number = len(existing) + 1

            prediction_path = eval_dir / (
                f"{experiment}_{version}_run{run_number:03d}.jsonl"
            )


        except Exception as e:
            raise FraudException(e, sys)

    def _save_local(self, tx):
        try:
            self.raw_writer.write(
                json.dumps(tx) + "\n"
            )
        except Exception:
            logging.exception("Failed local save")

        except Exception:
            logging.exception("Failed prediction save")

    def stream_tx(self, tx):
        try:
            self.redis_client.xadd(
                STREAM_NAME,
                {"data": json.dumps(tx)},
                maxlen=400000,
                approximate=True
            )

        except Exception:
            logging.exception("Failed Redis stream publish")

    def _maybe_start_campaign(self):
        if self.active_campaign:
            return

        if random.random() < 0.01:
            self.active_campaign = {
                "end_time": time.time() + random.randint(60, 300)
            }

            max_campaign = max(2, int(len(self.users) * 0.15))

            campaign_size = random.randint(
                2,
                max_campaign
            )

            self.campaign_users = random.sample(
                self.users,
                campaign_size
            )

            for u in self.campaign_users:
                u.behavior_state = "CARD_TESTING_SLOW"
                u.state_timer = random.randint(4, 12)

            logging.info(
                f"Fraud campaign started with "
                f"{len(self.campaign_users)} actors"
            )

    def _cleanup_campaign(self):
        if not self.active_campaign:
            return

        if time.time() > self.active_campaign["end_time"]:
            self.active_campaign = None
            self.campaign_users = []

    def _validate_tx(self, tx):
        required = [
            "tx_id",
            "timestamp",
            "user_id",
            "amount_usd",
            "merchant",
            "country",
            "lat",
            "lon",
            "device_id",
            "ip",
            "is_fraud",
            "fraud_type",
            "campaign_id",
        ]

        missing = [
            field for field in required
            if field not in tx
        ]

        if missing:
            raise ValueError(
                f"Missing tx fields: {missing}"
            )

        if tx["amount_usd"] <= 0:
            raise ValueError(
                f"Invalid amount: {tx['amount_usd']}"
            )

        if not isinstance(tx["is_fraud"], int):
            raise ValueError(
                "is_fraud must be int"
            )

        if tx["is_fraud"] not in [0, 1]:
            raise ValueError(
                "is_fraud must be 0 or 1"
            )

        # type checks FIRST
        if not isinstance(tx["lat"], (float, int)):
            raise ValueError("lat invalid")

        if not isinstance(tx["lon"], (float, int)):
            raise ValueError("lon invalid")

        # then range checks
        if not (-90 <= tx["lat"] <= 90):
            raise ValueError("Invalid latitude")

        if not (-180 <= tx["lon"] <= 180):
            raise ValueError("Invalid longitude")

        if tx["is_fraud"] == 0 and tx["fraud_type"] != "none":
            raise ValueError(
                "Legit tx cannot have fraud_type"
            )

        if tx["is_fraud"] == 1 and tx["fraud_type"] == "none":
            raise ValueError(
                "Fraud tx missing fraud_type"
            )

        try:
            datetime.fromisoformat(tx["timestamp"])
        except Exception:
            raise ValueError(
                f"Invalid timestamp: {tx['timestamp']}"
            )

        return True

    def _seasonal_event_rate(self):
        # now = datetime.utcnow()
        now = self.sim_clock

        base = 40

        hour = now.hour
        weekday = now.weekday()
        day = now.day

        # business hours spike
        if 9 <= hour <= 21:
            base *= 2.0

        # fraud-heavy night traffic
        elif 0 <= hour <= 5:
            base *= 1.4

        # weekends = more shopping
        if weekday >= 5:
            base *= 1.3

        # payday spikes
        if day in [1, 28, 29, 30, 31]:
            base *= 1.5

        return max(5, int(base))

    def run(self):
        logging.info("Starting real-time production...")

        try:
            while True:
                self._maybe_start_campaign()
                self._cleanup_campaign()
                

                pending_info = self.redis_client.xpending(
                    STREAM_NAME,
                    "fraud_scoring_group"
                )

                pending = pending_info["pending"]

                if pending > 10000:
                    logging.warning(
                        f"Backpressure detected. Pending={pending}"
                    )
                    time.sleep(1.0)
                    continue

                target_rate = self._seasonal_event_rate()
                n_events = np.random.poisson(target_rate)

                for _ in range(n_events):
                    # self.sim_clock += timedelta(
                    #     milliseconds=random.randint(50, 500)
                    # )

                    self.sim_clock += timedelta(
                        seconds=random.randint(10, 120)
                    )

                    user = random.choice(self.users)

                    if not user.should_transact(self.sim_clock):
                        continue

                    tx = user.generate_raw_tx(self.sim_clock)

                    if tx:
                        self.stream_tx(tx)
                        self._save_local(tx)

        except KeyboardInterrupt:
            logging.info("Simulator stopped.")

        finally:
            if hasattr(self, "raw_writer"):
                self.raw_writer.close()

            if hasattr(self, "pred_writer"):
                self.pred_writer.close()

def merchant_category(merchant):
    for category, merchants in MERCHANTS.items():
        if merchant in merchants:
            return category
    return "standard"



class User:
    def __init__(self, user_id):
        self.user_id = user_id

        self.home_country = random.choice(
            list(COUNTRY_PROFILES.keys())
        )

        self.next_tx_time = datetime.utcnow()

        self.profile = COUNTRY_PROFILES[self.home_country]

        self.home_lat = random.uniform(*self.profile["lat_range"])
        self.home_lon = random.uniform(*self.profile["lon_range"])

        self.current_lat = self.home_lat
        self.current_lon = self.home_lon

        self.persona = random_persona()

        self.devices = [f"dev_{uuid.uuid4().hex[:8]}"]
        self.ips = [
            f"{self.profile['ip_prefix']}."
            f"{random.randint(0,255)}."
            f"{random.randint(0,255)}"
        ]

        self.transactions = deque(maxlen=1000)

        self.last_tx_time = datetime.utcnow()

        self.base_risk = random.uniform(0.01, 0.15)
        self.blocked_count = 0

        self.behavior_state = "NORMAL"
        self.state_timer = 0

        self.favorite_merchants = [
            persona_merchant(self.persona)
            for _ in range(3)
        ]

        self.shared_campaign_id = None
        self.mimicry_level = None

    def known_device(self):
        return random.choice(self.devices) if self.devices else None

    def known_ip(self):
        return random.choice(self.ips) if self.ips else None

    def register_device(self):
        d = f"dev_{uuid.uuid4().hex[:8]}"
        self.devices.append(d)
        return d

    def register_ip(self, country=None):
        if country is None:
            country = self.home_country

        profile = COUNTRY_PROFILES[country]

        ip = (
            f"{profile['ip_prefix']}."
            f"{random.randint(0,255)}."
            f"{random.randint(1,254)}"
        )

        self.ips.append(ip)

        return ip
    
    def choose_merchant(self):
        if random.random() < 0.80:
            return random.choice(self.favorite_merchants)

        new_merchant = persona_merchant(self.persona)

        if random.random() < 0.20:
            self.favorite_merchants.append(new_merchant)

            if len(self.favorite_merchants) > 5:
                self.favorite_merchants.pop(0)

        return new_merchant
    
    def sample_target_hour(self):

        hour = int(
            random.gauss(
                self.persona.hour_mean,
                self.persona.hour_std
            )
        )

        return max(
            0,
            min(
                23,
                hour
            )
        )

    def recent_transactions(self, seconds):
        cutoff = self.last_tx_time - timedelta(seconds=seconds)
        return [
            t for t in self.transactions
            if cutoff <= t["timestamp"] <= self.last_tx_time
        ]

    def _update_behavior_state(self, current_time):
        current_hour = current_time.hour

        risk_multiplier = 1.0

        # fraud more active overnight
        if 0 <= current_hour <= 5:
            risk_multiplier = 1.8

        effective_risk = min(
            0.95,
            self.base_risk * risk_multiplier
        )

        if random.random() > effective_risk:
            if random.random() < 0.08:
                self.behavior_state = "WEIRD_LEGIT"
                self.state_timer = random.randint(2, 6)
            else:
                self.behavior_state = "NORMAL"
            return

        if self.behavior_state == "NORMAL":
            r = random.random()

            if r < 0.20:
                self.mimicry_level = None
                self.behavior_state = "CARD_TESTING_SLOW"
                self.state_timer = random.randint(4, 10)

            elif r < 0.35:
                self.mimicry_level = None
                self.behavior_state = "ACCOUNT_TAKEOVER"
                self.state_timer = random.randint(2, 5)

            elif r < 0.50:
                self.behavior_state = "BEHAVIORAL_MIMICRY"

                self.mimicry_level = random.choices(
                    ["easy", "medium", "advanced"],
                    weights=[40, 40, 20]
                )[0]

                self.state_timer = random.randint(3, 8)

            elif r < 0.60:
                self.behavior_state = "ADAPTIVE_ATTACK"
                self.state_timer = random.randint(3, 7)

        else:
            self.state_timer -= 1

            if self.state_timer <= 0:

                self.behavior_state = "NORMAL"

                self.mimicry_level = None


    def schedule_next_tx(self, now):

        if self.behavior_state == "NORMAL":
            gap_minutes = random.randint(30, 360)

        elif self.behavior_state == "WEIRD_LEGIT":
            gap_minutes = random.randint(10, 120)

        elif self.behavior_state == "CARD_TESTING_SLOW":
            gap_seconds = random.randint(20, 180)
            self.next_tx_time = now + timedelta(seconds=gap_seconds)
            return

        elif self.behavior_state == "ACCOUNT_TAKEOVER":
            gap_seconds = random.randint(30, 300)
            self.next_tx_time = now + timedelta(seconds=gap_seconds)
            return

        elif self.behavior_state == "BEHAVIORAL_MIMICRY":
            gap_minutes = random.randint(20, 180)

        else:  # adaptive attack
            gap_seconds = random.randint(10, 120)
            self.next_tx_time = now + timedelta(seconds=gap_seconds)
            return

        self.next_tx_time = now + timedelta(minutes=gap_minutes)

        if self.behavior_state == "BEHAVIORAL_MIMICRY":

            follow_profile = (
                random.random() < 0.70
            )

        else:

            follow_profile = (
                random.random() < 0.90
            )

        if follow_profile:

            target_hour = (
                self.sample_target_hour()
            )

            candidate = (
                self.next_tx_time.replace(
                    hour=target_hour,
                    minute=random.randint(0,59),
                    second=random.randint(0,59)
                )
            )

            if candidate > now:

                self.next_tx_time = candidate


    def generate_raw_tx(self, current_time):
        self._update_behavior_state(current_time)
        

        # gap = random.randint(10, 600)

        # if self.behavior_state == "CARD_TESTING_SLOW":
        #     gap = random.randint(300, 7200)

        # elif self.behavior_state == "ADAPTIVE_ATTACK":
        #     gap = random.randint(120, 1800)

        now = current_time
        self.last_tx_time = now

        fraud_type = "none"
        is_fraud = 0
        campaign_id = "none"

        if self.behavior_state == "NORMAL":
            amount = persona_amount(self.persona)

            if random.random() > self.persona.device_stability:
                device = self.register_device()
            else:
                device = self.known_device()

            ip = self.known_ip()

            merchant = self.choose_merchant()

            mcat = merchant_category(merchant)

            country = self.home_country

            if mcat == "digital":
                # VPN / remote digital access possible
                if random.random() < 0.20:
                    lat = self.home_lat + random.uniform(-2.0, 2.0)
                    lon = self.home_lon + random.uniform(-2.0, 2.0)
                else:
                    lat = self.home_lat + random.uniform(-0.1, 0.1)
                    lon = self.home_lon + random.uniform(-0.1, 0.1)

            else:
                # physical merchants should stay geographically tighter
                lat = self.home_lat + random.uniform(-0.03, 0.03)
                lon = self.home_lon + random.uniform(-0.03, 0.03)

        elif self.behavior_state == "WEIRD_LEGIT":
            amount = persona_amount(self.persona) * random.uniform(2, 6)

            device = (
                self.register_device()
                if random.random() < 0.05
                else self.known_device()
            )

            travel_prob = self.persona.travel_frequency

            if current_time.weekday() >= 5:
                travel_prob *= 1.3

            if random.random() < min(0.95, travel_prob):
                country = random.choice(list(COUNTRY_PROFILES.keys()))
                cp = COUNTRY_PROFILES[country]

                lat = random.uniform(*cp["lat_range"])
                lon = random.uniform(*cp["lon_range"])

                # traveler / vpn-ish legit
                ip = (
                    self.register_ip(country=country)
                    if random.random() < 0.6
                    else self.known_ip()
                )

            else:
                country = self.home_country
                lat = self.home_lat
                lon = self.home_lon

                ip = (
                    self.register_ip(country=self.home_country)
                    if random.random() < 0.10
                    else self.known_ip()
                )

            merchant = self.choose_merchant()

        elif self.behavior_state == "CARD_TESTING_SLOW":
            amount = round(random.uniform(0.5, 19.99), 2)

            device = (
                self.known_device()
                if random.random() < 0.8
                else self.register_device()
            )

            ip = (
                self.known_ip()
                if random.random() < 0.8
                else self.register_ip()
            )

            country = self.home_country
            lat = self.home_lat
            lon = self.home_lon
            merchant = random.choice(MERCHANTS["digital"])

            fraud_type = "card_testing"
            is_fraud = 1

        elif self.behavior_state == "ACCOUNT_TAKEOVER":
            amount = random.uniform(
                self.persona.avg_amount * 1.5,
                self.persona.avg_amount * 8
            )

            device = (
                self.register_device()
                if random.random() < 0.70
                else self.known_device()
            )

            # stealth local takeover
            if random.random() < 0.35:
                country = self.home_country
                lat = self.home_lat + random.uniform(-0.15, 0.15)
                lon = self.home_lon + random.uniform(-0.15, 0.15)

                ip = (
                    self.register_ip(country=self.home_country)
                    if random.random() < 0.75
                    else self.known_ip()
                )

            else:
                fraud_country = random.choice([
                    c for c in COUNTRY_PROFILES.keys()
                    if c != self.home_country
                ])

                cp = COUNTRY_PROFILES[fraud_country]

                country = fraud_country
                lat = random.uniform(*cp["lat_range"])
                lon = random.uniform(*cp["lon_range"])

                ip = (
                    self.register_ip(country=fraud_country)
                    if random.random() < 0.75
                    else self.known_ip()
                )

            merchant = random.choice(
                MERCHANTS["high_risk"] + MERCHANTS["luxury"]
            )

            fraud_type = "account_takeover"
            is_fraud = 1

        elif self.behavior_state == "BEHAVIORAL_MIMICRY":

            level = self.mimicry_level

            if level == "easy":

                device = (
                    self.known_device()
                    if random.random() < 0.50
                    else self.register_device()
                )

                ip = (
                    self.known_ip()
                    if random.random() < 0.50
                    else self.register_ip()
                )

                merchant = persona_merchant(
                    self.persona
                )

                amount = (
                    persona_amount(self.persona)
                    * random.uniform(1.2, 2.0)
                )

            elif level == "medium":

                device = self.known_device()

                ip = (
                    self.known_ip()
                    if random.random() < 0.80
                    else self.register_ip()
                )

                merchant = random.choice(
                    self.favorite_merchants
                )

                amount = persona_amount(
                    self.persona
                )

            else:  # advanced

                device = self.known_device()

                ip = self.known_ip()

                merchant = random.choice(
                    self.favorite_merchants
                )

                amount = persona_amount(
                    self.persona
                )

            mcat = merchant_category(
                merchant
            )

            country = self.home_country

            if mcat == "digital":

                lat = (
                    self.home_lat
                    + random.uniform(-1.0, 1.0)
                )

                lon = (
                    self.home_lon
                    + random.uniform(-1.0, 1.0)
                )

            else:

                lat = (
                    self.home_lat
                    + random.uniform(-0.08, 0.08)
                )

                lon = (
                    self.home_lon
                    + random.uniform(-0.08, 0.08)
                )

            fraud_type = "behavioral_mimicry"
            is_fraud = 1

        else:  # ADAPTIVE_ATTACK
            amount = round(random.uniform(1.0, 12.0), 2)

            device = (
                self.known_device()
                if random.random() < 0.7
                else self.register_device()
            )

            ip = (
                self.known_ip()
                if random.random() < 0.7
                else self.register_ip()
            )

            country = self.home_country
            lat = self.home_lat
            lon = self.home_lon
            merchant = random.choice(MERCHANTS["digital"])

            fraud_type = "card_testing"
            is_fraud = 1

        self.transactions.append({
            "timestamp": now,
            "amount_usd": amount,
            "device_id": device,
            "ip": ip,
            "merchant": merchant,
        })

        self.schedule_next_tx(now)

        return {
            "tx_id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "user_id": self.user_id,
            "amount_usd": round(amount, 2),
            "merchant": merchant,
            "country": country,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "device_id": device,
            "ip": ip,
            "is_fraud": is_fraud,
            "fraud_type": fraud_type,
            "campaign_id": campaign_id,
        }
    
    def should_transact(self, now):
        return now >= self.next_tx_time

def validate_simulator_contract(sim):

    for _ in range(20):
        user = random.choice(sim.users)
        tx = user.generate_raw_tx(datetime.utcnow())
        sim._validate_tx(tx)

    logging.info("Simulator contract validation passed")

if __name__ == "__main__":
    sim = TransactionSimulator(n_users=5000)

    validate_simulator_contract(sim)

    sim.run()