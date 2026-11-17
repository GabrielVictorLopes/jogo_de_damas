"""Telas: Menu, Partida e Fim de jogo."""
import math
import random
import time
from abc import ABC, abstractmethod
import pygame
from checkers.board import Board, Color, Piece
from checkers.game import Game
from checkers.rules import RuleSet
from checkers.positions import endgame_demo
from .transform import Transform2D, Vector2D
from .animation import MoveAnimation, Particles
from .widgets import Button, Choice, TextInput, Toggle
from . import theme as T


class Screen(ABC):
    """Base das telas (padrão State): o App delega eventos, atualização e desenho à tela atual."""

    def __init__(self, app) -> None:
        self.app = app

    @abstractmethod
    def handle(self, e) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, surf) -> None: ...


DECOR = [(0.10, 0.24, True, True), (0.90, 0.30, False, False),
         (0.08, 0.76, False, True), (0.92, 0.72, True, False)]


def fmt_time(seconds: float) -> str:
    m, sec = divmod(int(seconds), 60)
    return f"{m:02d}:{sec:02d}"


class MenuScreen(Screen):
    """Tela inicial: título, botões grandes e uma vitrine do tabuleiro escolhido."""
    BTN_W, BTN_H, GAP = 340, 58, 14

    def __init__(self, app, names=None) -> None:
        super().__init__(app)
        self.saved = app.store.latest_in_progress()
        self.demo = Board()  # posição inicial exibida na vitrine
        self._showcase_key, self._showcase_img = None, None
        self.buttons = [Button("Nova partida", app.show_setup, size=24)]
        self.resume_btn = Button("Continuar partida", self._resume, primary=False, size=21)
        if self.saved:
            self.buttons.append(self.resume_btn)
        self.buttons += [Button("Histórico de partidas", app.show_history, primary=False, size=21),
                         Button("Sair", app.quit, primary=False, size=21)]

    def _resume(self) -> None:
        if self.saved:
            self.app.resume_game(self.saved.id)

    def handle(self, e) -> None:
        for b in self.buttons:
            b.handle(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.app.show_setup()

    def update(self, dt) -> None:
        pass

    def _showcase_surface(self, th, cell) -> "pygame.Surface":
        """Moldura + sombra + tabuleiro + peças desenhados uma única vez (nada é recalculado a cada quadro)."""
        key = (th["name"], cell)
        if self._showcase_key != key:
            size, m, sp = cell * 8, 14, 20
            fw = size + 2 * m
            surf = pygame.Surface((fw + 2 * sp, fw + 2 * sp + 6), pygame.SRCALPHA)
            frame = pygame.Rect(sp, sp, fw, fw)
            T.shadow(surf, frame, 14, sp, 150)
            pygame.draw.rect(surf, th["frame"], frame, border_radius=14)
            pygame.draw.rect(surf, th["rim"], frame.inflate(-8, -8), 1, border_radius=10)
            surf.blit(T.board_surface(th, cell), (sp + m, sp + m))
            for r, c, p in list(self.demo.pieces(Color.DARK)) + list(self.demo.pieces(Color.LIGHT)):
                T.piece(surf, (sp + m + c * cell + cell / 2, sp + m + r * cell + cell / 2), int(cell * 0.38),
                        p.color is Color.LIGHT, p.king, palette=th.get("pieces"))
            self._showcase_img, self._showcase_key = surf, key
        return self._showcase_img

    def draw(self, surf) -> None:
        w, h = surf.get_size()
        hero = w >= 860
        cx = int(w * 0.31) if hero else w // 2
        if hero:
            cell = max(30, min(54, (h - 150) // 8, int(w * 0.46 - 60) // 8))
            img = self._showcase_surface(T.BOARD_THEMES[self.app.theme], cell)
            surf.blit(img, img.get_rect(center=(int(w * 0.72), h // 2)))
        else:
            for fx, fy, light, king in DECOR:
                T.piece(surf, (fx * w, fy * h), 30, light, king, alpha=90)
        n = len(self.buttons)
        total = 130 + n * (self.BTN_H + self.GAP) + (24 if self.saved else 0)
        y = max(30, (h - total) // 2)
        T.piece(surf, (cx, y + 30), 34, False, True)
        T.text(surf, "DAMAS", 84, T.TEXT, center=(cx, y + 118), bold=True)
        by = y + 190
        bw = min(self.BTN_W, w - 60)
        for b in self.buttons:
            b.rect = pygame.Rect(cx - bw // 2, by, bw, self.BTN_H)
            b.draw(surf)
            by += self.BTN_H + self.GAP
            if b is self.resume_btn and self.saved:
                sv = self.saved
                T.text(surf, f"{sv.player1[:12]} × {sv.player2[:12]} · {fmt_time(sv.duration)} · {sv.moves} lances",
                       13, T.MUTED, center=(cx, by - self.GAP + 12))
                by += 24


class SetupScreen(Screen):
    """Nova partida: jogadores e lado, regras e tabuleiro, tudo numa tela só."""

    def __init__(self, app, names) -> None:
        super().__init__(app)
        self.inputs = [TextInput("", names[0]), TextInput("", names[1])]
        self.sides = [Choice("Brancas", lambda: self._side(Color.LIGHT), True),
                      Choice("Pretas", lambda: self._side(Color.DARK), False)]
        self.start = Button("Iniciar partida", self._start, size=24)
        self.back = Button("‹  Voltar", app.show_menu, primary=False, size=17)
        self.swatches: list[pygame.Rect] = []
        self.dt = 0.0
        r = app.rules
        self.toggles = {
            "mandatory_capture": Toggle("Comer obrigatório", r.mandatory_capture,
                                        "Se houver captura, você é obrigado a fazê-la."),
            "majority_rule": Toggle("Lei da maioria", r.majority_rule,
                                    "Entre várias capturas, vale a que come mais peças."),
            "men_capture_backward": Toggle("Pedra come para trás", r.men_capture_backward,
                                           "Pedras comuns também podem capturar para trás."),
            "flying_kings": Toggle("Dama voadora", r.flying_kings,
                                   "A dama anda e captura várias casas na diagonal."),
            "show_hints": Toggle("Mostrar dicas de jogadas", r.show_hints,
                                 "Destaca destinos possíveis e peças que serão capturadas."),
        }

    def _side(self, color: Color) -> None:
        self.app.p1_color = color

    def _start(self) -> None:
        n1 = self.inputs[0].value.strip() or "Jogador 1"
        n2 = self.inputs[1].value.strip() or "Jogador 2"
        self.app.rules = RuleSet(**{k: t.value for k, t in self.toggles.items()})
        self.app.start_game(n1, n2)

    def handle(self, e) -> None:
        for w in (*self.inputs, *self.toggles.values(), *self.sides, self.start, self.back):
            w.handle(e)
        self.toggles["majority_rule"].enabled = self.toggles["mandatory_capture"].value
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self._start()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.show_menu()
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.swatches):
                if r.collidepoint(e.pos):
                    self.app.theme = i

    def update(self, dt) -> None:
        self.dt = dt

    def _card(self, surf, rect, title) -> None:
        T.shadow(surf, rect, 16, 12, 90)
        pygame.draw.rect(surf, T.SURFACE, rect, border_radius=16)
        pygame.draw.rect(surf, T.SURFACE_HI, rect, 1, border_radius=16)
        T.text(surf, title, 20, T.TEXT, topleft=(rect.x + 24, rect.y + 18), bold=True)

    def draw(self, surf) -> None:
        w, h = surf.get_size()
        W = min(1000, w - 40)
        x0 = (w - W) // 2
        self.back.rect = pygame.Rect(x0, 18, 110, 36)
        self.back.draw(surf)
        T.text(surf, "Nova partida", 34, T.TEXT, center=(w // 2, 38), bold=True)
        gap = 20
        top_h = 360
        y1 = 80
        left = pygame.Rect(x0, y1, int((W - gap) * 0.45), top_h)
        right = pygame.Rect(left.right + gap, y1, W - gap - left.w, top_h)

        # ---- Jogadores e lado
        self._card(surf, left, "Jogadores")
        light1 = self.app.p1_color is Color.LIGHT
        names = ("Brancas", "Pretas")
        iw = left.w - 48
        for i, inp in enumerate(self.inputs):
            inp.label = f"Jogador {i + 1} — {names[0 if (light1 == (i == 0)) else 1]}"
            inp.rect = pygame.Rect(left.x + 24, left.y + 80 + i * 76, iw, 44)
            inp.draw(surf, self.dt)
        T.text(surf, "Jogador 1 joga com as peças", 15, T.MUTED, topleft=(left.x + 24, left.y + 222))
        bw = (iw - 10) // 2
        for i, ch in enumerate(self.sides):
            ch.selected = (i == 0) == light1
            ch.rect = pygame.Rect(left.x + 24 + i * (bw + 10), left.y + 246, bw, 40)
            ch.draw(surf)

        # ---- Regras
        self._card(surf, right, "Regras")
        for i, tg in enumerate(self.toggles.values()):
            tg.rect = pygame.Rect(right.x + 24, right.y + 54 + i * 58, right.w - 48, 52)
            tg.draw(surf)

        # ---- Tabuleiro (8 estilos em uma fileira)
        board = pygame.Rect(x0, left.bottom + gap, W, 190)
        self._card(surf, board, "Tabuleiro")
        n, g2 = len(T.BOARD_THEMES), 14
        sw = min(110, (W - 48 - g2 * (n - 1)) // n)
        row_w = n * sw + (n - 1) * g2
        sx = board.x + (board.w - row_w) // 2
        self.swatches = []
        for i, th in enumerate(T.BOARD_THEMES):
            r = pygame.Rect(sx + i * (sw + g2), board.y + 58, sw, sw)
            self.swatches.append(r)
            sel = i == self.app.theme
            pygame.draw.rect(surf, th["frame"], r.inflate(6, 6), border_radius=8)
            surf.blit(pygame.transform.smoothscale(T.board_surface(th, 14), (sw, sw)), r)
            if sel or r.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surf, T.ACCENT if sel else T.MUTED, r.inflate(10, 10), 3, border_radius=10)
            T.text(surf, th["name"], 14, T.TEXT if sel else T.MUTED, center=(r.centerx, r.bottom + 18), bold=sel)

        self.start.rect = pygame.Rect(w // 2 - 190, board.bottom + 22, 380, 60)
        self.start.draw(surf)


class HistoryScreen(Screen):
    """Lista as partidas gravadas no banco: resultado, placar e tempo. Partidas em andamento podem ser retomadas."""
    ROW = 46
    COLS = (0, 88, 300, 376, 540, 596)  # data, jogadores, placar, resultado, tempo, lances

    def __init__(self, app) -> None:
        super().__init__(app)
        self.records = app.store.history(200)
        self.scroll = 0
        self.max_scroll = 0
        self.back = Button("Voltar", app.show_menu, primary=False, size=18)
        self.clear_btn = Button("Limpar histórico", self._ask_clear, primary=False, size=18, danger=True)
        self.row_buttons: list[tuple[pygame.Rect, int]] = []     # Continuar
        self.del_buttons: list[tuple[pygame.Rect, int]] = []     # Excluir
        self.armed = None  # confirmação em dois cliques: ("one", id) ou ("all", None), válido por 3 s
        self.armed_until = 0.0

    def _arm(self, what) -> None:
        self.armed, self.armed_until = what, time.time() + 3.0

    def _ask_clear(self) -> None:
        if self.armed == ("all", None) and time.time() < self.armed_until:
            self.app.store.clear()
            self._reload()
        else:
            self._arm(("all", None))

    def _reload(self) -> None:
        self.records = self.app.store.history(200)
        self.armed, self.scroll = None, 0

    def handle(self, e) -> None:
        self.back.handle(e)
        self.clear_btn.handle(e)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.show_menu()
        elif e.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.max_scroll, self.scroll - e.y))
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, rec_id in self.row_buttons:
                if rect.collidepoint(e.pos):
                    self.app.resume_game(rec_id)
                    return
            for rect, rec_id in self.del_buttons:
                if rect.collidepoint(e.pos):
                    if self.armed == ("one", rec_id) and time.time() < self.armed_until:
                        self.app.store.delete(rec_id)  # segundo clique: exclui de verdade
                        self._reload()
                    else:
                        self._arm(("one", rec_id))
                    return

    def update(self, dt) -> None:
        pass

    def draw(self, surf) -> None:
        w, h = surf.get_size()
        card = pygame.Rect(0, 0, min(900, w - 40), h - 60)
        card.center = (w // 2, h // 2)
        T.shadow(surf, card, 18)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=18)
        pygame.draw.rect(surf, T.SURFACE_HI, card, 1, border_radius=18)
        recs = self.records
        done = sum(1 for r in recs if r.status == "finalizada")
        going = sum(1 for r in recs if r.status == "em_andamento")
        T.text(surf, "Histórico de partidas", 30, T.TEXT, center=(card.centerx, card.y + 38), bold=True)
        T.text(surf, f"{len(recs)} partidas · {done} finalizadas · {going} em andamento", 15, T.MUTED,
               center=(card.centerx, card.y + 72))
        k = (card.w - 48) / 852
        x0 = card.x + 24
        head_y = card.y + 104
        for label, off in zip(("Data", "Jogadores", "Placar", "Resultado", "Tempo", "Lances"), self.COLS):
            T.text(surf, label, 13, T.MUTED, midleft=(x0 + int(off * k), head_y))
        top = head_y + 16
        bottom = card.bottom - 78
        visible = max(1, (bottom - top) // self.ROW)
        self.max_scroll = max(0, len(recs) - visible)
        self.scroll = min(self.scroll, self.max_scroll)
        self.row_buttons, self.del_buttons = [], []
        if self.armed and time.time() >= self.armed_until:
            self.armed = None
        if not recs:
            T.text(surf, "Nenhuma partida salva ainda.", 18, T.MUTED, center=(card.centerx, card.centery))
        for i, rec in enumerate(recs[self.scroll:self.scroll + visible]):
            row = pygame.Rect(card.x + 12, top + i * self.ROW, card.w - 24, self.ROW - 6)
            pygame.draw.rect(surf, T.SURFACE_HI if i % 2 == 0 else T.SURFACE, row, border_radius=10)
            cy = row.centery
            cells = (time.strftime("%d/%m %H:%M", time.localtime(rec.started_at)),
                     f"{rec.player1[:14]} × {rec.player2[:14]}",
                     f"{rec.score1} × {rec.score2}", None, fmt_time(rec.duration), str(rec.moves))
            for text, off in zip(cells, self.COLS):
                if text is not None:
                    T.text(surf, text, 15, T.TEXT, midleft=(x0 + int(off * k), cy))
            color = T.ACCENT if rec.status == "em_andamento" else (T.MUTED if rec.status == "abandonada" else T.GOLD)
            T.text(surf, rec.result_text[:22], 15, color, midleft=(x0 + int(self.COLS[3] * k), cy), bold=True)
            confirm = self.armed == ("one", rec.id)
            dbtn = pygame.Rect(row.right - 108, row.y + 6, 98, row.h - 12)
            base = T.DANGER if confirm else T.BG
            hover = dbtn.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(surf, tuple(min(255, c + 25) for c in base) if hover else base, dbtn, border_radius=8)
            T.text(surf, "Confirmar?" if confirm else "Excluir", 14, T.TEXT if confirm else T.MUTED,
                   center=dbtn.center, bold=confirm)
            self.del_buttons.append((dbtn, rec.id))
            if rec.status == "em_andamento":
                btn = pygame.Rect(dbtn.x - 108, row.y + 6, 98, row.h - 12)
                hover = btn.collidepoint(pygame.mouse.get_pos())
                pygame.draw.rect(surf, tuple(min(255, c + 25) for c in T.ACCENT) if hover else T.ACCENT, btn, border_radius=8)
                T.text(surf, "Continuar", 14, T.TEXT, center=btn.center, bold=True)
                self.row_buttons.append((btn, rec.id))
        if self.max_scroll:
            T.text(surf, "Role o mouse para ver mais partidas", 13, T.MUTED, midbottom=(card.centerx, card.bottom - 64))
        self.back.rect = pygame.Rect(card.centerx - 200, card.bottom - 56, 180, 42)
        self.back.draw(surf)
        if recs:
            self.clear_btn.label = "Confirmar: apagar tudo?" if self.armed == ("all", None) else "Limpar histórico"
            self.clear_btn.rect = pygame.Rect(card.centerx + 20, card.bottom - 56, 220, 42)
            self.clear_btn.draw(surf)


class MatchScreen(Screen):
    TOP = 110
    M = 24  # moldura com coordenadas

    def __init__(self, app, game: Game, game_id: int | None = None) -> None:
        super().__init__(app)
        self.game = game
        self.game_id = game_id  # registro no banco (None = partida de demonstração, não é gravada)
        self.notice = ("", 0.0)  # aviso curto (ex.: "Lance inválido")
        self.selected = None
        self.hover = None
        self.anim: MoveAnimation | None = None
        self.last = None
        self.fx = Particles()
        self.bursted: set = set()
        self.promo: dict = {}  # casa -> tempo da animação de promoção
        self.pause_btn = Button("Pausar", self.game.pause, primary=False, size=17)
        self.theme_btn = Button("Tema", self._next_theme, primary=False, size=17)
        self.end_btn = Button("Encerrar", self._ask_end, primary=False, size=17, danger=True)
        self.confirm_end = False
        self.pause_buttons = [Button("Continuar", self.game.resume), Button("Reiniciar", self.restart, primary=False),
                              Button("Encerrar partida", self._ask_end, primary=False, danger=True),
                              Button("Menu", self.to_menu, primary=False)]
        self.dialog_buttons = [Button("Encerrar", self.end_match, danger=True),
                               Button("Cancelar", self._cancel_end, primary=False)]

    PROMO_TIME = 0.8

    def _clear(self) -> None:
        self.selected = self.anim = self.last = None
        self.fx = Particles()
        self.promo = {}

    def save(self) -> None:
        """Grava o estado no banco (retomar depois, histórico, tempo, placar)."""
        self.app.store.save(self.game_id, self.game, self.app.theme)

    def _ask_end(self) -> None:
        self.confirm_end = True

    def _cancel_end(self) -> None:
        self.confirm_end = False

    def end_match(self) -> None:
        """Encerra sem vencedor: fica no banco como finalizada e volta ao menu."""
        self.confirm_end = False
        self.game.end()
        self.save()
        self.app.show_menu()

    def to_menu(self) -> None:
        self.save()  # a partida continua salva e pode ser retomada pelo menu
        self.app.show_menu()

    def restart(self) -> None:
        """Reiniciar partida: mesmos nomes e regras, tabuleiro inicial (a anterior fica como abandonada)."""
        self.app.store.abandon(self.game_id)
        self.game.reset()
        self.game_id = self.app.store.create(self.game, self.app.theme)
        self._clear()

    def load_demo(self) -> None:
        """Carrega um final de jogo curto para a demonstração (tecla F2); a demo não é gravada no histórico."""
        self.app.store.abandon(self.game_id)
        self.game_id = None
        self.game.load_board(endgame_demo())
        self._clear()

    def _next_theme(self) -> None:
        self.app.theme = (self.app.theme + 1) % len(T.BOARD_THEMES)

    # ---------- layout responsivo ----------
    def layout(self, surf) -> None:
        w, h = surf.get_size()
        size = max(240, min(w - 40 - 2 * self.M, h - self.TOP - 20 - 2 * self.M))
        self.cell = size // 8
        self.ox = (w - self.cell * 8) // 2
        self.oy = self.TOP + (h - self.TOP - self.cell * 8) // 2
        # Mundo (coluna, linha) -> tela (pixels): M = T(ox, oy) · S(cell)
        # Quem joga de Pretas fica embaixo: o tabuleiro gira 180° (escala negativa em torno do centro).
        if self.game.p1_color is Color.DARK:
            self.to_screen = (Transform2D.translation(self.ox + 8 * self.cell, self.oy + 8 * self.cell)
                              @ Transform2D.scaling(-self.cell))
        else:
            self.to_screen = Transform2D.translation(self.ox, self.oy) @ Transform2D.scaling(self.cell)
        self.to_world = self.to_screen.inverse()

    def cell_at(self, pos):
        w = self.to_world.apply(Vector2D(*pos))
        c, r = math.floor(w.x), math.floor(w.y)
        return (r, c) if 0 <= r < 8 and 0 <= c < 8 else None

    def center_of(self, r, c):
        return self.to_screen.apply(Vector2D(c + 0.5, r + 0.5)).as_tuple()

    def rect_of(self, r, c) -> pygame.Rect:
        a = self.to_screen.apply(Vector2D(c, r))
        b = self.to_screen.apply(Vector2D(c + 1, r + 1))
        return pygame.Rect(round(min(a.x, b.x)), round(min(a.y, b.y)), self.cell, self.cell)

    def _selectable(self, cell) -> bool:
        """Com dicas: só peças com lance. Sem dicas: qualquer peça sua (não revela quais podem mover)."""
        if self.game.rules.show_hints:
            return bool(self.game.moves_from(cell))
        p = self.game.board.get(*cell)
        return p is not None and p.color is self.game.turn

    # ---------- eventos ----------
    def handle(self, e) -> None:
        if self.confirm_end:  # janela de confirmação: só ela responde
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self._cancel_end()
            for b in self.dialog_buttons:
                b.handle(e)
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE) and not self.game.over:
            self.game.resume() if self.game.paused else self.game.pause()
            return
        if self.game.paused:  # pausado: só o menu de pausa responde
            for b in self.pause_buttons:
                b.handle(e)
            return
        self.pause_btn.handle(e)
        self.theme_btn.handle(e)
        self.end_btn.handle(e)
        if self.confirm_end:
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_t:
            self._next_theme()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F2 and not self.anim:
            self.load_demo()
            return
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
                    self.bursted = set()
                    self.selected = None
                    return
                if cell != self.selected and not self._selectable(cell) and not self.game.rules.show_hints:
                    self.notice = ("Lance inválido", 1.4)  # sem dicas, o jogo só avisa quando o lance não vale
            self.selected = cell if self._selectable(cell) else None

    def update(self, dt) -> None:
        if self.game.paused or self.confirm_end:  # congela cronômetro, animação e partículas
            return
        self.game.tick(dt)
        self.notice = (self.notice[0], max(0.0, self.notice[1] - dt))
        self.fx.update(dt)
        self.promo = {sq: t + dt for sq, t in self.promo.items() if t + dt < self.PROMO_TIME}
        if self.anim:
            for sq in self.anim.move.captured:
                if sq not in self.bursted and self.anim.passed(sq):
                    self.bursted.add(sq)
                    victim = self.game.board.get(*sq)
                    col = T.P_LIGHT if victim.color is Color.LIGHT else (90, 90, 110)
                    self.fx.burst(self.center_of(*sq), col, n=22, speed=self.cell * 3)
                    self.fx.burst(self.center_of(*sq), T.DANGER, n=8, speed=self.cell * 2, size=3)
        if self.anim and self.anim.update(dt):
            was_king = self.anim.piece.king
            self.game.play(self.anim.move)
            if self.anim.piece.king and not was_king:
                self.promo[self.anim.move.end] = 0.0
                self.fx.burst(self.center_of(*self.anim.move.end), T.GOLD, n=40, speed=self.cell * 4, life=0.9)
            self.last, self.anim = self.anim.move, None
            self.save()  # grava a cada lance: se fechar o jogo, dá para continuar de onde parou
            if self.game.over:
                self.app.show_end(self)

    # ---------- desenho ----------
    def _hovered_move(self):
        if self.selected and self.hover:
            for m in self.game.moves_from(self.selected):
                if m.end == self.hover:
                    return m
        return None

    def draw_piece(self, surf, center, piece: Piece, alpha=255, square=None) -> None:
        scale, angle = 1.0, 0.0
        if square in self.promo:  # promoção: escala pulsante e coroa girando uma volta
            k = self.promo[square] / self.PROMO_TIME
            scale, angle = 1 + 0.3 * math.sin(math.pi * k), 2 * math.pi * k
        T.piece(surf, center, int(self.cell * 0.38), piece.color is Color.LIGHT, piece.king, alpha, scale, angle,
                T.BOARD_THEMES[self.app.theme].get("pieces"))

    def _draw_pause(self, surf) -> None:
        w, h = surf.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 160))
        surf.blit(shade, (0, 0))
        card = pygame.Rect(0, 0, min(360, w - 40), 398)
        card.center = (w // 2, h // 2)
        T.shadow(surf, card, 18)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=18)
        T.text(surf, "Jogo pausado", 30, T.TEXT, center=(card.centerx, card.y + 48), bold=True)
        T.text(surf, "P ou Esc para continuar", 15, T.MUTED, center=(card.centerx, card.y + 82))
        for i, b in enumerate(self.pause_buttons):
            b.rect = pygame.Rect(card.x + 30, card.y + 110 + i * 68, card.w - 60, 52)
            b.draw(surf)

    def _draw_end_dialog(self, surf) -> None:
        w, h = surf.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        surf.blit(shade, (0, 0))
        card = pygame.Rect(0, 0, min(400, w - 40), 230)
        card.center = (w // 2, h // 2)
        T.shadow(surf, card, 18)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=18)
        pygame.draw.rect(surf, T.DANGER, card, 2, border_radius=18)
        T.text(surf, "Encerrar esta partida?", 26, T.TEXT, center=(card.centerx, card.y + 46), bold=True)
        T.text(surf, "Ela fica no histórico como finalizada", 15, T.MUTED, center=(card.centerx, card.y + 84))
        T.text(surf, "e não poderá ser retomada.", 15, T.MUTED, center=(card.centerx, card.y + 106))
        bw = (card.w - 90) // 2
        for i, b in enumerate(self.dialog_buttons):
            b.rect = pygame.Rect(card.x + 30 + i * (bw + 30), card.bottom - 76, bw, 52)
            b.draw(surf)

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
        foe = (T.P_DARK, T.P_DARK_EDGE) if player.color is Color.LIGHT else (T.P_LIGHT, T.P_LIGHT_EDGE)
        fit = max(1, (rect.w - 120) // 11)
        for i in range(min(player.score, fit)):
            cx = rect.x + 22 + i * 11
            pygame.draw.circle(surf, foe[1], (cx, rect.y + 61), 6)
            pygame.draw.circle(surf, foe[0], (cx, rect.y + 60), 5)
        label = f"+{player.score - fit}" if player.score > fit else ("" if player.score else "0 capturas")
        x = rect.x + 16 + min(player.score, fit) * 11 + (8 if player.score else 0)
        T.text(surf, label, 14, T.MUTED, midleft=(x, rect.y + 61))
        T.text(surf, f"⏱ {m:02d}:{s:02d}", 18, T.TEXT, topright=(rect.right - 16, rect.y + 46))

    def draw(self, surf) -> None:
        self.layout(surf)
        w = surf.get_width()
        g = self.game
        # cabeçalho: cartões dos jogadores + indicador de turno
        cw = max(150, min(280, (w - 390) // 2))
        self._player_card(surf, pygame.Rect(20, 16, cw, 80), g.player1, g.turn is g.p1_color and not g.over)
        self._player_card(surf, pygame.Rect(w - 20 - cw, 16, cw, 80), g.player2,
                          g.turn is not g.p1_color and not g.over)
        lbl = T.font(17, True).render(f"Vez de {g.current.name}", True, T.TEXT)
        pill = pygame.Rect(0, 0, lbl.get_width() + 52, 34)
        pill.center = (w // 2, 32)
        pygame.draw.rect(surf, T.SURFACE_HI, pill, border_radius=17)
        pygame.draw.rect(surf, T.ACCENT, pill, 1, border_radius=17)
        glow = 7 + 2 * math.sin(pygame.time.get_ticks() / 200)
        dot = T.P_LIGHT if g.turn is Color.LIGHT else T.P_DARK
        pygame.draw.circle(surf, (*T.ACCENT,), (pill.x + 20, pill.centery), int(glow))
        pygame.draw.circle(surf, dot, (pill.x + 20, pill.centery), 6)
        surf.blit(lbl, lbl.get_rect(midleft=(pill.x + 36, pill.centery)))
        hints = g.rules.show_hints
        if self.notice[1] > 0:
            T.text(surf, self.notice[0], 15, T.DANGER, center=(w // 2, 58))
        elif hints and g.rules.mandatory_capture and g.legal and g.legal[0].captured:
            T.text(surf, "Captura obrigatória!", 15, T.DANGER, center=(w // 2, 58))
        th = T.BOARD_THEMES[self.app.theme]
        self.theme_btn.label = f"Tema: {th['name']}"
        self.pause_btn.rect = pygame.Rect(w // 2 - 170, 70, 80, 30)
        self.theme_btn.rect = pygame.Rect(w // 2 - 84, 70, 164, 30)
        self.end_btn.rect = pygame.Rect(w // 2 + 86, 70, 84, 30)
        self.pause_btn.draw(surf)
        self.theme_btn.draw(surf)
        self.end_btn.draw(surf)
        T.text(surf, "P: pausar · T: tema · F2: final de jogo (demo)", 12, T.MUTED,
               bottomleft=(8, surf.get_height() - 6))

        cs = self.cell
        hmove = self._hovered_move()
        if not hints:
            hmove = None
        targets = {m.end for m in g.moves_from(self.selected)} if (self.selected and hints) else set()
        movable = {m.start for m in g.legal} if hints else set()
        overlay = pygame.Surface((cs, cs), pygame.SRCALPHA)
        M = self.M
        frame = pygame.Rect(self.ox - M, self.oy - M, cs * 8 + 2 * M, cs * 8 + 2 * M)
        T.shadow(surf, frame, 14, 16, 140)
        pygame.draw.rect(surf, th["frame"], frame, border_radius=14)
        pygame.draw.rect(surf, th["rim"], frame.inflate(-8, -8), 1, border_radius=10)
        for i in range(8):  # coordenadas acompanham a rotação do tabuleiro
            T.text(surf, "abcdefgh"[i], 13, (232, 222, 206), center=(self.center_of(0, i)[0], self.oy + cs * 8 + M / 2))
            T.text(surf, str(8 - i), 13, (232, 222, 206), center=(self.ox - M / 2, self.center_of(i, 0)[1]))
        surf.blit(T.board_surface(th, cs), (self.ox, self.oy))
        for r in range(8):
            for c in range(8):
                rect = self.rect_of(r, c)
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
                cx, cy = self.center_of(r, c)
                if (r, c) == self.selected:
                    cy -= cs * 0.08
                elif (r, c) == self.hover and (r, c) in movable and not self.anim and not g.over:
                    cy -= cs * 0.04
                self.draw_piece(surf, (cx, cy), p, alpha, square=(r, c))
                if hmove and (r, c) in hmove.captured:
                    pygame.draw.circle(surf, T.DANGER, self.center_of(r, c), int(cs * 0.42), 3)
                elif not self.selected and not self.anim and not g.over and (r, c) in movable:
                    pygame.draw.circle(surf, T.ACCENT, self.center_of(r, c), int(cs * 0.42), 2)
        if self.selected:
            pulse = 2 + int(2 * (1 + math.sin(pygame.time.get_ticks() / 150)))
            sx, sy = self.center_of(*self.selected)
            pygame.draw.circle(surf, T.GOLD, (sx, sy - cs * 0.08), int(cs * 0.43), pulse)
        if self.anim:
            r, c = self.anim.position()
            self.draw_piece(surf, self.center_of(r, c), self.anim.piece)
        self.fx.draw(surf)
        if self.game.paused:
            self._draw_pause(surf)
        if self.confirm_end:
            self._draw_end_dialog(surf)


class EndScreen(Screen):
    def __init__(self, app, match: MatchScreen) -> None:
        super().__init__(app)
        self.match = match
        self.buttons = [Button("Revanche", app.rematch), Button("Menu", app.show_menu, primary=False)]
        self.t = 0.0
        self.confetti = Particles()

    def handle(self, e) -> None:
        for b in self.buttons:
            b.handle(e)

    def update(self, dt) -> None:
        self.t += dt
        self.match.fx.update(dt)
        self.confetti.update(dt)
        if not self.match.game.draw and self.t < 4:
            w = pygame.display.get_surface().get_width()
            colors = (T.GOLD, T.ACCENT, T.DANGER, (120, 220, 150), T.TEXT)
            for _ in range(3):
                self.confetti.burst((random.uniform(0, w), -10), random.choice(colors), n=1,
                                    speed=120, life=2.6, size=5, gravity=260, spread=1.2, angle=math.pi / 2)

    def draw(self, surf) -> None:
        self.match.draw(surf)
        w, h = surf.get_size()
        shade = pygame.Surface((w, h), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        surf.blit(shade, (0, 0))
        self.confetti.draw(surf)
        k = min(1.0, self.t * 3.5)
        card = pygame.Rect(0, 0, min(420, w - 40), 290)
        card.center = (w // 2, h // 2 + int(60 * (1 - k) ** 2))
        T.shadow(surf, card, 18)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=18)
        g = self.match.game
        title = "Empate!" if g.draw else f"{g.winner.name} venceu!"
        pygame.draw.rect(surf, T.GOLD if not g.draw else T.ACCENT, card, 2, border_radius=18)
        T.text(surf, title, 34, T.GOLD, center=(card.centerx, card.y + 50), bold=True)
        pl, pd = g.player1, g.player2
        T.text(surf, f"{pl.name} {pl.score}  ×  {pd.score} {pd.name}", 20, T.TEXT,
               center=(card.centerx, card.y + 105))
        T.text(surf, f"Tempo de partida: {fmt_time(g.elapsed)}  ·  {g.move_count} lances", 16, T.MUTED,
               center=(card.centerx, card.y + 145))
        bw = (card.w - 90) // 2
        for i, b in enumerate(self.buttons):
            b.rect = pygame.Rect(card.x + 30 + i * (bw + 30), card.bottom - 90, bw, 56)
            b.draw(surf)
