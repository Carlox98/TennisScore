from datetime import date, datetime
from sqlalchemy import Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, default="")
    last_name: Mapped[str] = mapped_column(String, default="")
    name: Mapped[str] = mapped_column(String, index=True)
    nationality: Mapped[str | None] = mapped_column(String, nullable=True)
    hand: Mapped[str | None] = mapped_column(String(1), nullable=True)  # L/R/U
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    elo_overall: Mapped[float] = mapped_column(Float, default=1500.0)
    elo_hard: Mapped[float] = mapped_column(Float, default=1500.0)
    elo_clay: Mapped[float] = mapped_column(Float, default=1500.0)
    elo_grass: Mapped[float] = mapped_column(Float, default=1500.0)


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tourney_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    surface: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[str | None] = mapped_column(String(1), nullable=True)  # G/M/A/D/F
    draw_size: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_num: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tourney_id: Mapped[str] = mapped_column(String, ForeignKey("tournaments.tourney_id"), index=True)
    tourney_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    surface: Mapped[str | None] = mapped_column(String, nullable=True)
    round: Mapped[str | None] = mapped_column(String, nullable=True)
    best_of: Mapped[int | None] = mapped_column(Integer, nullable=True)

    winner_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), index=True)
    loser_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), index=True)
    score: Mapped[str | None] = mapped_column(String, nullable=True)

    winner_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loser_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Winner stats
    w_ace: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_df: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_svpt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_1stIn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_1stWon: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_2ndWon: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_SvGms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_bpSaved: Mapped[int | None] = mapped_column(Integer, nullable=True)
    w_bpFaced: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Loser stats
    l_ace: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_df: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_svpt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_1stIn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_1stWon: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_2ndWon: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_SvGms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_bpSaved: Mapped[int | None] = mapped_column(Integer, nullable=True)
    l_bpFaced: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    tournament: Mapped["Tournament"] = relationship("Tournament", foreign_keys=[tourney_id], primaryjoin="Match.tourney_id == Tournament.tourney_id")
    winner: Mapped["Player"] = relationship("Player", foreign_keys=[winner_id])
    loser: Mapped["Player"] = relationship("Player", foreign_keys=[loser_id])


class Ranking(Base):
    __tablename__ = "rankings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), index=True)
    ranking_date: Mapped[date] = mapped_column(Date, index=True)
    rank: Mapped[int] = mapped_column(Integer)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)

    player: Mapped["Player"] = relationship("Player")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"), nullable=True)
    player1_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    player2_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    surface: Mapped[str | None] = mapped_column(String, nullable=True)
    best_of: Mapped[int] = mapped_column(Integer, default=3)
    model_version: Mapped[str] = mapped_column(String, default="v1")
    prob_player1: Mapped[float] = mapped_column(Float)
    prob_player2: Mapped[float] = mapped_column(Float)
    predicted_winner_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    actual_winner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"), nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player1: Mapped["Player"] = relationship("Player", foreign_keys=[player1_id])
    player2: Mapped["Player"] = relationship("Player", foreign_keys=[player2_id])
