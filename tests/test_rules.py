"""Casos de teste das regras, do estado de partida e do banco (CT01–CT22)."""
import os
import tempfile
import unittest
from checkers.board import Board, Color, Move, Piece
from checkers.game import Game
from checkers.rules import Rules, RuleSet
from checkers.storage import GameStore, FINISHED, IN_PROGRESS, ABANDONED
from checkers.positions import endgame_demo
from ui.transform import Transform2D, Vector2D
import math

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


    def test_ct15_pause_and_restart(self):
        g = Game("A", "B")
        move = g.legal[0]
        g.pause()
        g.tick(5.0)
        self.assertEqual(g.players[L].time, 0.0)
        self.assertFalse(g.play(move))  # jogada com o jogo pausado é recusada
        g.resume()
        self.assertTrue(g.play(move))
        g.reset()
        self.assertEqual((g.turn, g.board.count(D), g.players[L].score), (L, 12, 0))

    def test_ct16_demo_endgame_victory(self):
        g = Game("A", "B")
        g.load_board(endgame_demo())
        self.assertEqual(len(g.legal), 1)
        self.assertTrue(g.play(g.legal[0]))  # captura dupla com promoção
        self.assertTrue(g.board.get(0, 5).king)
        self.assertTrue(g.play(g.legal[0]))  # Pretas avançam
        self.assertTrue(g.play(g.legal[0]))  # Brancas capturam a última peça
        self.assertIs(g.winner, g.players[L])
        self.assertEqual(g.players[L].score, 3)

    def test_ct17_matrix_transforms(self):
        m = Transform2D.translation(100, 50) @ Transform2D.scaling(60)  # mundo -> tela
        p = m.apply(Vector2D(2.5, 3.5))
        self.assertEqual((p.x, p.y), (250.0, 260.0))
        back = m.inverse().apply(p)
        self.assertAlmostEqual(back.x, 2.5); self.assertAlmostEqual(back.y, 3.5)
        r = Transform2D.rotation(math.pi / 2).apply(Vector2D(1, 0))
        self.assertAlmostEqual(r.x, 0); self.assertAlmostEqual(r.y, 1)
        mid = Vector2D(0, 0).lerp(Vector2D(4, 2), 0.5)
        self.assertEqual((mid.x, mid.y), (2.0, 1.0))

    def test_ct19_hints_rule_does_not_change_moves(self):
        b = board_with((5, 2, L, False), (4, 3, D, False), (5, 6, L, False))
        on = Rules.legal_moves(b, L, RuleSet(show_hints=True))
        off = Rules.legal_moves(b, L, RuleSet(show_hints=False))
        self.assertEqual(on, off)  # a ajuda é só visual: os lances legais continuam os mesmos
        self.assertTrue(RuleSet().show_hints)

    def test_ct20_choose_side(self):
        g = Game("Ana", "Beto", p1_color=D)
        self.assertEqual((g.player1.name, g.player1.color), ("Ana", D))
        self.assertEqual((g.player2.name, g.player2.color), ("Beto", L))
        self.assertEqual(g.turn, L)  # as Brancas sempre começam: quem escolheu Pretas joga em segundo
        self.assertEqual(g.current.name, "Beto")
        g.reset()
        self.assertEqual(g.player1.color, D)

    def test_ct21_save_and_resume_state(self):
        g = Game("Ana", "Beto", RuleSet(mandatory_capture=False, show_hints=False), D)
        g.play(g.legal[0]); g.tick(3.0)
        g.play(g.legal[0]); g.tick(2.0)
        r = Game.from_dict(g.to_dict())
        self.assertEqual((r.board.to_text(), r.turn, r.move_count), (g.board.to_text(), g.turn, 2))
        self.assertEqual((r.player1.name, r.player1.color, r.rules), ("Ana", D, g.rules))
        self.assertAlmostEqual(r.elapsed, 5.0)
        self.assertEqual(len(r.legal), len(g.legal))
        with self.assertRaises(ValueError):
            Board.from_text("x" * 64)

    def test_ct22_database_history(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "damas.db")
            db = GameStore(path)
            g = Game("Ana", "Beto")
            gid = db.create(g, theme=3)
            self.assertEqual(db.latest_in_progress().id, gid)
            g.play(g.legal[0]); g.tick(7.5)
            db.save(gid, g, 3)
            db.close()
            db = GameStore(path)  # fecha e reabre: o jogo continua lá
            rec = db.latest_in_progress()
            self.assertEqual((rec.player1, rec.moves, rec.status), ("Ana", 1, IN_PROGRESS))
            game, theme = db.load(gid)
            self.assertEqual((game.turn, theme, round(game.elapsed, 1)), (D, 3, 7.5))
            # fim de partida: vira "finalizada" com vencedor, placar e tempo
            g.board = board_with((5, 2, L, False), (4, 3, D, False)); g.turn = L
            g.legal = Rules.legal_moves(g.board, L, g.rules)
            g.play(g.legal[0])
            db.save(gid, g, 3)
            rec = db.history()[0]
            self.assertEqual((rec.status, rec.winner, rec.score1, rec.result_text), (FINISHED, "Ana", 1, "Ana venceu"))
            self.assertIsNone(db.latest_in_progress())
            gid2 = db.create(Game("C", "D"))
            db.abandon(gid2)
            self.assertEqual(db.history()[0].status, ABANDONED)
            db.close()

    def test_ct23_end_match_manually(self):
        with tempfile.TemporaryDirectory() as d:
            db = GameStore(os.path.join(d, "damas.db"))
            g = Game("Ana", "Beto")
            gid = db.create(g)
            g.play(g.legal[0]); g.tick(4.0)
            g.end()
            self.assertTrue(g.over)
            self.assertFalse(g.play(g.legal[0]))  # encerrada: não aceita mais lances
            db.save(gid, g)
            rec = db.history()[0]
            self.assertEqual((rec.status, rec.ended, rec.result_text, rec.moves), (FINISHED, True, "Encerrada", 1))
            self.assertIsNone(db.latest_in_progress())  # não aparece mais para retomar
            self.assertTrue(Game.from_dict(g.to_dict()).ended)
            db.close()

    def test_ct24_delete_records_and_migration(self):
        with tempfile.TemporaryDirectory() as d:
            db = GameStore(os.path.join(d, "damas.db"))
            ids = [db.create(Game("A", "B")) for _ in range(3)]
            db.delete(ids[1])
            self.assertEqual({r.id for r in db.history()}, {ids[0], ids[2]})
            db.clear()
            self.assertEqual(db.history(), [])
            db.close()
            # banco antigo (sem a coluna "ended") é atualizado sem perder os dados
            import sqlite3
            old = os.path.join(d, "velho.db")
            con = sqlite3.connect(old)
            con.execute(GameStore.SCHEMA.replace(",\n        ended       INTEGER NOT NULL DEFAULT 0", ""))
            con.execute("INSERT INTO games (started_at, updated_at, status, player1, player2, state) VALUES (1,1,'finalizada','X','Y','{}')")
            con.commit(); con.close()
            db = GameStore(old)
            self.assertTrue(db.available)
            self.assertEqual(db.history()[0].player1, "X")
            db.close()

    def test_ct22b_database_unavailable_is_silent(self):
        db = GameStore("/proc/nao/pode/criar/damas.db")
        self.assertFalse(db.available)
        self.assertIsNone(db.create(Game("A", "B")))
        self.assertEqual(db.history(), [])
        self.assertIsNone(db.latest_in_progress())


if __name__ == "__main__":
    unittest.main()
