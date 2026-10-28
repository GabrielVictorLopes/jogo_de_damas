"""Telas: Menu, Partida e Fim de jogo."""
import math
import pygame
from checkers.board import Color, Piece
from checkers.game import Game
from checkers.rules import RuleSet
from .animation import MoveAnimation
from .widgets import Button, TextInput, Toggle
from . import theme as T


DECOR = [(0.10, 0.24, True, True), (0.90, 0.30, False, False),
         (0.08, 0.76, False, True), (0.92, 0.72, True, False)]


class MenuScreen:
    def __init__(self, app, names) -> None:
        self.app = app
        self.inputs = [TextInput("Jogador 1 — Brancas", names[0]),
                       TextInput("Jogador 2 — Pretas", names[1])]
        self.start = Button("Iniciar partida", self._start)
        self.swatches: list[pygame.Rect] = []
        self.dt = 0.0
        r = app.rules
        self.toggles = {
            "mandatory_capture": Toggle("Comer obrigatório", r.mandatory_capture),
            "majority_rule": Toggle("Lei da maioria", r.majority_rule),
            "men_capture_backward": Toggle("Pedra come p/ trás", r.men_capture_backward),
            "flying_kings": Toggle("Dama voadora", r.flying_kings),
        }

    def _start(self) -> None:
        n1 = self.inputs[0].value.strip() or "Jogador 1"
        n2 = self.inputs[1].value.strip() or "Jogador 2"
        self.app.rules = RuleSet(**{k: t.value for k, t in self.toggles.items()})
        self.app.start_game(n1, n2)

    def handle(self, e) -> None:
        for w in (*self.inputs, *self.toggles.values(), self.start):
            w.handle(e)
        self.toggles["majority_rule"].enabled = self.toggles["mandatory_capture"].value
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._start()
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.swatches):
                if r.collidepoint(e.pos):
                    self.app.theme = i

    def update(self, dt) -> None:
        self.dt = dt

    def draw(self, surf) -> None:
        w, h = surf.get_size()
        t = pygame.time.get_ticks() / 1000
        for i, (fx, fy, light, king) in enumerate(DECOR):
            T.piece(surf, (fx * w, fy * h + math.sin(t * 1.2 + i) * 10), 30, light, king, alpha=110)
        card = pygame.Rect(0, 0, min(460, w - 40), 600)
        card.center = (w // 2, h // 2 + 50)
        T.text(surf, "DAMAS", 68, T.TEXT, center=(w // 2, card.top - 72), bold=True)
        T.text(surf, "2 jogadores  ·  regras oficiais", 18, T.MUTED, center=(w // 2, card.top - 26))
        T.shadow(surf, card, 18)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=18)
        pygame.draw.rect(surf, T.SURFACE_HI, card, 1, border_radius=18)
        for i, inp in enumerate(self.inputs):
            inp.rect = pygame.Rect(card.x + 30, card.y + 50 + i * 88, card.w - 60, 50)
            inp.draw(surf, self.dt)
        T.text(surf, "Tabuleiro", 16, T.MUTED, topleft=(card.x + 30, card.y + 214))
        n, gap = len(T.BOARD_THEMES), 10
        sw = (card.w - 60 - gap * (n - 1)) // n
        self.swatches = []
        for i, th in enumerate(T.BOARD_THEMES):
            r = pygame.Rect(card.x + 30 + i * (sw + gap), card.y + 240, sw, sw)
            self.swatches.append(r)
            q = sw / 4
            pygame.draw.rect(surf, th["frame"], r.inflate(6, 6), border_radius=8)
            for y in range(4):
                for x in range(4):
                    pygame.draw.rect(surf, th["dark"] if (x + y) % 2 else th["light"],
                                     (r.x + x * q, r.y + y * q, q + 1, q + 1))
            sel = i == self.app.theme
            if sel or r.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surf, T.ACCENT if sel else T.MUTED, r.inflate(10, 10), 3, border_radius=10)
            T.text(surf, th["name"], 13, T.TEXT if sel else T.MUTED, center=(r.centerx, r.bottom + 16))
        T.text(surf, "Regras", 16, T.MUTED, topleft=(card.x + 30, card.y + 352))
        tw = (card.w - 70) // 2
        for i, tg in enumerate(self.toggles.values()):
            tg.rect = pygame.Rect(card.x + 30 + (i % 2) * (tw + 10), card.y + 378 + (i // 2) * 48, tw, 40)
            tg.draw(surf)
        self.start.rect = pygame.Rect(card.x + 30, card.bottom - 86, card.w - 60, 56)
        self.start.draw(surf)


class MatchScreen:
    TOP = 110
    M = 24  # moldura com coordenadas

    def __init__(self, app, game: Game) -> None:
        self.app, self.game = app, game
        self.selected = None
        self.hover = None
        self.anim: MoveAnimation | None = None
        self.last = None
        self.menu_btn = Button("Menu", app.show_menu, primary=False, size=17)
        self.theme_btn = Button("Tema", self._next_theme, primary=False, size=17)

    def _next_theme(self) -> None:
        self.app.theme = (self.app.theme + 1) % len(T.BOARD_THEMES)

    # ---------- layout responsivo ----------
    def layout(self, surf) -> None:
        w, h = surf.get_size()
        size = max(240, min(w - 40 - 2 * self.M, h - self.TOP - 20 - 2 * self.M))
        self.cell = size // 8
        self.ox = (w - self.cell * 8) // 2
        self.oy = self.TOP + (h - self.TOP - self.cell * 8) // 2

    def cell_at(self, pos):
        c, r = (pos[0] - self.ox) // self.cell, (pos[1] - self.oy) // self.cell
        return (r, c) if 0 <= r < 8 and 0 <= c < 8 else None

    def center_of(self, r, c):
        return (self.ox + c * self.cell + self.cell / 2, self.oy + r * self.cell + self.cell / 2)

    # ---------- eventos ----------
    def handle(self, e) -> None:
        self.menu_btn.handle(e)
        self.theme_btn.handle(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_t:
            self._next_theme()
        if self.anim or self.game.over or not hasattr(self, "cell"):
            return
        if e.type == pygame.MOUSEMOTION:
            self.hover = self.cell_at(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            cell = self.cell_at(e.pos)
            if cell is None:
                return
            if self.selected:
                moves = [m for m in self.game.moves_from(self.selected) if m.end == cell]
                if moves:
                    piece = self.game.board.get(*self.selected)
                    self.anim = MoveAnimation(moves[0], piece)
                    self.selected = None
                    return
            self.selected = cell if self.game.moves_from(cell) else None

    def update(self, dt) -> None:
        self.game.tick(dt)
        if self.anim and self.anim.update(dt):
            self.game.play(self.anim.move)
            self.last, self.anim = self.anim.move, None
            if self.game.over:
                self.app.show_end(self)

    # ---------- desenho ----------
    def _hovered_move(self):
        if self.selected and self.hover:
            for m in self.game.moves_from(self.selected):
                if m.end == self.hover:
                    return m
        return None

    def draw_piece(self, surf, center, piece: Piece, alpha=255) -> None:
        T.piece(surf, center, int(self.cell * 0.38), piece.color is Color.LIGHT, piece.king, alpha)

    def _player_card(self, surf, rect, player, active) -> None:
        T.shadow(surf, rect, 14, 8, 70)
        pygame.draw.rect(surf, T.SURFACE_HI if active else T.SURFACE, rect, border_radius=14)
        if active:
            pygame.draw.rect(surf, T.ACCENT, rect, 2, border_radius=14)
        dot = T.P_LIGHT if player.color is Color.LIGHT else T.P_DARK
        pygame.draw.circle(surf, dot, (rect.x + 24, rect.y + 26), 10)
        pygame.draw.circle(surf, T.MUTED, (rect.x + 24, rect.y + 26), 10, 1)
        T.text(surf, player.name, 20, T.TEXT, midleft=(rect.x + 44, rect.y + 26), bold=True)
        m, s = divmod(int(player.time), 60)
        T.text(surf, f"Pontos: {player.score}", 16, T.MUTED, topleft=(rect.x + 16, rect.y + 48))
        T.text(surf, f"⏱ {m:02d}:{s:02d}", 18, T.TEXT, topright=(rect.right - 16, rect.y + 46))

    def draw(self, surf) -> None:
        self.layout(surf)
        w = surf.get_width()
        g = self.game
        # cabeçalho: cartões dos jogadores + indicador de turno
        cw = max(150, min(300, (w - 290) // 2))
        self._player_card(surf, pygame.Rect(20, 16, cw, 80), g.players[Color.LIGHT],
                          g.turn is Color.LIGHT and not g.over)
        self._player_card(surf, pygame.Rect(w - 20 - cw, 16, cw, 80), g.players[Color.DARK],
                          g.turn is Color.DARK and not g.over)
        T.text(surf, f"Vez de {g.current.name}", 18, T.ACCENT, center=(w // 2, 34), bold=True)
        if g.rules.mandatory_capture and g.legal and g.legal[0].captured:
            T.text(surf, "Captura obrigatória!", 15, T.DANGER, center=(w // 2, 58))
        th = T.BOARD_THEMES[self.app.theme]
        self.theme_btn.label = f"Tema: {th['name']}"
        self.menu_btn.rect = pygame.Rect(w // 2 - 118, 70, 86, 30)
        self.theme_btn.rect = pygame.Rect(w // 2 - 24, 70, 142, 30)
        self.menu_btn.draw(surf)
        self.theme_btn.draw(surf)

        cs = self.cell
        hmove = self._hovered_move()
        targets = {m.end for m in g.moves_from(self.selected)} if self.selected else set()
        movable = {m.start for m in g.legal}
        overlay = pygame.Surface((cs, cs), pygame.SRCALPHA)
        M = self.M
        frame = pygame.Rect(self.ox - M, self.oy - M, cs * 8 + 2 * M, cs * 8 + 2 * M)
        T.shadow(surf, frame, 14, 16, 140)
        pygame.draw.rect(surf, th["frame"], frame, border_radius=14)
        for i in range(8):
            T.text(surf, "abcdefgh"[i], 13, (232, 222, 206), center=(self.ox + i * cs + cs / 2, self.oy + cs * 8 + M / 2))
            T.text(surf, str(8 - i), 13, (232, 222, 206), center=(self.ox - M / 2, self.oy + i * cs + cs / 2))
        for r in range(8):
            for c in range(8):
                rect = pygame.Rect(self.ox + c * cs, self.oy + r * cs, cs, cs)
                pygame.draw.rect(surf, th["dark"] if (r + c) % 2 else th["light"], rect)
                if self.last and (r, c) in (self.last.start, self.last.end):
                    overlay.fill((*T.GOLD, 60)); surf.blit(overlay, rect)
                if (r, c) == self.selected:
                    overlay.fill((*T.ACCENT, 110)); surf.blit(overlay, rect)
                if (r, c) in targets:
                    if (r, c) == self.hover:
                        overlay.fill((*T.ACCENT, 140)); surf.blit(overlay, rect)
                    pygame.draw.circle(surf, T.ACCENT, rect.center, cs // 7)
                elif (r, c) == self.hover and (r, c) in movable and not self.anim:
                    overlay.fill((255, 255, 255, 45)); surf.blit(overlay, rect)

        for r in range(8):
            for c in range(8):
                p = g.board.get(r, c)
                if not p or (self.anim and (r, c) == self.anim.move.start):
                    continue
                alpha = 255
                if self.anim and (r, c) in self.anim.move.captured and self.anim.passed((r, c)):
                    alpha = 70
                self.draw_piece(surf, self.center_of(r, c), p, alpha)
                if hmove and (r, c) in hmove.captured:
                    pygame.draw.circle(surf, T.DANGER, self.center_of(r, c), int(cs * 0.42), 3)
                elif not self.selected and not self.anim and not g.over and (r, c) in movable:
                    pygame.draw.circle(surf, T.ACCENT, self.center_of(r, c), int(cs * 0.42), 2)
        if self.selected:
            pulse = 2 + int(2 * (1 + math.sin(pygame.time.get_ticks() / 150)))
            pygame.draw.circle(surf, T.GOLD, self.center_of(*self.selected), int(cs * 0.43), pulse)
        if self.anim:
            r, c = self.anim.position()
            self.draw_piece(surf, self.center_of(r, c), self.anim.piece)


class EndScreen:
    def __init__(self, app, match: MatchScreen) -> None:
        self.app, self.match = app, match
        self.buttons = [Button("Revanche", app.rematch), Button("Menu", app.show_menu, primary=False)]

    def handle(self, e) -> None:
        for b in self.buttons:
            b.handle(e)

    def update(self, dt) -> None:
        pass

    def draw(self, surf) -> None:
        self.match.draw(surf)
        w, h = surf.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        surf.blit(shade, (0, 0))
        card = pygame.Rect(0, 0, min(420, w - 40), 290)
        card.center = (w // 2, h // 2)
        T.shadow(surf, card, 18)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=18)
        g = self.match.game
        title = "Empate!" if g.draw else f"{g.winner.name} venceu!"
        T.text(surf, title, 34, T.GOLD, center=(card.centerx, card.y + 50), bold=True)
        pl, pd = g.players[Color.LIGHT], g.players[Color.DARK]
        T.text(surf, f"{pl.name} {pl.score}  ×  {pd.score} {pd.name}", 20, T.TEXT,
               center=(card.centerx, card.y + 105))
        bw = (card.w - 90) // 2
        for i, b in enumerate(self.buttons):
            b.rect = pygame.Rect(card.x + 30 + i * (bw + 30), card.bottom - 90, bw, 56)
            b.draw(surf)
