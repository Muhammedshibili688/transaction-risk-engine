from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


class FeatureDefinitions:

    IMPOSSIBLE_TRAVEL_SPEED_KMH = 1000

    @staticmethod
    def geo_distance_km(
        lat1,
        lon1,
        lat2,
        lon2
    ):
        R = 6371.0

        lat1 = radians(lat1)
        lon1 = radians(lon1)

        lat2 = radians(lat2)
        lon2 = radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a)
        )

        return R * c

    @classmethod
    def geo_features(
        cls,
        tx,
        user_state
    ):

        if (
            user_state["last_lat"] is None
            or user_state["last_lon"] is None
            or user_state["last_timestamp"] is None
        ):
            return {
                "geo_distance": 0.0,
                "geo_speed": 0.0,
                "impossible_travel": 0
            }

        prev_ts = datetime.fromisoformat(
            user_state["last_timestamp"]
        )

        curr_ts = datetime.fromisoformat(
            tx["timestamp"]
        )

        elapsed_hours = (
            curr_ts - prev_ts
        ).total_seconds() / 3600

        if elapsed_hours <= 0:
            return {
                "geo_distance": 0.0,
                "geo_speed": 0.0,
                "impossible_travel": 0
            }

        distance = cls.geo_distance_km(
            user_state["last_lat"],
            user_state["last_lon"],
            tx["lat"],
            tx["lon"]
        )

        speed = distance / elapsed_hours

        return {
            "geo_distance": round(distance, 2),
            "geo_speed": round(speed, 2),
            "impossible_travel": int(
                speed >
                cls.IMPOSSIBLE_TRAVEL_SPEED_KMH
            )
        }

    @staticmethod
    def identity_features(
        tx,
        user_state,
        known_device,
        known_ip
    ):

        return {
            "is_new_device": int(
                not known_device
            ),

            "is_new_ip": int(
                not known_ip
            ),

            "distinct_devices_24h":
                user_state[
                    "distinct_devices_24h"
                ],

            "distinct_ips_24h":
                user_state[
                    "distinct_ips_24h"
                ],

            "country_change": int(
                user_state["last_country"]
                is not None
                and
                tx["country"]
                != user_state["last_country"]
            )
        }

    @staticmethod
    def amount_features(
        tx,
        user_state,
        country_state
    ):

        avg_amount = user_state[
            "avg_amount"
        ]

        country_avg = country_state[
            "avg_amount"
        ]

        amount_ratio = (
            tx["amount_usd"] / avg_amount
            if avg_amount > 0
            else 1.0
        )

        user_country_ratio = (
            tx["amount_usd"] / country_avg
            if country_avg > 0
            else 1.0
        )

        return {
            "amount_ratio":
                round(amount_ratio, 2),

            "country_avg_amount":
                round(country_avg, 2),

            "user_country_ratio":
                round(
                    user_country_ratio,
                    2
                )
        }

    @staticmethod
    def behavioral_features(
        user_state
    ):

        return {
            "transaction_count_1m":
                user_state["tx_count_1m"],

            "transaction_count_5m":
                user_state["tx_count_5m"],

            "transaction_count_1h":
                user_state["tx_count_1h"],

            "transaction_count_24h":
                user_state["tx_count_24h"],

            "small_amount_burst":
                user_state[
                    "small_amount_burst_count"
                ],

            "merchant_repeat_count":
                user_state[
                    "merchant_repeat_count"
                ]
        }