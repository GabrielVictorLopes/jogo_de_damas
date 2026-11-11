"""Transformações 2D com matrizes homogêneas 3x3 (sem dependência gráfica).

Usadas para converter coordenadas de mundo (tabuleiro: coluna, linha) em
coordenadas de tela (pixels) e para animar a coroa da dama com rotação e escala.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Vector2D:
    x: float
    y: float

    def __add__(self, o: "Vector2D") -> "Vector2D":
        return Vector2D(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vector2D") -> "Vector2D":
        return Vector2D(self.x - o.x, self.y - o.y)

    def __mul__(self, k: float) -> "Vector2D":
        return Vector2D(self.x * k, self.y * k)

    def lerp(self, o: "Vector2D", t: float) -> "Vector2D":
        """Interpolação linear: P(t) = A + (B - A)·t."""
        return self + (o - self) * t

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class Transform2D:
    """Matriz afim 3x3 em coordenadas homogêneas: [x', y', 1]ᵀ = M · [x, y, 1]ᵀ."""

    def __init__(self, m: list[list[float]] | None = None) -> None:
        self.m = m or [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    @classmethod
    def translation(cls, tx: float, ty: float) -> "Transform2D":
        return cls([[1, 0, tx], [0, 1, ty], [0, 0, 1]])

    @classmethod
    def scaling(cls, sx: float, sy: float | None = None) -> "Transform2D":
        sy = sx if sy is None else sy
        return cls([[sx, 0, 0], [0, sy, 0], [0, 0, 1]])

    @classmethod
    def rotation(cls, angle: float) -> "Transform2D":
        c, s = math.cos(angle), math.sin(angle)
        return cls([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    def __matmul__(self, o: "Transform2D") -> "Transform2D":
        """Composição: (A @ B) aplica B primeiro e depois A."""
        return Transform2D([[sum(self.m[i][k] * o.m[k][j] for k in range(3)) for j in range(3)] for i in range(3)])

    def apply(self, v: Vector2D) -> Vector2D:
        m = self.m
        return Vector2D(m[0][0] * v.x + m[0][1] * v.y + m[0][2], m[1][0] * v.x + m[1][1] * v.y + m[1][2])

    def apply_points(self, pts) -> list[tuple[float, float]]:
        return [self.apply(Vector2D(*p)).as_tuple() for p in pts]

    def inverse(self) -> "Transform2D":
        (a, b, tx), (c, d, ty), _ = self.m
        det = a * d - b * c
        ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
        return Transform2D([[ia, ib, -(ia * tx + ib * ty)], [ic, id_, -(ic * tx + id_ * ty)], [0, 0, 1]])
