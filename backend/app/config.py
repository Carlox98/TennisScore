from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "trained_models"
DATABASE_URL = f"sqlite:///{BASE_DIR / 'tennis.db'}"

DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

SACKMANN_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"
MATCH_YEARS = list(range(2015, 2026))

ELO_K = 32
ELO_K_SURFACE = 40
ELO_INITIAL = 1500

MONTE_CARLO_SIMS = 10_000
