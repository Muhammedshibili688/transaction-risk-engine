import json
import sys
from src.utils.main_utils import calculate_haversine_distance, calculate_time_delta_hours
from src.exception import FraudException
from src.logger import logging

class FraudFeatureEngineer:
    def __init__(self, speed_threshold: float = 900.0):
        self.IMPOSSIBLE_SPEED_THRESHOLD = speed_threshold

    def compute_enriched_features(self, tx: dict, user_state: dict, country_state: dict) -> dict:
        """
        Generates the 11 behavioral features requested.
        """
        try:
            # 1. RAW INPUTS
            amount = float(tx['amount_usd'])
            
            # User History (from Redis)
            last_lat = float(user_state.get('last_lat', tx['lat']))
            last_lon = float(user_state.get('last_lon', tx['lon']))
            last_time = user_state.get('last_time', tx['timestamp'])
            user_avg = float(user_state.get('avg_amount', amount))
            
            known_devices = json.loads(user_state.get('devices', '[]'))
            known_ips = json.loads(user_state.get('ips', '[]'))
            
            # Country Context (from Redis)
            country_total = float(country_state.get('total_amount', 0))
            country_count = int(country_state.get('tx_count', 0))
            country_avg = country_total / country_count if country_count > 0 else amount

            # 2. FEATURE GENERATION
            # --- Amount Features ---
            amount_ratio = amount / user_avg if user_avg > 0 else 1.0
            user_country_ratio = amount / country_avg if country_avg > 0 else 1.0

            # --- Geo & Speed Features ---
            dist = calculate_haversine_distance(last_lat, last_lon, tx['lat'], tx['lon'])
            hours = calculate_time_delta_hours(last_time, tx['timestamp'])
            speed = dist / hours
            impossible_travel = 1 if speed > self.IMPOSSIBLE_SPEED_THRESHOLD else 0

            # --- Identity Features ---
            is_new_device = 1 if tx['device_id'] not in known_devices else 0
            is_new_ip = 1 if tx['ip'] not in known_ips else 0
            
            # These counts are retrieved from the current Redis state
            # Note: They are incremented in the Consumer after this step
            device_switch_count = int(user_state.get('device_switch_count', 0))
            ip_switch_count = int(user_state.get('ip_switch_count', 0))
            
            country_change = 1 if tx['country'] != user_state.get('last_country', tx['country']) else 0

            # 3. CONSOLIDATE OUTPUT (Exactly as per your list)
            return {
                "amount_ratio": round(float(amount_ratio), 2),
                "geo_distance": round(float(dist), 2),
                "geo_speed": round(float(speed), 2),
                "impossible_travel": int(impossible_travel),
                "is_new_device": int(is_new_device),
                "is_new_ip": int(is_new_ip),
                "device_switch_count": int(device_switch_count),
                "ip_switch_count": int(ip_switch_count),
                "country_change": int(country_change),
                "country_avg_amount": round(float(country_avg), 2),
                "user_country_ratio": round(float(user_country_ratio), 2)
            }

        except Exception as e:
            raise FraudException(e, sys)