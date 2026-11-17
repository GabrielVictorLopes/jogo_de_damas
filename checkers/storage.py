"""Banco de dados das partidas (SQLite, biblioteca padrão): histórico e retomada.

Sem dependência gráfica. Qualquer falha de disco desliga o banco em silêncio
(`available = False`) para nunca derrubar o jogo.
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from .game import Game

IN_PROGRESS, FINISHED, ABANDONED = "em_andamento", "finalizada", "abandonada"


def default_path() -> str:
    override = os.environ.get("DAMAS_DB")
    if override:
        return override
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "JogoDeDamas", "damas.db")


@dataclass
class GameRecord:
    id: int
    started_at: float
    updated_at: float
    status: str
    player1: str
    player2: str
    winner: str | None   # nome do vencedor; None em empate, encerramento manual ou partida em andamento
    draw: bool
    score1: int
    score2: int
    duration: float      # segundos de jogo (soma dos dois cronômetros)
    moves: int
    ended: bool = False  # encerrada manualmente

    @property
    def result_text(self) -> str:
        if self.status == IN_PROGRESS:
            return "Em andamento"
        if self.status == ABANDONED:
            return "Abandonada"
        if self.ended:
            return "Encerrada"
        return "Empate" if self.draw else f"{self.winner} venceu"


class GameStore:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS games (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at  REAL NOT NULL,
        updated_at  REAL NOT NULL,
        status      TEXT NOT NULL,
        player1     TEXT NOT NULL,
        player2     TEXT NOT NULL,
        winner      TEXT,
        draw        INTEGER NOT NULL DEFAULT 0,
        score1      INTEGER NOT NULL DEFAULT 0,
        score2      INTEGER NOT NULL DEFAULT 0,
        duration    REAL NOT NULL DEFAULT 0,
        moves       INTEGER NOT NULL DEFAULT 0,
        theme       INTEGER NOT NULL DEFAULT 0,
        state       TEXT NOT NULL,
        ended       INTEGER NOT NULL DEFAULT 0
    )"""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or default_path()
        self.available = True
        try:
            if self.path != ":memory:":
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self.db = sqlite3.connect(self.path)
            self.db.execute(self.SCHEMA)
            cols = {r[1] for r in self.db.execute("PRAGMA table_info(games)")}
            if "ended" not in cols:  # banco criado por uma versão anterior do jogo
                self.db.execute("ALTER TABLE games ADD COLUMN ended INTEGER NOT NULL DEFAULT 0")
            self.db.commit()
        except (sqlite3.Error, OSError):
            self.available = False

    # ---------- escrita ----------
    def _row(self, game: Game, status: str, theme: int):
        p1, p2 = game.player1, game.player2
        return (status, p1.name, p2.name, game.winner.name if game.winner else None, int(game.draw),
                p1.score, p2.score, game.elapsed, game.move_count, theme, json.dumps(game.to_dict()),
                time.time(), int(game.ended))

    def create(self, game: Game, theme: int = 0) -> int | None:
        if not self.available:
            return None
        try:
            cur = self.db.execute(
                "INSERT INTO games (status, player1, player2, winner, draw, score1, score2, duration,"
                " moves, theme, state, updated_at, ended, started_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (*self._row(game, IN_PROGRESS, theme), time.time()))
            self.db.commit()
            return cur.lastrowid
        except sqlite3.Error:
            return None

    def save(self, game_id: int | None, game: Game, theme: int = 0) -> None:
        """Grava o estado atual; marca como finalizada se a partida acabou (vitória, empate ou encerrada)."""
        if not self.available or game_id is None:
            return
        status = FINISHED if game.over else IN_PROGRESS
        try:
            self.db.execute(
                "UPDATE games SET status=?, player1=?, player2=?, winner=?, draw=?, score1=?, score2=?,"
                " duration=?, moves=?, theme=?, state=?, updated_at=?, ended=? WHERE id=?",
                (*self._row(game, status, theme), game_id))
            self.db.commit()
        except sqlite3.Error:
            pass

    def abandon(self, game_id: int | None) -> None:
        if not self.available or game_id is None:
            return
        try:
            self.db.execute("UPDATE games SET status=?, updated_at=? WHERE id=? AND status=?",
                            (ABANDONED, time.time(), game_id, IN_PROGRESS))
            self.db.commit()
        except sqlite3.Error:
            pass

    def delete(self, game_id: int) -> None:
        """Exclui o registro de uma partida."""
        if not self.available:
            return
        try:
            self.db.execute("DELETE FROM games WHERE id=?", (game_id,))
            self.db.commit()
        except sqlite3.Error:
            pass

    def clear(self) -> None:
        """Exclui todo o histórico."""
        if not self.available:
            return
        try:
            self.db.execute("DELETE FROM games")
            self.db.commit()
        except sqlite3.Error:
            pass

    # ---------- leitura ----------
    _COLS = "id, started_at, updated_at, status, player1, player2, winner, draw, score1, score2, duration, moves, ended"

    @staticmethod
    def _record(r) -> GameRecord:
        return GameRecord(r[0], r[1], r[2], r[3], r[4], r[5], r[6], bool(r[7]), r[8], r[9], r[10], r[11], bool(r[12]))

    def history(self, limit: int = 100) -> list[GameRecord]:
        if not self.available:
            return []
        try:
            rows = self.db.execute(
                f"SELECT {self._COLS} FROM games ORDER BY started_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
        except sqlite3.Error:
            return []
        return [self._record(r) for r in rows]

    def latest_in_progress(self) -> GameRecord | None:
        if not self.available:
            return None
        try:
            r = self.db.execute(
                f"SELECT {self._COLS} FROM games WHERE status=? ORDER BY updated_at DESC, id DESC LIMIT 1",
                (IN_PROGRESS,)).fetchone()
        except sqlite3.Error:
            return None
        return self._record(r) if r else None

    def load(self, game_id: int) -> tuple[Game, int] | None:
        """Retorna (partida, índice do tabuleiro) ou None se não existir/estiver corrompida."""
        if not self.available:
            return None
        try:
            r = self.db.execute("SELECT state, theme FROM games WHERE id=?", (game_id,)).fetchone()
            return (Game.from_dict(json.loads(r[0])), r[1]) if r else None
        except (sqlite3.Error, ValueError, KeyError, TypeError):
            return None

    def close(self) -> None:
        if self.available:
            self.db.close()
