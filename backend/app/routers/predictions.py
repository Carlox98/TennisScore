from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.predictor import predict_match, get_model_accuracy

router = APIRouter(prefix="/api", tags=["predictions"])


@router.get("/predictions/custom")
def custom_prediction(
    p1: int = Query(..., description="Player 1 ID"),
    p2: int = Query(..., description="Player 2 ID"),
    surface: str = Query("Hard", description="Hard/Clay/Grass"),
    best_of: int = Query(3, description="3 or 5"),
    db: Session = Depends(get_db),
):
    return predict_match(db, p1, p2, surface, best_of)


@router.get("/predictions/upcoming")
def upcoming_predictions(db: Session = Depends(get_db)):
    """Return recent predictions (placeholder - in production this would use a schedule)."""
    from sqlalchemy import desc
    from app.database.models import Prediction
    preds = db.query(Prediction).order_by(desc(Prediction.created_at)).limit(20).all()

    results = []
    for p in preds:
        results.append({
            "id": p.id,
            "player1": {"id": p.player1_id, "name": p.player1.name if p.player1 else str(p.player1_id)},
            "player2": {"id": p.player2_id, "name": p.player2.name if p.player2 else str(p.player2_id)},
            "surface": p.surface,
            "best_of": p.best_of,
            "prob_player1": p.prob_player1,
            "prob_player2": p.prob_player2,
            "predicted_winner_id": p.predicted_winner_id,
            "correct": p.correct,
            "created_at": str(p.created_at),
        })
    return results


@router.get("/model/accuracy")
def model_accuracy(db: Session = Depends(get_db)):
    return get_model_accuracy(db)
