from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Tournament

router = APIRouter(prefix="/api", tags=["tournaments"])


@router.get("/tournaments")
def list_tournaments(
    surface: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Tournament)
    if surface:
        q = q.filter(Tournament.surface == surface)
    tournaments = q.order_by(Tournament.name).all()
    return [
        {
            "id": t.id,
            "tourney_id": t.tourney_id,
            "name": t.name,
            "surface": t.surface,
            "level": t.level,
            "draw_size": t.draw_size,
        }
        for t in tournaments
    ]
