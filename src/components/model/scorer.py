import logging

class FraudScorer:
    def __init__(self, rule_config: dict):
        self.weights = rule_config.get('weights', {})
        self.limits = rule_config.get('thresholds', {})

    def calculate_heuristic_score(self, tx: dict) -> int:
        score = 0
        
        # 1. Geo Speed Logic
        if tx.get('geo_speed', 0) > self.limits.get('geo_speed_limit', 900):
            score += self.weights.get('impossible_travel', 0)
            
        # 2. Amount Ratio Logic
        if tx.get('amount_ratio', 0) > self.limits.get('amount_ratio_limit', 5.0):
            score += self.weights.get('high_risk_merchant', 0)
            
        # 3. New Device Logic
        if tx.get('is_new_device', 0) == 1:
            score += self.weights.get('new_device', 0)
            
        return min(score, 100)