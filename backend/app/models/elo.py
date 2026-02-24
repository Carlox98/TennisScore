import logging
from collections import defaultdict

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.config import ELO_K, ELO_K_SURFACE, ELO_INITIAL
from app.database.models import Match, Player

logger = logging.getLogger(__name__)

# Tournament level multipliers for K-factor
LEVEL_MULTIPLIER = {
    "G": 1.5,   # Grand Slam
    "F": 1.3,   # Tour Finals
    "M": 1.2,   # Masters 1000
    "A": 1.0,   # ATP 250/500
    "D": 0.8,   # Davis Cup
    "C": 0.6,   # Challengers
}


def expected_score(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


class EloSystem:
    def __init__(self):
        self.elo_overall: dict[int, float] = defaultdict(lambda: ELO_INITIAL)
        self.elo_surface: dict[str, dict[int, float]] = {
            "Hard": defaultdict(lambda: ELO_INITIAL),
            "Clay": defaultdict(lambda: ELO_INITIAL),
            "Grass": defaultdict(lambda: ELO_INITIAL),
            "Carpet": defaultdict(lambda: ELO_INITIAL),
        }
        self._history: list[dict] = []

    def get_elo(self, player_id: int) -> float:
        return self.elo_overall[player_id]

    def get_surface_elo(self, player_id: int, surface: str) -> float:
        if surface in self.elo_surface:
            return self.elo_surface[surface][player_id]
        return ELO_INITIAL

    def update(self, winner_id: int, loser_id: int, surface: str | None, level: str | None):
        # Overall Elo
        e_w = expected_score(self.elo_overall[winner_id], self.elo_overall[loser_id])
        k = ELO_K * LEVEL_MULTIPLIER.get(level or "A", 1.0)
        self.elo_overall[winner_id] += k * (1.0 - e_w)
        self.elo_overall[loser_id] += k * (0.0 - (1.0 - e_w))

        # Surface Elo
        if surface and surface in self.elo_surface:
            surf_dict = self.elo_surface[surface]
            e_ws = expected_score(surf_dict[winner_id], surf_dict[loser_id])
            ks = ELO_K_SURFACE * LEVEL_MULTIPLIER.get(level or "A", 1.0)
            surf_dict[winner_id] += ks * (1.0 - e_ws)
            surf_dict[loser_id] += ks * (0.0 - (1.0 - e_ws))

    def compute_all(self, db: Session) -> "EloSystem":
        logger.info("Computing Elo ratings for all matches...")
        matches = (
            db.query(Match)
            .join(Match.tournament)
            .order_by(asc(Match.tourney_date), asc(Match.match_num))
            .all()
        )
        for m in matches:
            level = m.tournament.level if m.tournament else None
            self.update(m.winner_id, m.loser_id, m.surface, level)

            self._history.append({
                "match_id": m.id,
                "winner_id": m.winner_id,
                "loser_id": m.loser_id,
                "winner_elo_after": self.elo_overall[m.winner_id],
                "loser_elo_after": self.elo_overall[m.loser_id],
            })

        logger.info(f"Elo computed for {len(matches)} matches, {len(self.elo_overall)} players")
        return self

    def save_to_db(self, db: Session):
        logger.info("Saving Elo ratings to database...")
        players = db.query(Player).all()
        count = 0
        for p in players:
            p.elo_overall = round(self.elo_overall.get(p.id, ELO_INITIAL), 1)
            p.elo_hard = round(self.elo_surface["Hard"].get(p.id, ELO_INITIAL), 1)
            p.elo_clay = round(self.elo_surface["Clay"].get(p.id, ELO_INITIAL), 1)
            p.elo_grass = round(self.elo_surface["Grass"].get(p.id, ELO_INITIAL), 1)
            count += 1
        db.commit()
        logger.info(f"Saved Elo for {count} players")

    def get_snapshot_before_match(self, match_id: int) -> dict | None:
        for i, h in enumerate(self._history):
            if h["match_id"] == match_id:
                if i == 0:
                    return None
                return self._history[i - 1]
        return None


# Module-level singleton for access from other modules
_elo_instance: EloSystem | None = None


def get_elo_system() -> EloSystem:
    global _elo_instance
    if _elo_instance is None:
        _elo_instance = EloSystem()
    return _elo_instance


def init_elo_system(db: Session) -> EloSystem:
    global _elo_instance
    _elo_instance = EloSystem()
    _elo_instance.compute_all(db)
    _elo_instance.save_to_db(db)
    return _elo_instance
