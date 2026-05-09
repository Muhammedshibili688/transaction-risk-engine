# import logging


# class FraudScorer:
#     def __init__(self, rule_config: dict):
#         self.weights = rule_config.get('weights', {})
#         self.limits = rule_config.get('thresholds', {})

#     def calculate_heuristic_score(self, tx: dict) -> int:
#         score = 0

#         # 1. Impossible travel
#         if tx.get('geo_speed', 0) > self.limits.get('geo_speed_limit', 900):
#             score += self.weights.get('impossible_travel', 0)

#         # 2. Amount ratio (large spend vs user average)
#         if tx.get('amount_ratio', 0) > self.limits.get('amount_ratio_limit', 5.0):
#             score += self.weights.get('high_risk_merchant', 0)

#         # 3. New device
#         if tx.get('is_new_device', 0) == 1:
#             score += self.weights.get('new_device', 0)

#         # 4. Velocity burst — many transactions in last 1 min
#         if tx.get('transaction_count_1m', 0) > 5:
#             score += self.weights.get('velocity_burst', 0)

#         # 5. Small amount burst — card testing probe pattern
#         if tx.get('small_amount_burst', 0) > 2:
#             score += self.weights.get('small_amount_burst', 0)

#         # 6. Merchant repeat — same merchant hit repeatedly in 5 min
#         if tx.get('merchant_repeat_count', 0) > 4:
#             score += self.weights.get('merchant_repeat', 0)

#         # 7. Card testing combo — small amount + new device together
#         if tx.get('amount_usd', 0) < 20 and tx.get('is_new_device', 0) == 1:
#             score += self.weights.get('card_testing_combo', 0)

#         return min(score, 100)



import math
from src.logger import logging


class FraudScorer:
    def __init__(self, rule_config: dict):
        self.weights = rule_config.get('weights', {})
        self.limits = rule_config.get('thresholds', {})

    def _identity_risk(self, tx: dict) -> int:
        """New device + new IP signals."""
        score = 0
        if tx.get('is_new_device', 0) == 1:
            score += self.weights.get('new_device', 0)
        if tx.get('is_new_ip', 0) == 1:
            score += self.weights.get('new_ip', 0)
        if tx.get('country_change', 0) == 1:
            score += self.weights.get('country_change', 0)
        return min(score, 40)

    def _behavioral_risk(self, tx: dict) -> int:

        score = 0
        speed = tx.get('geo_speed', 0)
        speed_limit = self.limits.get('geo_speed_limit', 1050)

        if speed > speed_limit:
            # /250 instead of /500 — more aggressive escalation
            score += min(70, int((speed - speed_limit) / 250 * 40))

        ratio = tx.get('amount_ratio', 0)
        ratio_limit = self.limits.get('amount_ratio_limit', 3.0)
        if ratio > ratio_limit:
            score += min(30, int((ratio / ratio_limit) * 10))

        return min(score, 70)

    def _velocity_risk(self, tx: dict) -> int:
        """Transaction frequency signals — continuous."""
        tx_count = tx.get('transaction_count_1m', 0)
        burst = tx.get('small_amount_burst', 0)
        merchant_repeat = tx.get('merchant_repeat_count', 0)

        velocity_score = min(20, tx_count * 3)
        burst_score = min(15, burst * 5)
        merchant_score = min(10, merchant_repeat * 2)

        return min(velocity_score + burst_score + merchant_score, 35)

    def _amount_risk(self, tx: dict) -> int:
        amount = tx.get('amount_usd', 0)
        tx_count = tx.get('transaction_count_1m', 0)
        
        # amount < 20 + high velocity = probing pattern
        if amount < 5:
            return 15
        elif amount < 20 and tx_count >= 3:  # ← velocity not burst (no double count)
            return 8
        return 0

    def calculate_heuristic_score(self, tx: dict) -> int:
        identity = self._identity_risk(tx)
        behavioral = self._behavioral_risk(tx)
        velocity = self._velocity_risk(tx)
        amount = self._amount_risk(tx)

        total = identity + behavioral + velocity + amount
        return min(total, 100)