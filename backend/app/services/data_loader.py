import logging
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
from sqlalchemy.orm import Session

from app.config import SACKMANN_BASE, MATCH_YEARS, DATA_DIR
from app.database.db import engine, SessionLocal
from app.database.models import Player, Tournament, Match, Ranking

logger = logging.getLogger(__name__)


def download_file(url: str, dest: Path) -> bool:
    if dest.exists():
        logger.info(f"Already downloaded: {dest.name}")
        return True
    logger.info(f"Downloading {url} ...")
    try:
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        logger.info(f"Saved {dest.name} ({dest.stat().st_size / 1024:.0f} KB)")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def download_all_data():
    files = {}
    # Match files
    for year in MATCH_YEARS:
        fname = f"atp_matches_{year}.csv"
        url = f"{SACKMANN_BASE}/{fname}"
        dest = DATA_DIR / fname
        if download_file(url, dest):
            files[fname] = dest

    # Players file
    fname = "atp_players.csv"
    url = f"{SACKMANN_BASE}/{fname}"
    dest = DATA_DIR / fname
    if download_file(url, dest):
        files[fname] = dest

    # Rankings
    fname = "atp_rankings_current.csv"
    url = f"{SACKMANN_BASE}/{fname}"
    dest = DATA_DIR / fname
    if download_file(url, dest):
        files[fname] = dest

    return files


def _parse_date(val) -> datetime | None:
    if pd.isna(val):
        return None
    s = str(int(val)) if isinstance(val, float) else str(val)
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None


def _safe_int(val) -> int | None:
    if pd.isna(val):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def load_players(db: Session):
    path = DATA_DIR / "atp_players.csv"
    if not path.exists():
        logger.warning("atp_players.csv not found")
        return
    df = pd.read_csv(path, dtype=str)
    count = 0
    for _, row in df.iterrows():
        pid = _safe_int(row.get("player_id"))
        if pid is None:
            continue
        existing = db.get(Player, pid)
        if existing:
            continue
        dob = None
        dob_str = row.get("dob", "")
        if dob_str and dob_str != "nan" and len(str(dob_str)) == 8:
            try:
                dob = datetime.strptime(str(dob_str), "%Y%m%d").date()
            except Exception:
                pass
        h = _safe_int(row.get("height"))
        player = Player(
            id=pid,
            first_name=str(row.get("name_first", "")).strip(),
            last_name=str(row.get("name_last", "")).strip(),
            name=f"{row.get('name_first', '')} {row.get('name_last', '')}".strip(),
            nationality=str(row.get("ioc", "")).strip() or None,
            hand=str(row.get("hand", "")).strip() or None,
            height=h,
            birth_date=dob,
        )
        db.add(player)
        count += 1
        if count % 1000 == 0:
            db.flush()
    db.commit()
    logger.info(f"Loaded {count} players")


def load_matches(db: Session):
    all_frames = []
    for year in MATCH_YEARS:
        path = DATA_DIR / f"atp_matches_{year}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, dtype=str)
        all_frames.append(df)
    if not all_frames:
        logger.warning("No match CSV files found")
        return
    df = pd.concat(all_frames, ignore_index=True)
    logger.info(f"Total rows from CSVs: {len(df)}")

    # Load tournaments first
    tourney_df = df[["tourney_id", "tourney_name", "surface", "tourney_level", "draw_size"]].drop_duplicates(subset=["tourney_id"])
    t_count = 0
    for _, row in tourney_df.iterrows():
        tid = str(row["tourney_id"])
        existing = db.query(Tournament).filter_by(tourney_id=tid).first()
        if existing:
            continue
        t = Tournament(
            tourney_id=tid,
            name=str(row.get("tourney_name", "")),
            surface=str(row.get("surface", "")) or None,
            level=str(row.get("tourney_level", "")) or None,
            draw_size=_safe_int(row.get("draw_size")),
        )
        db.add(t)
        t_count += 1
    db.commit()
    logger.info(f"Loaded {t_count} tournaments")

    # Ensure all players from matches exist
    player_ids_in_db = {p.id for p in db.query(Player.id).all()}
    for col in ["winner_id", "loser_id"]:
        for pid_str in df[col].dropna().unique():
            pid = _safe_int(pid_str)
            if pid and pid not in player_ids_in_db:
                # Find name from match data
                row = df[df[col] == pid_str].iloc[0]
                name_col = "winner_name" if col == "winner_id" else "loser_name"
                name = str(row.get(name_col, f"Player {pid}"))
                parts = name.split(" ", 1)
                db.add(Player(
                    id=pid,
                    first_name=parts[0] if parts else "",
                    last_name=parts[1] if len(parts) > 1 else "",
                    name=name,
                ))
                player_ids_in_db.add(pid)
    db.commit()

    # Load matches
    existing_count = db.query(Match).count()
    if existing_count > 0:
        logger.info(f"Matches already loaded ({existing_count}), skipping")
        return

    m_count = 0
    batch = []
    for _, row in df.iterrows():
        wid = _safe_int(row.get("winner_id"))
        lid = _safe_int(row.get("loser_id"))
        if not wid or not lid:
            continue
        m = Match(
            match_num=_safe_int(row.get("match_num")),
            tourney_id=str(row.get("tourney_id", "")),
            tourney_date=_parse_date(row.get("tourney_date")),
            surface=str(row.get("surface", "")) or None,
            round=str(row.get("round", "")) or None,
            best_of=_safe_int(row.get("best_of")),
            winner_id=wid,
            loser_id=lid,
            score=str(row.get("score", "")) or None,
            winner_rank=_safe_int(row.get("winner_rank")),
            loser_rank=_safe_int(row.get("loser_rank")),
            w_ace=_safe_int(row.get("w_ace")),
            w_df=_safe_int(row.get("w_df")),
            w_svpt=_safe_int(row.get("w_svpt")),
            w_1stIn=_safe_int(row.get("w_1stIn")),
            w_1stWon=_safe_int(row.get("w_1stWon")),
            w_2ndWon=_safe_int(row.get("w_2ndWon")),
            w_SvGms=_safe_int(row.get("w_SvGms")),
            w_bpSaved=_safe_int(row.get("w_bpSaved")),
            w_bpFaced=_safe_int(row.get("w_bpFaced")),
            l_ace=_safe_int(row.get("l_ace")),
            l_df=_safe_int(row.get("l_df")),
            l_svpt=_safe_int(row.get("l_svpt")),
            l_1stIn=_safe_int(row.get("l_1stIn")),
            l_1stWon=_safe_int(row.get("l_1stWon")),
            l_2ndWon=_safe_int(row.get("l_2ndWon")),
            l_SvGms=_safe_int(row.get("l_SvGms")),
            l_bpSaved=_safe_int(row.get("l_bpSaved")),
            l_bpFaced=_safe_int(row.get("l_bpFaced")),
        )
        batch.append(m)
        m_count += 1
        if len(batch) >= 2000:
            db.add_all(batch)
            db.flush()
            batch = []
    if batch:
        db.add_all(batch)
    db.commit()
    logger.info(f"Loaded {m_count} matches")


def load_rankings(db: Session):
    path = DATA_DIR / "atp_rankings_current.csv"
    if not path.exists():
        logger.warning("atp_rankings_current.csv not found")
        return
    existing = db.query(Ranking).count()
    if existing > 0:
        logger.info(f"Rankings already loaded ({existing}), skipping")
        return
    df = pd.read_csv(path, dtype=str)
    count = 0
    batch = []
    for _, row in df.iterrows():
        pid = _safe_int(row.get("player"))
        rk = _safe_int(row.get("rank"))
        d = _parse_date(row.get("ranking_date"))
        if not pid or not rk or not d:
            continue
        batch.append(Ranking(
            player_id=pid,
            ranking_date=d,
            rank=rk,
            points=_safe_int(row.get("points")),
        ))
        count += 1
        if len(batch) >= 5000:
            db.add_all(batch)
            db.flush()
            batch = []
    if batch:
        db.add_all(batch)
    db.commit()
    logger.info(f"Loaded {count} ranking entries")


def run_full_pipeline():
    logger.info("=== Starting full data pipeline ===")
    download_all_data()
    db = SessionLocal()
    try:
        load_players(db)
        load_matches(db)
        load_rankings(db)
    finally:
        db.close()
    logger.info("=== Data pipeline complete ===")
