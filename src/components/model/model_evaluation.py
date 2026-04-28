import json
from collections import defaultdict


class FraudModelEvaluator:
    def __init__(self):
        self.metrics = defaultdict(int)

    def load_data(self, feature_path, scoring_path):
        features = {}
        with open(feature_path, "r") as f:
            for line in f:
                tx = json.loads(line)
                features[tx["tx_id"]] = {
                "is_fraud": tx.get("is_fraud", 0),
                "amount": tx.get("amount_usd", 0)
                }

        results = []
        with open(scoring_path, "r") as f:
            for line in f:
                tx = json.loads(line)
                tx_id = tx["tx_id"]

                if tx_id in features:
                    results.append({
                        "y_true": features[tx_id],
                        "y_pred": 1 if tx["verdict"] == "BLOCK" else 0,
                        "amount": features[tx_id]["amount"]
                    })

        return results

    def compute_metrics(self, data):
        TP = FP = TN = FN = 0
        total_fraud_amount = 0
        missed_fraud_amount = 0

        for row in data:
            y_true = row["y_true"]
            y_pred = row["y_pred"]
            amount = row["amount"]

            if t_true == 1:
                total_fraud_amount += amount

            if y_true == 1 and y_pred == 1:
                TP += 1
            elif y_true == 0 and y_pred == 1:
                FP += 1
            elif y_true == 0 and y_pred == 0:
                TN += 1
            elif y_true == 1 and y_pred == 0:
                FN += 1
                missed_fraud_amount += amount

        TOTAL = (TP + FP +TN + FN)

        precision = TP / (TP + FP) if (TP + FP) else 0
        recall = TP / (TP + FN) if (TP + FN) else 0
        fpr = FP / (FP + TN) if (FP + TN) else 0
        fnr = FN / (FN + TP) if (FN + TP) else 0

        fraude_rate = (FN + TP) / TOTAL
        alert_rate = (TP + FP) / TOTAL

        expected_loss = missed_fraud_amount
        review_cost = FP * cost_per_review

        return {
            "TP": TP,
            "FP": FP,
            "TN": TN,
            "FN": FN,
            "precision": round(precision, 4),
            "recall": round(recall, 4),

            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),

            "expected_loss_usd": round(expected_loss, 2),
            "review_cost_usd": round(review_cost, 2)
        }