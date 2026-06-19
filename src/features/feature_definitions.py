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

        count = user_state["tx_count"]

        amount_sum = user_state[
            "amount_sum"
        ]

        amount_sum_sq = user_state[
            "amount_sum_sq"
        ]

        if count < 2:
            z_score = 0.0

        else:
            mean = amount_sum / count

            variance = (
                amount_sum_sq / count
            ) - (mean * mean)

            variance = max(
                variance,
                1e-6
            )

            std = variance ** 0.5

            z_score = (
                tx["amount_usd"]
                - mean
            ) / std

    

        return {
            "amount_ratio":
                round(amount_ratio, 2),

            "country_avg_amount":
                round(country_avg, 2),

            "user_country_ratio":
                round(user_country_ratio,2),

            "z_score":round(z_score, 4)
        }

    @staticmethod
    def behavioral_features(
        tx,
        state
    ):

        user_state = state["user"]

        merchant_counts = state["merchant_counts"]

        hour_counts = state["hour_counts"]

        device_merchant_counts = (
            state["device_merchant_counts"]
        )

        transition_counts = (
            state["transition_counts"]
        )

        outgoing_transition_counts = (
            state["outgoing_transition_counts"]
        )





        total_tx = max(
            user_state["tx_count"],
            1
        )

        if user_state["tx_count"] == 0:
            print(
                {
                    "type": "COLD USER",
                    "user_id": tx["user_id"]
                }
            )

        merchant_count = int(
            merchant_counts.get(
                tx["merchant"],
                0
            )
        )









        if merchant_count > total_tx:
            print(
            {
                "type": "MERCHANT BUG",
                "user_id": tx["user_id"],
                "merchant_count": merchant_count,
                "total_tx": total_tx
            }
        )












        merchant_affinity_score = (
            merchant_count
            / total_tx
        )

        # =========================================================
        if merchant_affinity_score > 1:
                print(
                    {   
                        "type": "MERCHANT SCORE > 1",
                        "user_id": tx["user_id"],
                        "merchant_count": merchant_count,
                        "total_tx": total_tx
                    }
                )        
        # =========================================================

        device_key = (
            f"{tx['device_id']}|"
            f"{tx['merchant']}"
        )

        pair_count = int(
            device_merchant_counts.get(
                device_key,
                0
            )
        )







        if pair_count > total_tx:
            print(
                {
                    "type": "DEVICE BUG",
                    "user_id": tx["user_id"],
                    "pair_count": pair_count,
                    "total_tx": total_tx
                    }
            )

 





        device_merchant_affinity_score = (
            pair_count
            / total_tx
        )


        # =======================================
        if device_merchant_affinity_score > 1:
            print(
                {   
                    "type": "DEVICE SCORE > 1",
                    "user_id": tx["user_id"],
                    "pair_count": pair_count,
                    "total_tx": total_tx
                }
            )
        # =========================================


        hour = str(
            datetime.fromisoformat(
                tx["timestamp"]
            ).hour
        )

        hour_count = int(
            hour_counts.get(
                hour,
                0
            )
        )








        if hour_count > total_tx:
            print(
                {
                    "type":"HOUR BUG",
                    "user_id": tx["user_id"],
                    "hour_count": hour_count,
                    "total_tx": total_tx
                }
            )













        hour_preference_score = (
            hour_count
            / total_tx
        )
        # ====================================================
        if hour_preference_score > 1:
                print(
                    {   
                        "type": "HOUR SCORE > 1",
                        "user_id": tx["user_id"],
                        "hour_count": hour_count,
                        "total_tx": total_tx
                    }
                )
        # =====================================================

        previous_merchant = (
            user_state["last_merchant"]
        )

        if previous_merchant == None:

            merchant_transition_score = 0.0

        else:
            transition_key = (
                f"{previous_merchant}|"
                f"{tx['merchant']}"
            )

            transition_count = int(
                transition_counts.get(
                    transition_key,
                    0
                )
            )

            outgoing_count = int(
                outgoing_transition_counts.get(
                    previous_merchant,
                    0
                )
            )






            if outgoing_count < transition_count:
                print(
                    {
                        "type":"TRANSITION BUG",
                        "user_id": tx["user_id"],
                        "transition_count": transition_count,
                        "outgoing_count": outgoing_count
                    }
                )






            merchant_transition_score = (
                transition_count
                / max(outgoing_count, 1)
            )

            # ====================================================
            

            if merchant_transition_score > 1:
                print(
                    {   
                        "type": "MERCHANT TRANSITION SCORE > 1",
                        "user_id": tx["user_id"],
                        "transition_count": transition_count,
                        "outgoing_count": outgoing_count
                    }
                )
            # =====================================================

            

        


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
                ],

            "merchant_affinity_score":
                round(
                    merchant_affinity_score,
                    4
                ),

            "hour_preference_score":
                round(
                    hour_preference_score,
                    4
                ),

            "device_merchant_affinity_score":
                round(
                    device_merchant_affinity_score,
                    4
                ),

            "merchant_transition_score":
                round(
                    merchant_transition_score,
                    4
                )
        }