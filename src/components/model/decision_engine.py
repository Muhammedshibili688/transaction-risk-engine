from src.entity.config_entity import DecisionConfig

class DecisionEngine:
    def __init__(self, config):
        self.high = config.high_risk_threshold
        self.medium = config.medium_risk_threshold

    def get_verdict(self, score: int) -> str:
        if score >= self.high:
            return "BLOCK"
        elif score >= self.medium:
            return "CHALLENGE_OTP"
        return "ALLOW"
    