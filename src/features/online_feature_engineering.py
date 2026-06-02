# from datetime import datetime
# from math import radians, sin, cos, sqrt, atan2


# class OnlineFeatureEngineer:
#     IMPOSSIBLE_TRAVEL_SPEED_KMH = 1000

#     def _geo_distance_km(self, lat1, lon1, lat2, lon2):
#         """
#         Haversine distance in KM
#         """
#         R = 6371.0

#         lat1 = radians(lat1)
#         lon1 = radians(lon1)
#         lat2 = radians(lat2)
#         lon2 = radians(lon2)

#         dlat = lat2 - lat1
#         dlon = lon2 - lon1

#         a = (
#             sin(dlat / 2) ** 2
#             + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
#         )

#         c = 2 * atan2(sqrt(a), sqrt(1 - a))

#         return R * c

#     def _geo_features(self, tx, state):
#         user = state["user"]

#         if (
#             user["last_lat"] is None
#             or user["last_lon"] is None
#             or user["last_timestamp"] is None
#         ):
#             return {
#                 "geo_distance": 0.0,
#                 "geo_speed": 0.0,
#                 "impossible_travel": 0,
#             }

#         prev_ts = datetime.fromisoformat(user["last_timestamp"])
#         curr_ts = datetime.fromisoformat(tx["timestamp"])

#         elapsed_hours = (
#             (curr_ts - prev_ts).total_seconds() / 3600
#         )

#         if elapsed_hours <= 0:
#             return {
#                 "geo_distance": 0.0,
#                 "geo_speed": 0.0,
#                 "impossible_travel": 0,
#             }

#         distance = self._geo_distance_km(
#             user["last_lat"],
#             user["last_lon"],
#             tx["lat"],
#             tx["lon"],
#         )

#         speed = distance / elapsed_hours

#         return {
#             "geo_distance": round(distance, 2),
#             "geo_speed": round(speed, 2),
#             "impossible_travel": int(
#                 speed > self.IMPOSSIBLE_TRAVEL_SPEED_KMH
#             ),
#         }
    
#     def device_history_key(self, user_id):
#         return f"user:{user_id}:devices:24h"


#     def ip_history_key(self, user_id):
#         return f"user:{user_id}:ips:24h"

#     def _identity_features(self, tx, state):
#         user = state["user"]

#         is_new_device = int(not state["known_device"])
#         is_new_ip = int(not state["known_ip"])

#         return {
#             "is_new_device": is_new_device,
#             "is_new_ip": is_new_ip,
#             "distinct_devices_24h": user["distinct_devices_24h"],
#             "distinct_ips_24h": user["distinct_ips_24h"],
#             "country_change": int(
#                 user["last_country"] is not None
#                 and tx["country"] != user["last_country"]
#             ),
#         }

#     def _amount_features(self, tx, state):
#         user = state["user"]
#         country = state["country"]

#         avg_amount = user["avg_amount"]
#         country_avg = country["avg_amount"]

#         amount_ratio = (
#             tx["amount_usd"] / avg_amount
#             if avg_amount > 0
#             else 1.0
#         )

#         user_country_ratio = (
#             tx["amount_usd"] / country_avg
#             if country_avg > 0
#             else 1.0
#         )

#         return {
#             "amount_ratio": round(amount_ratio, 2),
#             "country_avg_amount": round(country_avg, 2),
#             "user_country_ratio": round(user_country_ratio, 2),
#         }

#     def _behavioral_features(self, state):
#         user = state["user"]

#         return {
#             "transaction_count_1m": user["tx_count_1m"],
#             "transaction_count_5m": user["tx_count_5m"],
#             "transaction_count_1h": user["tx_count_1h"],
#             "transaction_count_24h": user["tx_count_24h"],
#             "small_amount_burst": user["small_amount_burst_count"],
#             "merchant_repeat_count": user["merchant_repeat_count"],
#         }

#     def compute(self, tx, state):
#         enriched = tx.copy()

#         enriched.update(
#             self._geo_features(tx, state)
#         )

#         enriched.update(
#             self._identity_features(tx, state)
#         )

#         enriched.update(
#             self._amount_features(tx, state)
#         )

#         enriched.update(
#             self._behavioral_features(state)
#         )

#         return enriched



from src.features.feature_definitions import FeatureDefinitions

class OnlineFeatureEngineer:

    def compute(self, tx, state):

        user = state["user"]

        enriched = {}

        enriched.update(
            FeatureDefinitions.geo_features(
                tx,
                user
            )
        )

        enriched.update(
            FeatureDefinitions.identity_features(
                tx,
                user,
                state["known_device"],
                state["known_ip"]
            )
        )

        enriched.update(
            FeatureDefinitions.amount_features(
                tx,
                user,
                state["country"]
            )
        )

        enriched.update(
            FeatureDefinitions.behavioral_features(
                user
            )
        )

        return enriched