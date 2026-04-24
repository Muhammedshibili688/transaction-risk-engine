from src.entity.config_entity import DecisionConfig

class DecisionEngine:
    def __init__(self, config: DecisionConfig):
        self.config = config

    def get_verdict(self, score: int) -> str:
        if score >= self.config.high_risk_threshold:
            return "BLOCK"
        elif score >= self.config.medium_risk_threshold:
            return "CHALLENGE_OTP"
        return "ALLOW"