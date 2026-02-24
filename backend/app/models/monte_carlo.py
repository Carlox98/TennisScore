import logging
from collections import Counter

import numpy as np

from app.config import MONTE_CARLO_SIMS

logger = logging.getLogger(__name__)


def simulate_game(p_server: float, rng: np.random.Generator) -> int:
    """Simulate a single game. Returns 1 if server wins, 0 otherwise."""
    points_server = 0
    points_returner = 0
    while True:
        if rng.random() < p_server:
            points_server += 1
        else:
            points_returner += 1
        # Check win conditions
        if points_server >= 4 and points_server - points_returner >= 2:
            return 1
        if points_returner >= 4 and points_returner - points_server >= 2:
            return 0
        # Deuce shortcut — at 3-3 or beyond, keep playing
        # (already handled by the while loop)


def simulate_tiebreak(p1_serve: float, p2_serve: float, rng: np.random.Generator) -> int:
    """Simulate a tiebreak. Returns 1 if p1 wins, 0 if p2 wins."""
    p1_pts = 0
    p2_pts = 0
    total = 0
    # p1 serves first point
    server_is_p1 = True
    while True:
        p_serve = p1_serve if server_is_p1 else p2_serve
        if rng.random() < p_serve:
            if server_is_p1:
                p1_pts += 1
            else:
                p2_pts += 1
        else:
            if server_is_p1:
                p2_pts += 1
            else:
                p1_pts += 1
        total += 1
        # Check win
        if p1_pts >= 7 and p1_pts - p2_pts >= 2:
            return 1
        if p2_pts >= 7 and p2_pts - p1_pts >= 2:
            return 0
        # Service change: after 1st point, then every 2 points
        if total == 1 or (total > 1 and (total - 1) % 2 == 0):
            server_is_p1 = not server_is_p1


def simulate_set(p1_serve: float, p2_serve: float, rng: np.random.Generator) -> tuple[int, int]:
    """Simulate a set. Returns (p1_games, p2_games)."""
    p1_games = 0
    p2_games = 0
    p1_serving = True  # p1 starts serving
    while True:
        if p1_games == 6 and p2_games == 6:
            # Tiebreak
            winner = simulate_tiebreak(p1_serve, p2_serve, rng)
            if winner == 1:
                return (7, 6)
            else:
                return (6, 7)

        p_serve = p1_serve if p1_serving else p2_serve
        game_won = simulate_game(p_serve, rng)
        if p1_serving:
            if game_won:
                p1_games += 1
            else:
                p2_games += 1
        else:
            if game_won:
                p2_games += 1
            else:
                p1_games += 1

        # Check set win (need 6 games with 2-game lead, or 7-5)
        if p1_games >= 6 and p1_games - p2_games >= 2:
            return (p1_games, p2_games)
        if p2_games >= 6 and p2_games - p1_games >= 2:
            return (p1_games, p2_games)

        p1_serving = not p1_serving


def simulate_match(
    p1_serve_pct: float,
    p2_serve_pct: float,
    best_of: int = 3,
    n_sims: int = MONTE_CARLO_SIMS,
) -> dict:
    """
    Monte Carlo match simulation.

    Args:
        p1_serve_pct: P(point won on serve) for player 1
        p2_serve_pct: P(point won on serve) for player 2
        best_of: 3 or 5 sets
        n_sims: number of simulations

    Returns:
        dict with score distributions, win probability, expected games
    """
    rng = np.random.default_rng(42)
    sets_to_win = 2 if best_of == 3 else 3

    p1_wins = 0
    score_counts: Counter = Counter()
    total_games_list = []

    for _ in range(n_sims):
        p1_sets = 0
        p2_sets = 0
        set_scores = []
        total_games = 0

        while p1_sets < sets_to_win and p2_sets < sets_to_win:
            g1, g2 = simulate_set(p1_serve_pct, p2_serve_pct, rng)
            total_games += g1 + g2
            if g1 > g2:
                p1_sets += 1
            else:
                p2_sets += 1
            set_scores.append((g1, g2))

        if p1_sets > p2_sets:
            p1_wins += 1

        score_key = f"{p1_sets}-{p2_sets}"
        score_counts[score_key] += 1
        total_games_list.append(total_games)

    # Build results
    p1_win_prob = p1_wins / n_sims
    score_distribution = {
        k: round(v / n_sims, 4) for k, v in sorted(score_counts.items())
    }
    avg_games = float(np.mean(total_games_list))

    return {
        "p1_win_prob": round(p1_win_prob, 4),
        "p2_win_prob": round(1 - p1_win_prob, 4),
        "score_distribution": score_distribution,
        "expected_total_games": round(avg_games, 1),
        "simulations": n_sims,
    }
