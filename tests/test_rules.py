"""Casos de teste das regras (CT01–CT10)."""
import unittest
from checkers.board import Board, Color, Move, Piece
from checkers.game import Game
from checkers.rules import Rules, RuleSet

L, D = Color.LIGHT, Color.DARK


def board_with(*items):
    b = Board(setup=False)
    for r, c, color, king in items:
        b.set(r, c, Piece(color, king))
    return b


class TestRules(unittest.TestCase):
    def test_ct01_initial_position(self):
        b = Board()
        self.assertEqual((b.count(L), b.count(D)), (12, 12))
        self.assertEqual(len(Rules.legal_moves(b, L)), 7)

    def test_ct02_invalid_backward_move(self):
        g = Game("A", "B")
        self.assertFalse(g.play(Move(((5, 0), (6, 1)))))
        self.assertEqual(g.turn, L)

    def test_ct03_collision_occupied_square(self):
        b = board_with((5, 2, L, False), (4, 1, L, False), (4, 3, L, False))
        ends = {m.end for m in Rules.legal_moves(b, L) if m.start == (5, 2)}
        self.assertEqual(ends, set())

    def test_ct04_capture_mandatory(self):
        b = board_with((5, 2, L, False), (4, 3, D, False), (5, 6, L, False))
        moves = Rules.legal_moves(b, L)
        self.assertEqual(moves, [Move(((5, 2), (3, 4)), ((4, 3),))])

    def test_ct05_backward_capture_by_man(self):
        b = board_with((3, 2, L, False), (4, 3, D, False))
        self.assertIn(Move(((3, 2), (5, 4)), ((4, 3),)), Rules.legal_moves(b, L))

    def test_ct06_multiple_capture_and_majority(self):
        b = board_with((7, 0, L, False), (6, 1, D, False), (4, 3, D, False),
                       (7, 6, L, False), (6, 7, D, False))
        moves = Rules.legal_moves(b, L)
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].path, ((7, 0), (5, 2), (3, 4)))
        self.assertEqual(len(moves[0].captured), 2)

    def test_ct07_promotion(self):
        b = board_with((1, 2, L, False))
        self.assertTrue(b.apply(Move(((1, 2), (0, 1)))))
        self.assertTrue(b.get(0, 1).king)

    def test_ct08_flying_king(self):
        b = board_with((7, 0, L, True), (3, 4, D, False))
        moves = Rules.legal_moves(b, L)
        self.assertTrue(all(m.captured == ((3, 4),) for m in moves))
        self.assertEqual({m.end for m in moves}, {(2, 5), (1, 6), (0, 7)})

    def test_ct09_turns_and_score(self):
        g = Game("A", "B")
        g.board = board_with((5, 2, L, False), (4, 3, D, False), (0, 7, D, False))
        g.legal = Rules.legal_moves(g.board, L)
        self.assertTrue(g.play(g.legal[0]))
        self.assertEqual(g.players[L].score, 1)
        self.assertEqual(g.turn, D)

    def test_ct10_victory_and_draw(self):
        g = Game("A", "B")
        g.board = board_with((5, 2, L, False), (4, 3, D, False))
        g.legal = Rules.legal_moves(g.board, L)
        g.play(g.legal[0])
        self.assertIs(g.winner, g.players[L])
        g = Game("A", "B")
        g.board = board_with((7, 0, L, True), (0, 3, D, True))
        g.legal = Rules.legal_moves(g.board, L)
        g.quiet_king_moves = Game.DRAW_LIMIT - 1
        g.play(Move(((7, 0), (6, 1))))
        self.assertTrue(g.draw)

    def test_ct11_custom_rules(self):
        b = board_with((5, 2, L, False), (4, 3, D, False), (5, 6, L, False))
        free = Rules.legal_moves(b, L, RuleSet(mandatory_capture=False))
        self.assertTrue(any(m.captured for m in free) and any(not m.captured for m in free))
        b = board_with((3, 2, L, False), (4, 3, D, False))
        self.assertFalse(any(m.captured for m in Rules.legal_moves(b, L, RuleSet(men_capture_backward=False))))
        b = board_with((7, 0, L, True))
        self.assertEqual(len(Rules.legal_moves(b, L, RuleSet(flying_kings=False))), 1)
        # sem captura obrigatória pode parar no meio de uma captura múltipla
        b = board_with((7, 0, L, False), (6, 1, D, False), (4, 3, D, False))
        ends = {m.end for m in Rules.legal_moves(b, L, RuleSet(mandatory_capture=False))}
        self.assertTrue({(5, 2), (3, 4)} <= ends)


if __name__ == "__main__":
    unittest.main()