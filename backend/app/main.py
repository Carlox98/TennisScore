import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import init_db
from app.routers import predictions, players, tournaments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="Tennis Predictor API",
    description="ATP match prediction using Elo + XGBoost + Monte Carlo",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions.router)
app.include_router(players.router)
app.include_router(tournaments.router)


@app.on_event("startup")
def on_startup():
    init_db()
    # Try to load Elo + model if already trained
    try:
        from app.models.xgboost_model import get_model
        from app.models.elo import get_elo_system, EloSystem
        from app.database.db import SessionLocal
        from app.database.models import Match

        model = get_model()
        if not model.is_trained():
            logging.getLogger(__name__).warning(
                "Model not trained yet. Run: python -m app.database.seed"
            )
        else:
            # Rebuild Elo from DB
            db = SessionLocal()
            try:
                elo = get_elo_system()
                if not elo.elo_overall:
                    elo.compute_all(db)
            finally:
                db.close()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Startup model load: {e}")


@app.get("/")
def root():
    return {
        "name": "Tennis Predictor API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    from app.models.xgboost_model import get_model
    model = get_model()
    return {
        "status": "ok",
        "model_trained": model.is_trained(),
        "model_metrics": model.metrics,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
