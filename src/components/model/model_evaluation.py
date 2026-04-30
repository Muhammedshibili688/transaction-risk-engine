# import json
# from collections import defaultdict


# class FraudModelEvaluator:
#     def __init__(self):
#         self.metrics = defaultdict(int)

#     def load_data(self, feature_path, scoring_path):
#         features = {}
#         with open(feature_path, "r") as f:
#             for line in f:
#                 tx = json.loads(line)
#                 features[tx["tx_id"]] = {
#                 "is_fraud": tx.get("is_fraud", 0),
#                 "amount": tx.get("amount_usd", 0)
#                 }

#         results = []
#         with open(scoring_path, "r") as f:
#             for line in f:
#                 tx = json.loads(line)
#                 tx_id = tx["tx_id"]

#                 if tx_id in features:
#                     results.append({
#                         "y_true": features[tx_id]["is_fraud"],
#                         # "y_pred": 1 if tx["verdict"] == "BLOCK" else 0,
#                         "risk_score": tx.get("risk_score", 0),
#                         "amount": features[tx_id]["amount"]
#                     })

#         print(f"Loaded features: {len(features)}")
#         print(f"Matched results: {len(results)}")

#         return results

#     def compute_metrics(self, data, cost_per_review=2.0):
#         TP = FP = TN = FN = 0
#         total_fraud_amount = 0
#         missed_fraud_amount = 0

#         for row in data:
#             y_true = row["y_true"]
#             score = row["risk_score"]
#             y_pred = 1 if score >= threshold else 0
#             amount = row["amount"]

#             if y_true == 1:
#                 total_fraud_amount += amount

#             if y_true == 1 and y_pred == 1:
#                 TP += 1
#             elif y_true == 0 and y_pred == 1:
#                 FP += 1
#             elif y_true == 0 and y_pred == 0:
#                 TN += 1
#             elif y_true == 1 and y_pred == 0:
#                 FN += 1
#                 missed_fraud_amount += amount

#         TOTAL = (TP + FP +TN + FN)

#         if TOTAL == 0:
#             return {
#                 "error": "No matching data between features and scoring"
#             }

#         precision = TP / (TP + FP) if (TP + FP) else 0
#         recall = TP / (TP + FN) if (TP + FN) else 0
#         fpr = FP / (FP + TN) if (FP + TN) else 0
#         fnr = FN / (FN + TP) if (FN + TP) else 0

#         fraude_rate = (FN + TP) / TOTAL
#         alert_rate = (TP + FP) / TOTAL

#         expected_loss = missed_fraud_amount
#         review_cost = FP * cost_per_review

#         return {
#             "TP": TP,
#             "FP": FP,
#             "TN": TN,
#             "FN": FN,
#             "precision": round(precision, 4),
#             "recall": round(recall, 4),

#             "false_positive_rate": round(fpr, 4),
#             "false_negative_rate": round(fnr, 4),

#             "expected_loss_usd": round(expected_loss, 2),
#             "review_cost_usd": round(review_cost, 2)
#         }



import json
from collections import defaultdict


class FraudModelEvaluator:
    def __init__(self):
        self.metrics = defaultdict(int)

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    def load_data(self, feature_path, scoring_path):
        features = {}

        # Load feature data (ground truth)
        with open(feature_path, "r") as f:
            for line in f:
                tx = json.loads(line)
                features[tx["tx_id"]] = {
                    "is_fraud": tx.get("is_fraud", 0),
                    "amount": tx.get("amount_usd", 0)
                }

        results = []

        # Load scoring output
        with open(scoring_path, "r") as f:
            for line in f:
                tx = json.loads(line)
                tx_id = tx["tx_id"]

                if tx_id in features:
                    results.append({
                        "y_true": features[tx_id]["is_fraud"],
                        "risk_score": tx.get("risk_score", 0),
                        "amount": features[tx_id]["amount"]
                    })

        print(f"Loaded features: {len(features)}")
        print(f"Matched results: {len(results)}")

        return results

    # -----------------------------
    # COMPUTE METRICS
    # -----------------------------
    def compute_metrics(self, data, threshold=60, cost_per_review=2.0):

        if not data:
            return {
                "error": "No matching data between features and scoring"
            }

        TP = FP = TN = FN = 0
        total_fraud_amount = 0
        missed_fraud_amount = 0

        for row in data:
            y_true = row["y_true"]
            score = row["risk_score"]
            amount = row["amount"]

            # Threshold-based prediction
            y_pred = 1 if score >= threshold else 0

            if y_true == 1:
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

        TOTAL = TP + FP + TN + FN

        if TOTAL == 0:
            return {
                "error": "No valid predictions"
            }

        # -----------------------------
        # CLASSIFICATION METRICS
        # -----------------------------
        precision = TP / (TP + FP) if (TP + FP) else 0
        recall = TP / (TP + FN) if (TP + FN) else 0
        fpr = FP / (FP + TN) if (FP + TN) else 0
        fnr = FN / (FN + TP) if (FN + TP) else 0

        fraud_rate = (FN + TP) / TOTAL
        alert_rate = (TP + FP) / TOTAL

        # -----------------------------
        # BUSINESS METRICS
        # -----------------------------
        expected_loss = missed_fraud_amount
        review_cost = FP * cost_per_review
        total_cost = expected_loss + review_cost

        return {
            "threshold": threshold,

            # confusion matrix
            "TP": TP,
            "FP": FP,
            "TN": TN,
            "FN": FN,

            # classification
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),

            # system behavior
            "fraud_rate": round(fraud_rate, 4),
            "alert_rate": round(alert_rate, 4),

            # business impact
            "expected_loss_usd": round(expected_loss, 2),
            "review_cost_usd": round(review_cost, 2),
            "total_cost_usd": round(total_cost, 2)
        }