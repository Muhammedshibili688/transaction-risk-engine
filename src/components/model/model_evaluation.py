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
                features[tx["tx_id"]] = tx.get("is_fraud", 0)

        results = []
        with open(scoring_path, "r") as f:
            for line in f:
                tx = json.loads(line)
                tx_id = tx["tx_id"]

                if tx_id in features:
                    results.append({
                        "y_true": features[tx_id],
                        "y_pred": 1 if tx["verdict"] == "BLOCK" else 0
                    })

        return results

    def compute_metrics(self, data):
        TP = FP = TN = FN = 0

        for row in data:
            y_true = row["y_true"]
            y_pred = row["y_pred"]

            if y_true == 1 and y_pred == 1:
                TP += 1
            elif y_true == 0 and y_pred == 1:
                FP += 1
            elif y_true == 0 and y_pred == 0:
                TN += 1
            elif y_true == 1 and y_pred == 0:
                FN += 1

        precision = TP / (TP + FP) if (TP + FP) else 0
        recall = TP / (TP + FN) if (TP + FN) else 0
        fpr = FP / (FP + TN) if (FP + TN) else 0
        fnr = FN / (FN + TP) if (FN + TP) else 0

        return {
            "TP": TP,
            "FP": FP,
            "TN": TN,
            "FN": FN,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4)
        }