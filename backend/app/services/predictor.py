import logging

from sqlalchemy.orm import Session

from app.database.models import Player, Prediction
from app.models.elo import get_elo_system
from app.models.xgboost_model import get_model
from app.models.monte_carlo import simulate_match
from app.services.feature_engine import FeatureEngine

logger = logging.getLogger(__name__)


def predict_match(
    db: Session,
    p1_id: int,
    p2_id: int,
    surface: str = "Hard",
    best_of: int = 3,
    level: str = "A",
    save: bool = True,
) -> dict:
    elo = get_elo_system()
    model = get_model()
    fe = FeatureEngine(elo)

    # Build features
    features = fe.compute_live_features(p1_id, p2_id, surface, best_of, level)

    # Enrich with player DB data
    p1 = db.get(Player, p1_id)
    p2 = db.get(Player, p2_id)
    if p1:
        features["p1_height"] = p1.height or 185
        features["p1_hand_R"] = 1 if p1.hand == "R" else 0
        if p1.birth_date:
            from datetime import date
            features["p1_age"] = round((date.today() - p1.birth_date).days / 365.25, 1)
    if p2:
        features["p2_height"] = p2.height or 185
        features["p2_hand_R"] = 1 if p2.hand == "R" else 0
        if p2.birth_date:
            from datetime import date
            features["p2_age"] = round((date.today() - p2.birth_date).days / 365.25, 1)

    # Get latest rankings from DB
    from sqlalchemy import desc
    from app.database.models import Ranking
    r1 = db.query(Ranking).filter(Ranking.player_id == p1_id).order_by(desc(Ranking.ranking_date)).first()
    r2 = db.query(Ranking).filter(Ranking.player_id == p2_id).order_by(desc(Ranking.ranking_date)).first()
    features["p1_rank"] = r1.rank if r1 else 500
    features["p2_rank"] = r2.rank if r2 else 500
    features["rank_diff"] = features["p2_rank"] - features["p1_rank"]

    # XGBoost prediction
    prob_p1 = model.predict(features)
    prob_p2 = 1.0 - prob_p1

    # Monte Carlo simulation for score distribution
    p1_serve_pct = max(0.55, min(0.75, features.get("p1_srv_won", 0.63)))
    p2_serve_pct = max(0.55, min(0.75, features.get("p2_srv_won", 0.63)))
    mc_result = simulate_match(p1_serve_pct, p2_serve_pct, best_of, n_sims=5000)

    # Most likely score
    most_likely_score = max(mc_result["score_distribution"], key=mc_result["score_distribution"].get)

    # Confidence
    max_prob = max(prob_p1, prob_p2)
    if max_prob > 0.70:
        confidence = "High"
    elif max_prob > 0.55:
        confidence = "Medium"
    else:
        confidence = "Low"

    predicted_winner_id = p1_id if prob_p1 >= 0.5 else p2_id

    result = {
        "player1": {
            "id": p1_id,
            "name": p1.name if p1 else str(p1_id),
            "nationality": p1.nationality if p1 else None,
            "rank": features["p1_rank"],
            "elo": features["p1_elo"],
        },
        "player2": {
            "id": p2_id,
            "name": p2.name if p2 else str(p2_id),
            "nationality": p2.nationality if p2 else None,
            "rank": features["p2_rank"],
            "elo": features["p2_elo"],
        },
        "surface": surface,
        "best_of": best_of,
        "prob_player1": round(prob_p1, 4),
        "prob_player2": round(prob_p2, 4),
        "predicted_winner_id": predicted_winner_id,
        "confidence": confidence,
        "most_likely_score": most_likely_score,
        "score_distribution": mc_result["score_distribution"],
        "expected_total_games": mc_result["expected_total_games"],
    }

    # Save prediction to DB
    if save:
        pred = Prediction(
            player1_id=p1_id,
            player2_id=p2_id,
            surface=surface,
            best_of=best_of,
            prob_player1=prob_p1,
            prob_player2=prob_p2,
            predicted_winner_id=predicted_winner_id,
        )
        db.add(pred)
        db.commit()
        result["prediction_id"] = pred.id

    return result


def get_model_accuracy(db: Session) -> dict:
    model = get_model()
    predictions = (
        db.query(Prediction)
        .filter(Prediction.actual_winner_id.isnot(None))
        .order_by(Prediction.created_at)
        .all()
    )

    if not predictions:
        return {
            "total_predictions": 0,
            "correct": 0,
            "accuracy": 0,
            "model_metrics": model.metrics,
            "feature_importance": dict(list(model.feature_importance.items())[:15]),
        }

    correct = sum(1 for p in predictions if p.correct)
    return {
        "total_predictions": len(predictions),
        "correct": correct,
        "accuracy": round(correct / len(predictions), 4) if predictions else 0,
        "model_metrics": model.metrics,
        "feature_importance": dict(list(model.feature_importance.items())[:15]),
    }
