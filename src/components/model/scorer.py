import logging


class FraudScorer:
    def __init__(self, rule_config: dict):
        self.weights = rule_config.get('weights', {})
        self.limits = rule_config.get('thresholds', {})

    def calculate_heuristic_score(self, tx: dict) -> int:
        score = 0

        # 1. Impossible travel
        if tx.get('geo_speed', 0) > self.limits.get('geo_speed_limit', 900):
            score += self.weights.get('impossible_travel', 0)

        # 2. Amount ratio (large spend vs user average)
        if tx.get('amount_ratio', 0) > self.limits.get('amount_ratio_limit', 5.0):
            score += self.weights.get('high_risk_merchant', 0)

        # 3. New device
        if tx.get('is_new_device', 0) == 1:
            score += self.weights.get('new_device', 0)

        # 4. Velocity burst — many transactions in last 1 min
        if tx.get('transaction_count_1m', 0) > 5:
            score += self.weights.get('velocity_burst', 0)

        # 5. Small amount burst — card testing probe pattern
        if tx.get('small_amount_burst', 0) > 2:
            score += self.weights.get('small_amount_burst', 0)

        # 6. Merchant repeat — same merchant hit repeatedly in 5 min
        if tx.get('merchant_repeat_count', 0) > 4:
            score += self.weights.get('merchant_repeat', 0)

        # 7. Card testing combo — small amount + new device together
        if tx.get('amount_usd', 0) < 20 and tx.get('is_new_device', 0) == 1:
            score += self.weights.get('card_testing_combo', 0)

        return min(score, 100)