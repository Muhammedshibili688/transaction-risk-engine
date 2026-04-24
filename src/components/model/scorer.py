class FraudScorer:
    def calculate_heuristic_score(self, tx: dict) -> int:
        """Calculates a risk score from 0 to 100."""
        score = 0
        if tx['impossible_travel'] == 1: score += 50
        if tx['amount_ratio'] > 5: score += 30
        if tx['is_new_device'] == 1: score += 20
        if tx['merchant_category'] == 'high_risk': score += 10
        
        return min(score, 100)