"""Animação linear de movimento (interpolação segmento a segmento)."""
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
