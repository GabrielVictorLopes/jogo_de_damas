"""Modelo do tabuleiro: matriz bidimensional 8x8 de peças."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    LIGHT = 1  # Brancas (começam embaixo, movem para cima)
    DARK = 2   # Pretas

    @property
    def opponent(self) -> "Color":
        return Color.DARK if self is Color.LIGHT else Color.LIGHT

    @property
    def direction(self) -> int:
        return -1 if self is Color.LIGHT else 1

    @property
    def promotion_row(self) -> int:
        return 0 if self is Color.LIGHT else Board.SIZE - 1


@dataclass
class Piece:
    color: Color
    king: bool = False


@dataclass(frozen=True)
class Move:
    path: tuple[tuple[int, int], ...]
    captured: tuple[tuple[int, int], ...] = ()

    @property
    def start(self) -> tuple[int, int]:
        return self.path[0]

    @property
    def end(self) -> tuple[int, int]:
        return self.path[-1]


class Board:
    SIZE = 8

    def __init__(self, setup: bool = True) -> None:
        self.grid: list[list[Piece | None]] = [[None] * self.SIZE for _ in range(self.SIZE)]
        if setup:
            self.setup()

    def setup(self) -> None:
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if (r + c) % 2 == 1:
                    if r < 3:
                        self.grid[r][c] = Piece(Color.DARK)
                    elif r > 4:
                        self.grid[r][c] = Piece(Color.LIGHT)

    @classmethod
    def inside(cls, r: int, c: int) -> bool:
        return 0 <= r < cls.SIZE and 0 <= c < cls.SIZE

    def get(self, r: int, c: int) -> Piece | None:
        return self.grid[r][c]

    def set(self, r: int, c: int, piece: Piece | None) -> None:
        self.grid[r][c] = piece

    def pieces(self, color: Color):
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                p = self.grid[r][c]
                if p and p.color is color:
                    yield r, c, p

    def count(self, color: Color) -> int:
        return sum(1 for _ in self.pieces(color))

    def apply(self, move: Move) -> bool:
        """Executa o lance; retorna True se houve promoção."""
        (sr, sc), (er, ec) = move.start, move.end
        piece = self.grid[sr][sc]
        self.grid[sr][sc] = None
        for r, c in move.captured:
            self.grid[r][c] = None
        self.grid[er][ec] = piece
        if piece and not piece.king and er == piece.color.promotion_row:
            piece.king = True
            return True
        return False
