import joblib

from xgboost import (
    XGBClassifier
)


class XGBoostTraining:

    def train(
        self,
        X_train,
        y_train
    ):

        model = XGBClassifier(

            objective="binary:logistic",

            n_estimators=100,

            max_depth=6,

            learning_rate=0.1,

            subsample=0.8,

            colsample_bytree=0.8,

            random_state=42,

            eval_metric="logloss",

            n_jobs=-1
        )

        model.fit(
            X_train,
            y_train
        )

        print("\n")
        print("=" * 80)
        print("XGBOOST BASELINE")
        print("=" * 80)

        return (
            model,
            {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8
            }
        )

    def save_model(
        self,
        model,
        model_path
    ):

        joblib.dump(
            model,
            model_path
        )

        print(
            f"Model Saved -> {model_path}"
        )