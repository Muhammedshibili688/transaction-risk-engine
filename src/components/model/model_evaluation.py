import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    average_precision_score
)


class ModelEvaluation:

    def load_model(
        self,
        model_path
    ):

        return joblib.load(
            model_path
        )

    def load_scaler(
        self,
        scaler_path
    ):

        return joblib.load(
            scaler_path
        )

    def evaluate(
        self,
        model,
        X_test,
        y_test
    ):

        predictions = (
            model.predict(
                X_test
            )
        )

        probabilities = (
            model.predict_proba(
                X_test
            )[:,1]
        )

        accuracy = (
            accuracy_score(
                y_test,
                predictions
            )
        )

        precision = (
            precision_score(
                y_test,
                predictions
            )
        )

        recall = (
            recall_score(
                y_test,
                predictions
            )
        )

        f1 = (
            f1_score(
                y_test,
                predictions
            )
        )

        roc_auc = (
            roc_auc_score(
                y_test,
                probabilities
            )
        )

        pr_auc = (
            average_precision_score(
                y_test,
                probabilities
            )
        )

        tn, fp, fn, tp = (
            confusion_matrix(
                y_test,
                predictions
            ).ravel()
        )

        review_rate = (
            (tp + fp)
            /
            len(y_test)
        )

        metrics = {

            "accuracy":
                accuracy,

            "precision":
                precision,

            "recall":
                recall,

            "f1":
                f1,

            "roc_auc":
                roc_auc,

            "pr_auc":
                pr_auc,

            "tp":
                int(tp),

            "fp":
                int(fp),

            "tn":
                int(tn),

            "fn":
                int(fn),

            "review_rate":
                review_rate
        }

        return metrics

    def show_metrics(
        self,
        metrics
    ):

        print("\n")
        print("=" * 80)
        print("MODEL METRICS")
        print("=" * 80)

        for k, v in metrics.items():

            print(
                f"{k}: {v}"
            )

    def show_coefficients(
        self,
        model,
        feature_columns
    ):

        coef_df = pd.DataFrame(
            {
                "feature":
                    feature_columns,

                "coefficient":
                    model.coef_[0]
            }
        )

        coef_df["abs_coef"] = (
            coef_df["coefficient"]
            .abs()
        )

        coef_df = (
            coef_df
            .sort_values(
                by="abs_coef",
                ascending=False
            )
        )

        print("\n")
        print("=" * 80)
        print("LOGISTIC COEFFICIENTS")
        print("=" * 80)

        print(
            coef_df[
                [
                    "feature",
                    "coefficient"
                ]
            ]
            .to_string(
                index=False
            )
        )
    
    def show_feature_importance(
        self,
        model,
        feature_columns
    ):

        import pandas as pd

        importance_df = pd.DataFrame(
            {
                "feature": feature_columns,
                "importance":
                model.feature_importances_
            }
        )

        importance_df = (
            importance_df
            .sort_values(
                "importance",
                ascending=False
            )
        )

        print("\n")
        print("=" * 80)
        print("FEATURE IMPORTANCE")
        print("=" * 80)

        print(
            importance_df.to_string(
                index=False
            )
        )