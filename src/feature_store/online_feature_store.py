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

        new_count = old_count + 1

        if old_count == 0:
            new_avg = amount
        else:
            new_avg = (
                (old_avg * old_count) + amount
            ) / new_count

        # -----------------------------
        # velocity counters
        # -----------------------------
        # def update_window(count, start_ts, seconds):
        #     if not start_ts:
        #         return 1, curr_dt.isoformat()

        #     start_dt = datetime.fromisoformat(start_ts)

        #     elapsed = (
        #         curr_dt - start_dt
        #     ).total_seconds()

        #     if elapsed > seconds:
        #         return 1, curr_dt.isoformat()

        #     return count + 1, start_ts

        # tx_count_1m, window_1m_start = update_window(
        #     state["tx_count_1m"],
        #     state["window_1m_start"],
        #     60
        # )

        # tx_count_5m, window_5m_start = update_window(
        #     state["tx_count_5m"],
        #     state["window_5m_start"],
        #     300
        # )

        # tx_count_1h, window_1h_start = update_window(
        #     state["tx_count_1h"],
        #     state["window_1h_start"],
        #     3600
        # )

        # tx_count_24h, window_24h_start = update_window(
        #     state["tx_count_24h"],
        #     state["window_24h_start"],
        #     86400
        # )

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

                "last_merchant": tx["merchant"]
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

        results = pipe.execute()

        user_raw = results[0]
        country_raw = results[1]
        known_device = results[2]
        known_ip = results[3]

        tx_count_1m = results[4]
        tx_count_5m = results[5]
        tx_count_1h = results[6]
        tx_count_24h = results[7]

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
            "user": user_state,
            "known_device": known_device,
            "known_ip": known_ip,
            "country": country_state
        }