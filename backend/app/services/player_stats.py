import logging
from datetime import date, timedelta

from sqlalchemy import or_, desc, func
from sqlalchemy.orm import Session

from app.database.models import Player, Match, Ranking
from app.models.elo import get_elo_system

logger = logging.getLogger(__name__)


def get_player_profile(db: Session, player_id: int) -> dict | None:
    player = db.get(Player, player_id)
    if not player:
        return None

    # Latest ranking
    latest_rank = (
        db.query(Ranking)
        .filter(Ranking.player_id == player_id)
        .order_by(desc(Ranking.ranking_date))
        .first()
    )

    # Win/loss record
    wins = db.query(func.count()).filter(Match.winner_id == player_id).scalar()
    losses = db.query(func.count()).filter(Match.loser_id == player_id).scalar()

    # Surface records
    surface_records = {}
    for surface in ["Hard", "Clay", "Grass"]:
        sw = db.query(func.count()).filter(Match.winner_id == player_id, Match.surface == surface).scalar()
        sl = db.query(func.count()).filter(Match.loser_id == player_id, Match.surface == surface).scalar()
        total = sw + sl
        surface_records[surface.lower()] = {
            "wins": sw, "losses": sl,
            "win_rate": round(sw / total, 3) if total > 0 else 0,
        }

    # Recent form (last 10 matches)
    recent = get_recent_matches(db, player_id, 10)

    age = None
    if player.birth_date:
        delta = date.today() - player.birth_date
        age = round(delta.days / 365.25, 1)

    # Compute radar stats from recent matches
    radar = _compute_radar(db, player_id)

    # Playing style badge
    style = _classify_style(radar)

    return {
        "id": player.id,
        "name": player.name,
        "nationality": player.nationality,
        "hand": player.hand,
        "height": player.height,
        "age": age,
        "birth_date": str(player.birth_date) if player.birth_date else None,
        "rank": latest_rank.rank if latest_rank else None,
        "rank_points": latest_rank.points if latest_rank else None,
        "elo_overall": player.elo_overall,
        "elo_hard": player.elo_hard,
        "elo_clay": player.elo_clay,
        "elo_grass": player.elo_grass,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / (wins + losses), 3) if (wins + losses) > 0 else 0,
        "surface_records": surface_records,
        "recent_matches": recent,
        "radar": radar,
        "style": style,
    }


def get_recent_matches(db: Session, player_id: int, limit: int = 10) -> list[dict]:
    matches = (
        db.query(Match)
        .filter(or_(Match.winner_id == player_id, Match.loser_id == player_id))
        .order_by(desc(Match.tourney_date))
        .limit(limit)
        .all()
    )
    results = []
    for m in matches:
        is_winner = m.winner_id == player_id
        opp_id = m.loser_id if is_winner else m.winner_id
        opponent = db.get(Player, opp_id)
        results.append({
            "match_id": m.id,
            "date": str(m.tourney_date) if m.tourney_date else None,
            "surface": m.surface,
            "round": m.round,
            "won": is_winner,
            "score": m.score,
            "opponent": {
                "id": opp_id,
                "name": opponent.name if opponent else f"Player {opp_id}",
            },
            "aces": m.w_ace if is_winner else m.l_ace,
            "double_faults": m.w_df if is_winner else m.l_df,
        })
    return results


def get_h2h(db: Session, p1_id: int, p2_id: int) -> dict:
    p1 = db.get(Player, p1_id)
    p2 = db.get(Player, p2_id)

    matches = (
        db.query(Match)
        .filter(
            or_(
                (Match.winner_id == p1_id) & (Match.loser_id == p2_id),
                (Match.winner_id == p2_id) & (Match.loser_id == p1_id),
            )
        )
        .order_by(desc(Match.tourney_date))
        .all()
    )

    p1_wins = sum(1 for m in matches if m.winner_id == p1_id)
    p2_wins = sum(1 for m in matches if m.winner_id == p2_id)

    history = []
    for m in matches:
        history.append({
            "date": str(m.tourney_date) if m.tourney_date else None,
            "surface": m.surface,
            "round": m.round,
            "score": m.score,
            "winner_id": m.winner_id,
        })

    # H2H per surface
    surface_h2h = {}
    for surface in ["Hard", "Clay", "Grass"]:
        s_matches = [m for m in matches if m.surface == surface]
        s_p1 = sum(1 for m in s_matches if m.winner_id == p1_id)
        s_p2 = sum(1 for m in s_matches if m.winner_id == p2_id)
        surface_h2h[surface.lower()] = {"p1_wins": s_p1, "p2_wins": s_p2}

    return {
        "player1": {"id": p1_id, "name": p1.name if p1 else str(p1_id)},
        "player2": {"id": p2_id, "name": p2.name if p2 else str(p2_id)},
        "p1_wins": p1_wins,
        "p2_wins": p2_wins,
        "total_matches": len(matches),
        "surface_h2h": surface_h2h,
        "history": history,
    }


def search_players(db: Session, query: str, limit: int = 20) -> list[dict]:
    from thefuzz import fuzz

    players = db.query(Player).all()
    scored = []
    q_lower = query.lower()
    for p in players:
        name_lower = p.name.lower()
        if q_lower in name_lower:
            score = 100
        else:
            score = fuzz.partial_ratio(q_lower, name_lower)
        if score >= 60:
            scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    return [
        {
            "id": p.id,
            "name": p.name,
            "nationality": p.nationality,
            "elo": p.elo_overall,
        }
        for _, p in scored[:limit]
    ]


def get_rankings(db: Session, limit: int = 100) -> list[dict]:
    # Get latest ranking date
    latest_date = db.query(func.max(Ranking.ranking_date)).scalar()
    if not latest_date:
        return []

    rankings = (
        db.query(Ranking)
        .filter(Ranking.ranking_date == latest_date)
        .order_by(Ranking.rank)
        .limit(limit)
        .all()
    )

    results = []
    for r in rankings:
        player = db.get(Player, r.player_id)
        results.append({
            "rank": r.rank,
            "points": r.points,
            "player": {
                "id": r.player_id,
                "name": player.name if player else str(r.player_id),
                "nationality": player.nationality if player else None,
                "elo": player.elo_overall if player else 1500,
            }
        })
    return results


def _compute_radar(db: Session, player_id: int) -> dict:
    """Compute 6 radar stats from last 20 matches, each scaled 0-100."""
    matches = (
        db.query(Match)
        .filter(or_(Match.winner_id == player_id, Match.loser_id == player_id))
        .order_by(desc(Match.tourney_date))
        .limit(20)
        .all()
    )
    if not matches:
        return {"serve": 50, "return": 50, "power": 50, "consistency": 50, "clutch": 50, "form": 50}

    serve_pts, ret_pts, aces, dfs, bp_saved, bp_faced = 0, 0, 0, 0, 0, 0
    total_svpt, total_opp_svpt = 0, 0
    wins = 0
    recent_wins = 0

    for i, m in enumerate(matches):
        is_w = m.winner_id == player_id
        prefix = "w_" if is_w else "l_"
        opp_prefix = "l_" if is_w else "w_"

        svpt = getattr(m, f"{prefix}svpt") or 0
        won1 = getattr(m, f"{prefix}1stWon") or 0
        won2 = getattr(m, f"{prefix}2ndWon") or 0
        opp_svpt = getattr(m, f"{opp_prefix}svpt") or 0
        opp_won1 = getattr(m, f"{opp_prefix}1stWon") or 0
        opp_won2 = getattr(m, f"{opp_prefix}2ndWon") or 0

        serve_pts += won1 + won2
        total_svpt += svpt
        ret_pts += (opp_svpt - opp_won1 - opp_won2) if opp_svpt else 0
        total_opp_svpt += opp_svpt
        aces += getattr(m, f"{prefix}ace") or 0
        dfs += getattr(m, f"{prefix}df") or 0
        bp_s = getattr(m, f"{prefix}bpSaved") or 0
        bp_f = getattr(m, f"{prefix}bpFaced") or 0
        bp_saved += bp_s
        bp_faced += bp_f
        if is_w:
            wins += 1
        if i < 5 and is_w:
            recent_wins += 1

    n = len(matches)
    serve_score = min(100, (serve_pts / total_svpt * 150)) if total_svpt else 50
    return_score = min(100, (ret_pts / total_opp_svpt * 200)) if total_opp_svpt else 50
    power_score = min(100, aces / n * 10) if n else 50
    consistency_score = max(0, 100 - (dfs / n * 15)) if n else 50
    clutch_score = min(100, (bp_saved / bp_faced * 100)) if bp_faced else 50
    form_score = min(100, recent_wins / min(5, n) * 100) if n else 50

    return {
        "serve": round(serve_score),
        "return": round(return_score),
        "power": round(power_score),
        "consistency": round(consistency_score),
        "clutch": round(clutch_score),
        "form": round(form_score),
    }


def _classify_style(radar: dict) -> str:
    if radar["power"] > 70 and radar["serve"] > 65:
        return "Serve & Volley"
    if radar["power"] > 60 and radar["serve"] > 55:
        return "Aggressive Baseliner"
    if radar["return"] > 60 and radar["consistency"] > 65:
        return "Counter-Puncher"
    return "All-Court"
