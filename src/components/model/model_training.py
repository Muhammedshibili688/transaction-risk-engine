import joblib
from sklearn.model_selection import GridSearchCV
from xgboost import XGBClassifier


class ModelTraining:

    PARAM_GRID = {
        "C": [
            0.001,
            0.01,
            0.1,
            1,
            5,
            10,
            50,
            100
        ]
    }

    def train(
        self,
        X_train,
        y_train
    ):

        grid = GridSearchCV(
            XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            ),

            param_grid=
            self.PARAM_GRID,

            scoring=
            "average_precision",

            cv=5,

            n_jobs=-1
        )

        grid.fit(
            X_train,
            y_train
        )

        print("\n")
        print("=" * 80)
        print("GRID SEARCH RESULTS")
        print("=" * 80)

        print(
            "Best Params:",
            grid.best_params_
        )

        print(
            "Best CV PR-AUC:",
            round(
                grid.best_score_,
                4
            )
        )

        return (
            grid.best_estimator_,
            grid.best_params_
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

    def save_scaler(
        self,
        scaler,
        scaler_path
    ):

        joblib.dump(
            scaler,
            scaler_path
        )

        print(
            f"Scaler Saved -> {scaler_path}"
        )