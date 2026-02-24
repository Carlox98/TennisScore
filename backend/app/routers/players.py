from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.player_stats import (
    get_player_profile,
    get_recent_matches,
    get_h2h,
    search_players,
    get_rankings,
)

router = APIRouter(prefix="/api", tags=["players"])


@router.get("/players/search")
def search(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    return search_players(db, q)


@router.get("/players/compare")
def compare_players(
    p1: int = Query(...),
    p2: int = Query(...),
    db: Session = Depends(get_db),
):
    return get_h2h(db, p1, p2)


@router.get("/players/{player_id}")
def player_profile(player_id: int, db: Session = Depends(get_db)):
    profile = get_player_profile(db, player_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Player not found")
    return profile


@router.get("/players/{player_id}/form")
def player_form(player_id: int, db: Session = Depends(get_db)):
    return get_recent_matches(db, player_id, limit=10)


@router.get("/rankings")
def rankings(limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    return get_rankings(db, limit)
