"""Regras oficiais (Damas Brasileiras): captura obrigatória, lei da maioria,
captura para trás pelas pedras, dama de longo alcance."""
from __future__ import annotations
from dataclasses import dataclass
from .board import Board, Color, Move, Piece

DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


@dataclass(frozen=True)
class RuleSet:
    """Regras configuráveis antes da partida (padrão = regras oficiais)."""
    mandatory_capture: bool = True     # comer é obrigatório
    majority_rule: bool = True         # obrigatório capturar o máximo de peças
    men_capture_backward: bool = True  # pedra pode capturar para trás
    flying_kings: bool = True          # dama anda/captura várias casas


class Rules:
    @staticmethod
    def legal_moves(board: Board, color: Color, rules: RuleSet | None = None) -> list[Move]:
        rules = rules or RuleSet()
        captures: list[Move] = []
        for r, c, p in board.pieces(color):
            captures += Rules._captures(board, r, c, p, rules)
        if captures and rules.mandatory_capture:
            if rules.majority_rule:
                best = max(len(m.captured) for m in captures)
                captures = [m for m in captures if len(m.captured) == best]
            return captures
        moves: list[Move] = captures
        for r, c, p in board.pieces(color):
            moves += Rules._simple_moves(board, r, c, p, rules)
        return moves

    @staticmethod
    def _simple_moves(board: Board, r: int, c: int, p: Piece, rules: RuleSet) -> list[Move]:
        moves = []
        long = p.king and rules.flying_kings
        for dr, dc in DIRECTIONS:
            if not p.king and dr != p.color.direction:
                continue  # pedra só anda para frente
            nr, nc = r + dr, c + dc
            while Board.inside(nr, nc) and board.get(nr, nc) is None:
                moves.append(Move(((r, c), (nr, nc))))
                if not long:
                    break
                nr, nc = nr + dr, nc + dc
        return moves

    @staticmethod
    def _captures(board: Board, r0: int, c0: int, p: Piece, rules: RuleSet) -> list[Move]:
        results: list[Move] = []
        long = p.king and rules.flying_kings
        only_forward = not p.king and not rules.men_capture_backward

        def empty(r: int, c: int) -> bool:
            return (r, c) == (r0, c0) or board.get(r, c) is None

        def dfs(pos, path, captured):
            found = False
            for dr, dc in DIRECTIONS:
                if only_forward and dr != p.color.direction:
                    continue
                nr, nc = pos[0] + dr, pos[1] + dc
                if long:
                    while Board.inside(nr, nc) and empty(nr, nc):
                        nr, nc = nr + dr, nc + dc
                if not Board.inside(nr, nc) or empty(nr, nc) or (nr, nc) in captured:
                    continue
                if board.get(nr, nc).color is p.color:
                    continue
                lr, lc = nr + dr, nc + dc
                while Board.inside(lr, lc) and empty(lr, lc):
                    found = True
                    dfs((lr, lc), path + [(lr, lc)], captured + [(nr, nc)])
                    if not long:
                        break
                    lr, lc = lr + dr, lc + dc
            if not found and captured:
                results.append(Move(tuple(path), tuple(captured)))

        dfs((r0, c0), [(r0, c0)], [])
        return results
