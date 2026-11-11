"""Estado da partida: turnos, pontuação, cronômetro e fim de jogo."""
from __future__ import annotations
from dataclasses import dataclass
from .board import Board, Color, Move
from .rules import Rules, RuleSet


@dataclass
class Player:
    name: str
    color: Color
    score: int = 0
    time: float = 0.0


class Game:
    DRAW_LIMIT = 20  # lances seguidos só de damas, sem captura

    def __init__(self, name1: str, name2: str, rules: RuleSet | None = None) -> None:
        self.rules = rules or RuleSet()
        self.players = {Color.LIGHT: Player(name1, Color.LIGHT),
                        Color.DARK: Player(name2, Color.DARK)}
        self.reset()

    def reset(self) -> None:
        self.board = Board()
        self.turn = Color.LIGHT
        self.winner: Player | None = None
        self.draw = False
        self.quiet_king_moves = 0
        self.paused = False
        for p in self.players.values():
            p.score, p.time = 0, 0.0
        self.legal = Rules.legal_moves(self.board, self.turn, self.rules)

    @property
    def current(self) -> Player:
        return self.players[self.turn]

    @property
    def over(self) -> bool:
        return self.winner is not None or self.draw

    def moves_from(self, pos: tuple[int, int]) -> list[Move]:
        return [m for m in self.legal if m.start == pos]

    def pause(self) -> None:
        if not self.over:
            self.paused = True

    def resume(self) -> None:
        self.paused = False

    def load_board(self, board: Board, turn: Color = Color.LIGHT) -> None:
        """Reinicia a partida a partir de uma posição pronta (ex.: demonstração)."""
        self.reset()
        self.board, self.turn = board, turn
        self.legal = Rules.legal_moves(self.board, self.turn, self.rules)

    def tick(self, dt: float) -> None:
        if not self.over and not self.paused:
            self.current.time += dt

    def play(self, move: Move) -> bool:
        if self.over or self.paused or move not in self.legal:
            return False  # lance inválido, fora de hora ou jogo pausado
        was_king = self.board.get(*move.start).king
        self.board.apply(move)
        self.current.score += len(move.captured)
        self.quiet_king_moves = self.quiet_king_moves + 1 if was_king and not move.captured else 0
        self.turn = self.turn.opponent
        self.legal = Rules.legal_moves(self.board, self.turn, self.rules)
        if not self.legal:  # sem peças ou bloqueado: perde
            self.winner = self.players[self.turn.opponent]
        elif self.quiet_king_moves >= self.DRAW_LIMIT:
            self.draw = True
        return True
