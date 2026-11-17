"""Controlador principal: laço de jogo a 60 FPS e troca de telas."""
import pygame
from checkers.board import Color
from checkers.game import Game
from checkers.rules import RuleSet
from checkers.storage import GameStore
from .screens import MenuScreen, SetupScreen, MatchScreen, EndScreen, HistoryScreen
from . import theme as T


def make_icon(size: int = 64) -> "pygame.Surface":
    """Ícone da janela desenhado por código: peça dourada com coroa de dama."""
    u = size / 64
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(s, (20, 23, 31), (0, 0, size, size), border_radius=int(14 * u))
    cx, cy = size // 2, int(size * 0.55)
    pygame.draw.circle(s, (126, 92, 68), (cx, cy), int(24 * u))
    pygame.draw.circle(s, (232, 177, 58), (cx, cy), int(22 * u))
    pygame.draw.circle(s, (126, 92, 68), (cx, cy), int(15 * u), max(1, int(2 * u)))
    crown = [(-16, 5), (-16, -7), (-8, -1), (0, -11), (8, -1), (16, -7), (16, 5)]
    pygame.draw.polygon(s, (20, 23, 31), [(cx + x * u, cy + y * u) for x, y in crown])
    pygame.draw.rect(s, (20, 23, 31), (cx - 16 * u, cy + 4 * u, 32 * u, 4 * u))
    return s


class App:
    FPS = 60

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_icon(make_icon())  # antes de criar a janela
        pygame.display.set_caption("Damas")
        self.surface = pygame.display.set_mode((980, 780), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.names = ["Jogador 1", "Jogador 2"]
        self.theme = 0  # índice em theme.BOARD_THEMES
        self.rules = RuleSet()
        self.p1_color = Color.LIGHT  # lado do Jogador 1
        self.store = GameStore()     # banco SQLite: histórico e partidas salvas
        self.fade = 0.0
        self.running = True
        self.show_menu()

    def _switch(self, screen, fade: bool = True) -> None:
        self.screen = screen
        if fade:
            self.fade = 1.0

    def show_menu(self) -> None:
        self._switch(MenuScreen(self, self.names))

    def show_setup(self) -> None:
        self._switch(SetupScreen(self, self.names))

    def quit(self) -> None:
        self.save_current()
        self.running = False

    def show_history(self) -> None:
        self._switch(HistoryScreen(self))

    def start_game(self, n1: str, n2: str) -> None:
        self.names = [n1, n2]
        game = Game(n1, n2, self.rules, self.p1_color)
        self._switch(MatchScreen(self, game, self.store.create(game, self.theme)))

    def resume_game(self, game_id: int) -> None:
        """Retoma uma partida salva (tabuleiro, turno, placar, tempo, regras e lado) já em pausa."""
        loaded = self.store.load(game_id)
        if loaded is None:
            return
        game, theme = loaded
        self.theme = theme % len(T.BOARD_THEMES)
        self.rules, self.p1_color = game.rules, game.p1_color
        self.names = [game.player1.name, game.player2.name]
        game.pause()
        self._switch(MatchScreen(self, game, game_id))

    def save_current(self) -> None:
        """Grava a partida em andamento (usado ao fechar a janela)."""
        if isinstance(self.screen, MatchScreen) and not self.screen.game.over:
            self.screen.save()

    def show_end(self, match) -> None:
        self._switch(EndScreen(self, match), fade=False)

    def rematch(self) -> None:
        self.start_game(*self.names)

    def run(self) -> None:
        pygame.key.start_text_input()
        self.running = True
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.save_current()
                    self.running = False
                else:
                    self.screen.handle(e)
            self.screen.update(dt)
            T.background(self.surface)
            self.screen.draw(self.surface)
            if self.fade > 0:
                veil = pygame.Surface(self.surface.get_size())
                veil.fill(T.BG_BOTTOM)
                veil.set_alpha(int(255 * self.fade))
                self.surface.blit(veil, (0, 0))
                self.fade = max(0.0, self.fade - dt * 3.5)
            T.text(self.surface, f"{self.clock.get_fps():.0f} FPS", 12, T.MUTED,
                   bottomright=(self.surface.get_width() - 8, self.surface.get_height() - 6))
            pygame.display.flip()
        self.store.close()
        pygame.quit()