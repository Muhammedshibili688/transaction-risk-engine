import random
from datetime import datetime, timedelta
from src.configuration.redis_connection import RedisClient
from src.logger import logging

class OnlineFeatureStore:
    def __init__(self):
        self.redis = RedisClient().client

    def user_key(self, user_id: str) -> str:
        return f"user:{user_id}"
    
    def device_key(self, user_id: str) -> str:
        return f"user:{user_id}: devices "
    
    def ip_key(self, user_id: str) -> str:
        return f"user:{user_id}: ips"
    
    def device_history_key(self, user_id):
        return f"user:{user_id}:devices:24h"

    def ip_history_key(self, user_id):
        return f"user:{user_id}:ips:24h"
    
    def get_distinct_devices_24h(self, user_id):
        return self.redis.zcard(
            self.device_history_key(user_id)
        )


    def get_distinct_ips_24h(self, user_id):
        return self.redis.zcard(
            self.ip_history_key(user_id)
        )
    
    def velocity_key(self, user_id: str) -> str:
        return f"vel:{user_id}"
    
    def burst_key(self, user_id: str) -> str:
        return f"burst:{user_id}"
    
    def merchant_key(self, user_id: str, merchant: str) -> str:
        return f"merch:{user_id}:{merchant}"
    
    def country_key(self, country):
        return f"Country: {country}"

    def merchant_counts_key(
        self,
        user_id
    ):
        return (
            f"user:{user_id}:merchant_counts"
        )

    def hour_counts_key(
        self,
        user_id
    ):
        return (
            f"user:{user_id}:hour_counts"
        )

    def device_merchant_counts_key(
        self,
        user_id
    ):
        return (
            f"user:{user_id}:device_merchant_counts"
        )

    def transition_counts_key(
        self,
        user_id
    ):
        return (
            f"user:{user_id}:transition_counts"
        )

    def outgoing_transition_counts_key(
        self,
        user_id
    ):
        return (
            f"user:{user_id}:outgoing_transition_counts"
        )
    
    # =================================================
    # Read methods
    # =================================================

    def fetch_user_state(self, user_id):
        key = self.user_key(user_id)

        data = self.redis.hgetall(key)

        if not data:
            return {
                "avg_amount": 0.0,
                "tx_count": 0,
                "last_country": None,
                "last_lat": None,
                "last_lon": None,
                "last_timestamp": None,

                "tx_count_1m": 0,
                "tx_count_5m": 0,
                "tx_count_1h": 0,
                "tx_count_24h": 0,

                "small_amount_burst_count": 0,
                "merchant_repeat_count": 0,

                "distinct_devices_24h": 0,
                "distinct_ips_24h": 0,
            }

        return {
            "avg_amount": float(data.get("avg_amount", 0)),
            "tx_count": int(data.get("tx_count", 0)),
            "last_country": data.get("last_country"),
            "last_lat": float(data["last_lat"]) if data.get("last_lat") else None,
            "last_lon": float(data["last_lon"]) if data.get("last_lon") else None,
            "last_timestamp": data.get("last_timestamp"),

            "tx_count_1m": int(data.get("tx_count_1m", 0)),
            "tx_count_5m": int(data.get("tx_count_5m", 0)),
            "tx_count_1h": int(data.get("tx_count_1h", 0)),
            "tx_count_24h": int(data.get("tx_count_24h", 0)),

            "small_amount_burst_count": int(
                data.get("small_amount_burst_count", 0)
            ),

            "merchant_repeat_count": int(
                data.get("merchant_repeat_count", 0)
            ),

            "distinct_devices_24h": int(
                data.get("distinct_devices_24h", 0)
            ),

            "distinct_ips_24h": int(
                data.get("distinct_ips_24h", 0)
            ),
        }
    
    def is_known_device(self, used_id, device_id):
        return self.redis.sismember(
            self.device_key(used_id),
            device_id
        )
    
    def is_known_ip(self, user_id, ip):
        return self.redis.sismember(
            self.ip_key(user_id),
            ip
        )
    
    def get_country_stats(self, country):
        data = self.redis.hgetall(
            self.country_key(country)
        )

        if not data:
            return {
                "avg_amount": 0.0,
                "tx_count": 0
            }

        return {
            "avg_amount": float(
                data.get("avg_amount", 0)
            ),
            "tx_count": int(
                data.get("tx_count", 0)
            )
        }
    

    def get_small_amount_burst(self, user_id, timestamp):
        key = self.burst_key(user_id)
        ts = timestamp.timestamp()

        return self.redis.zcount(key, ts - 300, ts)

    def get_merchant_repeat(self, user_id, merchant, timestamp):
        key = self.merchant_key(user_id, merchant)
        ts = timestamp.timestamp()

        return self.redis.zcount(key, ts - 300, ts)

    
    # =================================================
    # Write methods
    # =================================================

    def update_state(self, tx, prior_state):

        user_id = tx["user_id"]
        
        amount = tx["amount_usd"]
        timestamp = tx["timestamp"]

        curr_dt = datetime.fromisoformat(timestamp)

        user_key = self.user_key(user_id)
        state = prior_state["user"]

        # -----------------------------
        # avg amount + tx count
        # -----------------------------
        old_avg = state["avg_amount"]
        old_count = state["tx_count"]
        old_sum = state["amount_sum"]
        old_sum_sq = state["amount_sum_sq"]

        merchant_total = sum(
            int(v)
            for v in prior_state["merchant_counts"].values()
        )

        if merchant_total != old_count:
            print(
                {
                    "type": "PRE_UPDATE_MISMATCH",
                    "user_id": user_id,
                    "merchant_total": merchant_total,
                    "old_count": old_count
                }
            )

        new_count = old_count + 1

        new_sum = old_sum + amount

        new_sum_sq = (
            old_sum_sq
            + amount * amount
        )

        if old_count == 0:
            new_avg = amount
        else:
            new_avg = (
                (old_avg * old_count) + amount
            ) / new_count

        
        # -----------------------------
        # small amount burst
        # -----------------------------
        if amount < 20:
            small_amount_burst_count = (
                state["small_amount_burst_count"] + 1
            )
        else:
            small_amount_burst_count = 0

        # -----------------------------
        # merchant repeat
        # -----------------------------
        if tx["merchant"] == state["last_merchant"]:
            merchant_repeat_count = (
                state["merchant_repeat_count"] + 1
            )
        else:
            merchant_repeat_count = 1

        # -----------------------------
        # distinct identities
        # -----------------------------
        distinct_devices_24h = state["distinct_devices_24h"]
        distinct_ips_24h = state["distinct_ips_24h"]

        if not prior_state["known_device"]:
            distinct_devices_24h += 1

        if not prior_state["known_ip"]:
            distinct_ips_24h += 1

        # -----------------------------
        # country stats
        # -----------------------------
        country = tx["country"]
        country_stats = prior_state["country"]

        c_count = country_stats["tx_count"]
        c_avg = country_stats["avg_amount"]

        new_c_count = c_count + 1

        if c_count == 0:
            new_c_avg = amount
        else:
            new_c_avg = (
                (c_avg * c_count) + amount
            ) / new_c_count

        # -----------------------------
        # persist
        # -----------------------------
        pipe = self.redis.pipeline()

        # identity memory
        pipe.sadd(
            self.device_key(user_id),
            tx["device_id"]
        )

        pipe.sadd(
            self.ip_key(user_id),
            tx["ip"]
        )

        velocity_key = self.velocity_key(user_id)

        pipe.zadd(
            velocity_key,
            {
                tx["tx_id"]: curr_dt.timestamp()
            }
        )

        if random.random() < 0.01:

            pipe.zremrangebyscore(
                velocity_key,
                0,
                curr_dt.timestamp() - 86400
            )

        if random.random() < 0.0001:
            print(
                {
                    "user_id": user_id,
                    "old_count": old_count,
                    "new_count": new_count
                }
            )

        # user state
        pipe.hset(
            user_key,
            mapping={
                "avg_amount": new_avg,
                "tx_count": new_count,

                "last_country": tx["country"],
                "last_lat": tx["lat"],
                "last_lon": tx["lon"],
                "last_timestamp": timestamp,

                "small_amount_burst_count":
                    small_amount_burst_count,

                "merchant_repeat_count":
                    merchant_repeat_count,

                "distinct_devices_24h":
                    distinct_devices_24h,

                "distinct_ips_24h":
                    distinct_ips_24h,

                "last_merchant": tx["merchant"],

                "amount_sum":new_sum,

                "amount_sum_sq":new_sum_sq
            }
        )

        # country state
        pipe.hset(
            self.country_key(country),
            mapping={
                "avg_amount": new_c_avg,
                "tx_count": new_c_count
            }
        )
        # =================================
        # Merchant counts
        # =================================

        pipe.hincrby(
            self.merchant_counts_key(
                user_id
            ),
            tx["merchant"],
            1
        )

        # =================================
        # Hour counts
        # =================================

        hour = str(
            curr_dt.hour
        )

        pipe.hincrby(
            self.hour_counts_key(
                user_id
            ),
            hour,
            1
        )

        # =================================
        # Device Merchnat counts
        # =================================

        device_merchant_key = (
            f"{tx['device_id']}|"
            f"{tx['merchant']}"
        )

        pipe.hincrby(
            self.device_merchant_counts_key(
                user_id
            ),
            device_merchant_key,
            1
        )

        # =================================
        # Merchnat Transition
        # =================================

        previous_merchant = (
            state["last_merchant"]
        )

        if previous_merchant:

            transition_key = (
                f"{previous_merchant}|"
                f"{tx['merchant']}"
            )

            # specific transition
            pipe.hincrby(
                self.transition_counts_key(
                    user_id
                ),
                transition_key,
                1
            )

            # total outgoing transitions
            pipe.hincrby(
                self.outgoing_transition_counts_key(
                    user_id
                ),
                previous_merchant,
                1
            )

        pipe.execute()

    def fetch_full_state(self, tx):
        user_id = tx["user_id"]
        country = tx["country"]
        device_id = tx["device_id"]
        ip = tx["ip"]

        pipe = self.redis.pipeline()

        pipe.hgetall(self.user_key(user_id))
        pipe.hgetall(self.country_key(country))

        pipe.sismember(
            self.device_key(user_id),
            device_id
        )

        pipe.sismember(
            self.ip_key(user_id),
            ip
        )

        ts = datetime.fromisoformat(
            tx["timestamp"]
        ).timestamp()

        velocity_key = self.velocity_key(user_id)

        pipe.zcount(
            velocity_key,
            ts - 60,
            ts
        )

        pipe.zcount(
            velocity_key,
            ts - 300,
            ts
        )

        pipe.zcount(
            velocity_key,
            ts - 3600,
            ts
        )

        pipe.zcount(
            velocity_key,
            ts - 86400,
            ts
        )

        pipe.hgetall(
            self.merchant_counts_key(
                user_id
            )
        )

        pipe.hgetall(
            self.hour_counts_key(
                user_id
            )
        )

        pipe.hgetall(
            self.device_merchant_counts_key(
                user_id
            )
        )

        pipe.hgetall(
            self.transition_counts_key(
                user_id
            )
        )

        pipe.hgetall(
            self.outgoing_transition_counts_key(
                user_id
            )
        )

        results = pipe.execute()

        user_raw = results[0]
        country_raw = results[1]
        known_device = results[2]
        known_ip = results[3]

        tx_count_1m = results[4]
        tx_count_5m = results[5]
        tx_count_1h = results[6]
        tx_count_24h = results[7]

        merchant_counts = results[8]
        hour_counts = results[9]
        device_merchant_counts = results[10]
        transition_counts = results[11]
        outgoing_transition_counts = results[12]

        if not user_raw:
            user_state = {
                "avg_amount": 0.0,
                "tx_count": 0,
                "last_country": None,
                "last_lat": None,
                "last_lon": None,
                "last_timestamp": None,

                "tx_count_1m": tx_count_1m,
                "tx_count_5m": tx_count_5m,
                "tx_count_1h": tx_count_1h,
                "tx_count_24h": tx_count_24h,

                "small_amount_burst_count": 0,
                "merchant_repeat_count": 0,

                "distinct_devices_24h": 0,
                "distinct_ips_24h": 0,

                "last_merchant": None,
                "amount_sum": 0.0,
                "amount_sum_sq": 0.0,
            }

        else:
            user_state = {
                "avg_amount": float(user_raw.get("avg_amount", 0)),
                "tx_count": int(user_raw.get("tx_count", 0)),
                "last_country": user_raw.get("last_country"),
                "last_lat": float(user_raw["last_lat"]) if user_raw.get("last_lat") else None,
                "last_lon": float(user_raw["last_lon"]) if user_raw.get("last_lon") else None,
                "last_timestamp": user_raw.get("last_timestamp"),

                "tx_count_1m": tx_count_1m,
                "tx_count_5m": tx_count_5m,
                "tx_count_1h": tx_count_1h,
                "tx_count_24h": tx_count_24h,

                "small_amount_burst_count": int(
                    user_raw.get("small_amount_burst_count", 0)
                ),

                "merchant_repeat_count": int(
                    user_raw.get("merchant_repeat_count", 0)
                ),

                "distinct_devices_24h": int(
                    user_raw.get("distinct_devices_24h", 0)
                ),

                "distinct_ips_24h": int(
                    user_raw.get("distinct_ips_24h", 0)
                ),

                "last_merchant": user_raw.get("last_merchant"),

                "amount_sum": float(
                    user_raw.get(
                        "amount_sum",
                        0.0
                    )
                ),

                "amount_sum_sq": float(
                    user_raw.get(
                        "amount_sum_sq",
                        0.0
                    )
                ),
            }

        if not country_raw:
            country_state = {
                "avg_amount": 0.0,
                "tx_count": 0
            }
        else:
            country_state = {
                "avg_amount": float(country_raw.get("avg_amount", 0)),
                "tx_count": int(country_raw.get("tx_count", 0))
            }


        return {
            "user":user_state,
            "known_device":known_device,
            "known_ip":known_ip,
            "country":country_state,
            "merchant_counts":merchant_counts,
            "hour_counts":hour_counts,
            "device_merchant_counts":device_merchant_counts,
            "transition_counts":transition_counts,
            "outgoing_transition_counts":outgoing_transition_counts
        }