import logging

from app.database.db import init_db, SessionLocal
from app.services.data_loader import run_full_pipeline
from app.models.elo import init_elo_system
from app.services.feature_engine import FeatureEngine
from app.models.elo import get_elo_system
from app.models.xgboost_model import TennisXGBoost

logger = logging.getLogger(__name__)


def seed_all():
    """Run the full pipeline: download data, init DB, compute Elo, train model."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # 1. Init database tables
    logger.info("Step 1/5: Initializing database...")
    init_db()

    # 2. Download & load data
    logger.info("Step 2/5: Downloading and loading data...")
    run_full_pipeline()

    # 3. Compute Elo
    logger.info("Step 3/5: Computing Elo ratings...")
    db = SessionLocal()
    try:
        elo = init_elo_system(db)
    finally:
        db.close()

    # 4. Build features
    logger.info("Step 4/5: Building features...")
    db = SessionLocal()
    try:
        fe = FeatureEngine(get_elo_system())
        features_df = fe.build_features_from_db(db)
    finally:
        db.close()

    # 5. Train model
    logger.info("Step 5/5: Training XGBoost model...")
    model = TennisXGBoost()
    metrics = model.train(features_df)
    logger.info(f"Training complete! Metrics: {metrics}")

    return metrics


if __name__ == "__main__":
    seed_all()
