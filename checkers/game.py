"""Estado da partida: turnos, pontuação, cronômetro e fim de jogo."""
from __future__ import annotations
from dataclasses import asdict, dataclass
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

    def __init__(self, name1: str, name2: str, rules: RuleSet | None = None,
                 p1_color: Color = Color.LIGHT) -> None:
        """O Jogador 1 escolhe o lado (p1_color); as Brancas sempre começam."""
        self.rules = rules or RuleSet()
        self.p1_color = p1_color
        self.players = {p1_color: Player(name1, p1_color),
                        p1_color.opponent: Player(name2, p1_color.opponent)}
        self.reset()

    def reset(self) -> None:
        self.board = Board()
        self.turn = Color.LIGHT
        self.winner: Player | None = None
        self.draw = False
        self.ended = False  # encerrada manualmente pelos jogadores
        self.quiet_king_moves = 0
        self.move_count = 0
        self.paused = False
        for p in self.players.values():
            p.score, p.time = 0, 0.0
        self.legal = Rules.legal_moves(self.board, self.turn, self.rules)

    @property
    def current(self) -> Player:
        return self.players[self.turn]

    @property
    def player1(self) -> Player:
        return self.players[self.p1_color]

    @property
    def player2(self) -> Player:
        return self.players[self.p1_color.opponent]

    @property
    def elapsed(self) -> float:
        """Tempo total de partida (soma do tempo dos dois jogadores)."""
        return sum(p.time for p in self.players.values())

    @property
    def over(self) -> bool:
        return self.winner is not None or self.draw or self.ended

    def moves_from(self, pos: tuple[int, int]) -> list[Move]:
        return [m for m in self.legal if m.start == pos]

    def end(self) -> None:
        """Encerra a partida sem vencedor (registrada como finalizada)."""
        self.ended, self.paused = True, False

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
        self.move_count += 1
        self.quiet_king_moves = self.quiet_king_moves + 1 if was_king and not move.captured else 0
        self.turn = self.turn.opponent
        self.legal = Rules.legal_moves(self.board, self.turn, self.rules)
        if not self.legal:  # sem peças ou bloqueado: perde
            self.winner = self.players[self.turn.opponent]
        elif self.quiet_king_moves >= self.DRAW_LIMIT:
            self.draw = True
        return True

    # ---------- persistência ----------
    def to_dict(self) -> dict:
        """Estado completo da partida em tipos simples (JSON) para salvar e retomar."""
        return {
            "board": self.board.to_text(),
            "turn": self.turn.name,
            "p1_color": self.p1_color.name,
            "names": [self.player1.name, self.player2.name],
            "scores": [self.player1.score, self.player2.score],
            "times": [self.player1.time, self.player2.time],
            "quiet_king_moves": self.quiet_king_moves,
            "move_count": self.move_count,
            "winner": self.winner.color.name if self.winner else None,
            "draw": self.draw,
            "ended": self.ended,
            "rules": asdict(self.rules),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Game":
        known = RuleSet.__dataclass_fields__
        rules = RuleSet(**{k: v for k, v in d.get("rules", {}).items() if k in known})
        g = cls(d["names"][0], d["names"][1], rules, Color[d["p1_color"]])
        g.board = Board.from_text(d["board"])
        g.turn = Color[d["turn"]]
        for p, score, t in zip((g.player1, g.player2), d["scores"], d["times"]):
            p.score, p.time = int(score), float(t)
        g.quiet_king_moves = int(d.get("quiet_king_moves", 0))
        g.move_count = int(d.get("move_count", 0))
        g.draw = bool(d.get("draw", False))
        g.ended = bool(d.get("ended", False))
        g.winner = g.players[Color[d["winner"]]] if d.get("winner") else None
        g.legal = Rules.legal_moves(g.board, g.turn, g.rules)
        return g
