import logging
from datetime import date, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd
from sqlalchemy import and_, or_, asc
from sqlalchemy.orm import Session

from app.database.models import Match, Player, Tournament
from app.models.elo import EloSystem, ELO_INITIAL

logger = logging.getLogger(__name__)

SURFACE_MAP = {"Hard": 0, "Clay": 1, "Grass": 2, "Carpet": 3}
LEVEL_MAP = {"G": 4, "F": 3, "M": 2, "A": 1, "D": 0}
ROUND_MAP = {"F": 7, "SF": 6, "QF": 5, "R16": 4, "R32": 3, "R64": 2, "R128": 1, "RR": 3}


def _safe_div(a, b) -> float:
    if b is None or b == 0 or a is None:
        return 0.0
    return a / b


class PlayerMatchStats:
    """Rolling stats for a player computed from recent matches."""

    def __init__(self):
        self.matches: list[dict] = []

    def add_match(self, match: Match, is_winner: bool):
        prefix = "w_" if is_winner else "l_"
        opp_prefix = "l_" if is_winner else "w_"
        self.matches.append({
            "date": match.tourney_date,
            "surface": match.surface,
            "won": is_winner,
            "ace": getattr(match, f"{prefix}ace"),
            "df": getattr(match, f"{prefix}df"),
            "svpt": getattr(match, f"{prefix}svpt"),
            "1stIn": getattr(match, f"{prefix}1stIn"),
            "1stWon": getattr(match, f"{prefix}1stWon"),
            "2ndWon": getattr(match, f"{prefix}2ndWon"),
            "SvGms": getattr(match, f"{prefix}SvGms"),
            "bpSaved": getattr(match, f"{prefix}bpSaved"),
            "bpFaced": getattr(match, f"{prefix}bpFaced"),
            "opp_svpt": getattr(match, f"{opp_prefix}svpt"),
            "opp_1stIn": getattr(match, f"{opp_prefix}1stIn"),
            "opp_1stWon": getattr(match, f"{opp_prefix}1stWon"),
            "opp_2ndWon": getattr(match, f"{opp_prefix}2ndWon"),
            "opp_bpSaved": getattr(match, f"{opp_prefix}bpSaved"),
            "opp_bpFaced": getattr(match, f"{opp_prefix}bpFaced"),
            "opponent_id": match.loser_id if is_winner else match.winner_id,
        })

    def _recent(self, n: int, surface: str | None = None) -> list[dict]:
        filtered = self.matches
        if surface:
            filtered = [m for m in filtered if m["surface"] == surface]
        return filtered[-n:]

    def win_rate(self, n: int, surface: str | None = None) -> float:
        recent = self._recent(n, surface)
        if not recent:
            return 0.5
        return sum(1 for m in recent if m["won"]) / len(recent)

    def avg_stat(self, stat: str, n: int) -> float:
        recent = self._recent(n)
        vals = [m[stat] for m in recent if m[stat] is not None]
        return np.mean(vals) if vals else 0.0

    def first_serve_pct(self, n: int) -> float:
        recent = self._recent(n)
        total_svpt = sum(m["svpt"] for m in recent if m["svpt"])
        total_1stIn = sum(m["1stIn"] for m in recent if m["1stIn"])
        return _safe_div(total_1stIn, total_svpt)

    def serve_points_won_pct(self, n: int) -> float:
        recent = self._recent(n)
        total_svpt = sum(m["svpt"] for m in recent if m["svpt"])
        total_won = sum((m["1stWon"] or 0) + (m["2ndWon"] or 0) for m in recent)
        return _safe_div(total_won, total_svpt)

    def return_points_won_pct(self, n: int) -> float:
        recent = self._recent(n)
        opp_svpt = sum(m["opp_svpt"] for m in recent if m["opp_svpt"])
        opp_won = sum((m["opp_1stWon"] or 0) + (m["opp_2ndWon"] or 0) for m in recent)
        return _safe_div(opp_svpt - opp_won, opp_svpt)

    def bp_saved_pct(self, n: int) -> float:
        recent = self._recent(n)
        faced = sum(m["bpFaced"] for m in recent if m["bpFaced"])
        saved = sum(m["bpSaved"] for m in recent if m["bpSaved"])
        return _safe_div(saved, faced)

    def bp_converted_pct(self, n: int) -> float:
        recent = self._recent(n)
        opp_faced = sum(m["opp_bpFaced"] for m in recent if m["opp_bpFaced"])
        opp_saved = sum(m["opp_bpSaved"] for m in recent if m["opp_bpSaved"])
        if not opp_faced:
            return 0.0
        return _safe_div(opp_faced - opp_saved, opp_faced)

    def matches_in_period(self, ref_date: date, days: int) -> int:
        if ref_date is None:
            return 0
        cutoff = ref_date - timedelta(days=days)
        return sum(1 for m in self.matches if m["date"] and m["date"] >= cutoff)

    def h2h_win_rate(self, opponent_id: int, surface: str | None = None) -> float:
        h2h = [m for m in self.matches if m["opponent_id"] == opponent_id]
        if surface:
            h2h = [m for m in h2h if m["surface"] == surface]
        if not h2h:
            return 0.5
        return sum(1 for m in h2h if m["won"]) / len(h2h)


class FeatureEngine:
    def __init__(self, elo_system: EloSystem):
        self.elo = elo_system
        self.player_stats: dict[int, PlayerMatchStats] = defaultdict(PlayerMatchStats)

    def build_features_from_db(self, db: Session) -> pd.DataFrame:
        logger.info("Building features from all matches...")
        matches = (
            db.query(Match)
            .join(Match.tournament)
            .order_by(asc(Match.tourney_date), asc(Match.match_num))
            .all()
        )

        # Reset Elo for chronological computation
        elo = EloSystem()
        rows = []

        for m in matches:
            wid = m.winner_id
            lid = m.loser_id
            surface = m.surface
            level = m.tournament.level if m.tournament else "A"
            match_date = m.tourney_date

            w_stats = self.player_stats[wid]
            l_stats = self.player_stats[lid]

            # Get current Elo before update
            w_elo = elo.get_elo(wid)
            l_elo = elo.get_elo(lid)
            w_surf_elo = elo.get_surface_elo(wid, surface) if surface else ELO_INITIAL
            l_surf_elo = elo.get_surface_elo(lid, surface) if surface else ELO_INITIAL

            # Get player info
            w_player = db.get(Player, wid)
            l_player = db.get(Player, lid)

            w_age = _player_age(w_player, match_date)
            l_age = _player_age(l_player, match_date)

            features = {
                "match_id": m.id,
                "target": 1,  # p1 (winner) wins — we'll randomize later

                # Elo
                "p1_elo": w_elo,
                "p2_elo": l_elo,
                "elo_diff": w_elo - l_elo,
                "p1_surf_elo": w_surf_elo,
                "p2_surf_elo": l_surf_elo,
                "surf_elo_diff": w_surf_elo - l_surf_elo,

                # Ranking
                "p1_rank": m.winner_rank or 500,
                "p2_rank": m.loser_rank or 500,
                "rank_diff": (m.loser_rank or 500) - (m.winner_rank or 500),

                # Win rates
                "p1_win10": w_stats.win_rate(10),
                "p2_win10": l_stats.win_rate(10),
                "p1_win20": w_stats.win_rate(20),
                "p2_win20": l_stats.win_rate(20),
                "p1_win10_surf": w_stats.win_rate(10, surface),
                "p2_win10_surf": l_stats.win_rate(10, surface),

                # Serve stats
                "p1_1st_pct": w_stats.first_serve_pct(20),
                "p2_1st_pct": l_stats.first_serve_pct(20),
                "p1_srv_won": w_stats.serve_points_won_pct(20),
                "p2_srv_won": l_stats.serve_points_won_pct(20),
                "p1_ret_won": w_stats.return_points_won_pct(20),
                "p2_ret_won": l_stats.return_points_won_pct(20),

                # Ace/DF per match
                "p1_ace_avg": w_stats.avg_stat("ace", 20),
                "p2_ace_avg": l_stats.avg_stat("ace", 20),
                "p1_df_avg": w_stats.avg_stat("df", 20),
                "p2_df_avg": l_stats.avg_stat("df", 20),

                # Break points
                "p1_bp_saved": w_stats.bp_saved_pct(20),
                "p2_bp_saved": l_stats.bp_saved_pct(20),
                "p1_bp_conv": w_stats.bp_converted_pct(20),
                "p2_bp_conv": l_stats.bp_converted_pct(20),

                # H2H
                "p1_h2h": w_stats.h2h_win_rate(lid),
                "p2_h2h": l_stats.h2h_win_rate(wid),
                "p1_h2h_surf": w_stats.h2h_win_rate(lid, surface),
                "p2_h2h_surf": l_stats.h2h_win_rate(wid, surface),

                # Fatigue
                "p1_matches_7d": w_stats.matches_in_period(match_date, 7),
                "p2_matches_7d": l_stats.matches_in_period(match_date, 7),
                "p1_matches_14d": w_stats.matches_in_period(match_date, 14),
                "p2_matches_14d": l_stats.matches_in_period(match_date, 14),
                "p1_matches_30d": w_stats.matches_in_period(match_date, 30),
                "p2_matches_30d": l_stats.matches_in_period(match_date, 30),

                # Player attributes
                "p1_age": w_age,
                "p2_age": l_age,
                "p1_height": w_player.height or 185 if w_player else 185,
                "p2_height": l_player.height or 185 if l_player else 185,
                "p1_hand_R": 1 if (w_player and w_player.hand == "R") else 0,
                "p2_hand_R": 1 if (l_player and l_player.hand == "R") else 0,

                # Match context
                "surface_hard": 1 if surface == "Hard" else 0,
                "surface_clay": 1 if surface == "Clay" else 0,
                "surface_grass": 1 if surface == "Grass" else 0,
                "level_ord": LEVEL_MAP.get(level, 1),
                "round_ord": ROUND_MAP.get(m.round, 3),
                "best_of": m.best_of or 3,
            }
            rows.append(features)

            # Update Elo AFTER recording features
            elo.update(wid, lid, surface, level)

            # Record match in player stats
            w_stats.add_match(m, is_winner=True)
            l_stats.add_match(m, is_winner=False)

        df = pd.DataFrame(rows)
        logger.info(f"Built {len(df)} feature rows")

        # Randomize p1/p2 assignment to avoid bias
        df = _randomize_sides(df)
        return df

    def compute_live_features(
        self, p1_id: int, p2_id: int, surface: str, best_of: int, level: str = "A"
    ) -> dict:
        p1 = self.player_stats.get(p1_id, PlayerMatchStats())
        p2 = self.player_stats.get(p2_id, PlayerMatchStats())

        p1_elo = self.elo.get_elo(p1_id)
        p2_elo = self.elo.get_elo(p2_id)
        p1_surf = self.elo.get_surface_elo(p1_id, surface)
        p2_surf = self.elo.get_surface_elo(p2_id, surface)

        today = date.today()

        return {
            "p1_elo": p1_elo,
            "p2_elo": p2_elo,
            "elo_diff": p1_elo - p2_elo,
            "p1_surf_elo": p1_surf,
            "p2_surf_elo": p2_surf,
            "surf_elo_diff": p1_surf - p2_surf,
            "p1_rank": 500,
            "p2_rank": 500,
            "rank_diff": 0,
            "p1_win10": p1.win_rate(10),
            "p2_win10": p2.win_rate(10),
            "p1_win20": p1.win_rate(20),
            "p2_win20": p2.win_rate(20),
            "p1_win10_surf": p1.win_rate(10, surface),
            "p2_win10_surf": p2.win_rate(10, surface),
            "p1_1st_pct": p1.first_serve_pct(20),
            "p2_1st_pct": p2.first_serve_pct(20),
            "p1_srv_won": p1.serve_points_won_pct(20),
            "p2_srv_won": p2.serve_points_won_pct(20),
            "p1_ret_won": p1.return_points_won_pct(20),
            "p2_ret_won": p2.return_points_won_pct(20),
            "p1_ace_avg": p1.avg_stat("ace", 20),
            "p2_ace_avg": p2.avg_stat("ace", 20),
            "p1_df_avg": p1.avg_stat("df", 20),
            "p2_df_avg": p2.avg_stat("df", 20),
            "p1_bp_saved": p1.bp_saved_pct(20),
            "p2_bp_saved": p2.bp_saved_pct(20),
            "p1_bp_conv": p1.bp_converted_pct(20),
            "p2_bp_conv": p2.bp_converted_pct(20),
            "p1_h2h": p1.h2h_win_rate(p2_id),
            "p2_h2h": p2.h2h_win_rate(p1_id),
            "p1_h2h_surf": p1.h2h_win_rate(p2_id, surface),
            "p2_h2h_surf": p2.h2h_win_rate(p1_id, surface),
            "p1_matches_7d": p1.matches_in_period(today, 7),
            "p2_matches_7d": p2.matches_in_period(today, 7),
            "p1_matches_14d": p1.matches_in_period(today, 14),
            "p2_matches_14d": p2.matches_in_period(today, 14),
            "p1_matches_30d": p1.matches_in_period(today, 30),
            "p2_matches_30d": p2.matches_in_period(today, 30),
            "p1_age": 27,
            "p2_age": 27,
            "p1_height": 185,
            "p2_height": 185,
            "p1_hand_R": 1,
            "p2_hand_R": 1,
            "surface_hard": 1 if surface == "Hard" else 0,
            "surface_clay": 1 if surface == "Clay" else 0,
            "surface_grass": 1 if surface == "Grass" else 0,
            "level_ord": LEVEL_MAP.get(level, 1),
            "round_ord": 3,
            "best_of": best_of,
        }


def _player_age(player: Player | None, match_date: date | None) -> float:
    if not player or not player.birth_date or not match_date:
        return 27.0
    delta = match_date - player.birth_date
    return round(delta.days / 365.25, 1)


def _randomize_sides(df: pd.DataFrame) -> pd.DataFrame:
    """Randomly swap p1/p2 in half the rows to remove winner-always-p1 bias."""
    np.random.seed(42)
    swap_mask = np.random.random(len(df)) < 0.5

    p1_cols = [c for c in df.columns if c.startswith("p1_")]
    p2_cols = [c for c in df.columns if c.startswith("p2_")]

    for p1c, p2c in zip(p1_cols, p2_cols):
        df.loc[swap_mask, [p1c, p2c]] = df.loc[swap_mask, [p2c, p1c]].values

    # Flip diff columns
    for col in ["elo_diff", "surf_elo_diff", "rank_diff"]:
        if col in df.columns:
            df.loc[swap_mask, col] = -df.loc[swap_mask, col]

    # Flip target
    df.loc[swap_mask, "target"] = 0

    return df
