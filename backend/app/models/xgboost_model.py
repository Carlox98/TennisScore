import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier

from app.config import MODELS_DIR

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "p1_elo", "p2_elo", "elo_diff",
    "p1_surf_elo", "p2_surf_elo", "surf_elo_diff",
    "p1_rank", "p2_rank", "rank_diff",
    "p1_win10", "p2_win10", "p1_win20", "p2_win20",
    "p1_win10_surf", "p2_win10_surf",
    "p1_1st_pct", "p2_1st_pct",
    "p1_srv_won", "p2_srv_won",
    "p1_ret_won", "p2_ret_won",
    "p1_ace_avg", "p2_ace_avg",
    "p1_df_avg", "p2_df_avg",
    "p1_bp_saved", "p2_bp_saved",
    "p1_bp_conv", "p2_bp_conv",
    "p1_h2h", "p2_h2h",
    "p1_h2h_surf", "p2_h2h_surf",
    "p1_matches_7d", "p2_matches_7d",
    "p1_matches_14d", "p2_matches_14d",
    "p1_matches_30d", "p2_matches_30d",
    "p1_age", "p2_age",
    "p1_height", "p2_height",
    "p1_hand_R", "p2_hand_R",
    "surface_hard", "surface_clay", "surface_grass",
    "level_ord", "round_ord", "best_of",
]

MODEL_PATH = MODELS_DIR / "xgboost_v1.pkl"


class TennisXGBoost:
    def __init__(self):
        self.model: XGBClassifier | None = None
        self.metrics: dict = {}
        self.feature_importance: dict = {}

    def train(self, df: pd.DataFrame) -> dict:
        logger.info(f"Training XGBoost on {len(df)} samples...")
        df = df.dropna(subset=["target"])

        X = df[FEATURE_COLS].fillna(0)
        y = df["target"].astype(int)

        # Time-series split: train on first 80%, test on last 20%
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            reg_alpha=0.1,
            reg_lambda=1.0,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        # Evaluate
        y_prob = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        self.metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "log_loss": round(log_loss(y_test, y_prob), 4),
            "brier_score": round(brier_score_loss(y_test, y_prob), 4),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        logger.info(f"Model metrics: {self.metrics}")

        # Feature importance
        importances = self.model.feature_importances_
        self.feature_importance = dict(
            sorted(zip(FEATURE_COLS, importances), key=lambda x: -x[1])
        )

        # Save
        self.save()
        return self.metrics

    def predict(self, features: dict) -> float:
        if self.model is None:
            self.load()
        row = pd.DataFrame([features])[FEATURE_COLS].fillna(0)
        prob = self.model.predict_proba(row)[0][1]
        return float(prob)

    def save(self):
        MODEL_PATH.parent.mkdir(exist_ok=True)
        joblib.dump({
            "model": self.model,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
        }, MODEL_PATH)
        logger.info(f"Model saved to {MODEL_PATH}")

    def load(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"No trained model at {MODEL_PATH}")
        data = joblib.load(MODEL_PATH)
        self.model = data["model"]
        self.metrics = data.get("metrics", {})
        self.feature_importance = data.get("feature_importance", {})
        logger.info("Model loaded")

    def is_trained(self) -> bool:
        return self.model is not None or MODEL_PATH.exists()


# Module singleton
_model_instance: TennisXGBoost | None = None


def get_model() -> TennisXGBoost:
    global _model_instance
    if _model_instance is None:
        _model_instance = TennisXGBoost()
        if MODEL_PATH.exists():
            _model_instance.load()
    return _model_instance
