"""Animação linear de movimento (interpolação segmento a segmento)."""
import math
import random
import pygame
from checkers.board import Move, Piece


class MoveAnimation:
    SEGMENT_TIME = 0.18  # segundos por casa-destino do caminho

    def __init__(self, move: Move, piece: Piece) -> None:
        self.move, self.piece, self.t = move, piece, 0.0
        self.total = self.SEGMENT_TIME * (len(move.path) - 1)

    def update(self, dt: float) -> bool:
        self.t = min(self.t + dt, self.total)
        return self.t >= self.total

    def position(self) -> tuple[float, float]:
        """Posição atual em coordenadas (linha, coluna) fracionárias."""
        seg = min(int(self.t / self.SEGMENT_TIME), len(self.move.path) - 2)
        f = min(1.0, (self.t - seg * self.SEGMENT_TIME) / self.SEGMENT_TIME)
        (r1, c1), (r2, c2) = self.move.path[seg], self.move.path[seg + 1]
        return r1 + (r2 - r1) * f, c1 + (c2 - c1) * f

    def passed(self, square) -> bool:
        """Peça capturada já foi 'pulada' pela animação?"""
        idx = self.move.captured.index(square)
        return self.t >= (idx + 0.5) * self.SEGMENT_TIME


class Particles:
    """Sistema simples de partículas (estouro de captura, promoção, confete)."""

    def __init__(self) -> None:
        self.items: list[list] = []

    def burst(self, pos, color, n=18, speed=170, life=0.6, size=5, gravity=0.0, spread=math.tau, angle=0.0):
        for _ in range(n):
            a = angle + random.uniform(-spread / 2, spread / 2)
            v = random.uniform(0.35, 1.0) * speed
            self.items.append([pos[0], pos[1], math.cos(a) * v, math.sin(a) * v, life, life, color, size, gravity])

    def update(self, dt: float) -> None:
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[8] * dt
            p[4] -= dt
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self, surf) -> None:
        for x, y, _, _, life, total, color, size, _ in self.items:
            pygame.draw.circle(surf, color, (int(x), int(y)), max(1, int(size * life / total)))