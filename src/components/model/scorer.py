class FraudScorer:
    def __init__(self, rule_config: dict):
        self.cfg = rule_config
        self.weights = rule_config['weights']
        self.limits = rule_config['thresholds']

    def calculate_score(self, tx: dict) -> int:
        score = 0
        
        # 1. Geo Logic (using limits from YAML)
        if tx['geo_speed'] > self.limits['geo_speed_limit']:
            score += self.weights['impossible_travel']
            
        # 2. Amount logic
        if tx['amount_ratio'] > self.limits['amount_ratio_limit']:
            score += self.weights['high_risk_merchant']
            
        return min(score, 100)