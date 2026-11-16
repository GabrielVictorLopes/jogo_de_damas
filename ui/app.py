"""Controlador principal: laço de jogo a 60 FPS e troca de telas."""
import pygame
from checkers.game import Game
from checkers.rules import RuleSet
from .screens import MenuScreen, MatchScreen, EndScreen
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
        self.fade = 0.0
        self.show_menu()

    def _switch(self, screen, fade: bool = True) -> None:
        self.screen = screen
        if fade:
            self.fade = 1.0

    def show_menu(self) -> None:
        self._switch(MenuScreen(self, self.names))

    def start_game(self, n1: str, n2: str) -> None:
        self.names = [n1, n2]
        self._switch(MatchScreen(self, Game(n1, n2, self.rules)))

    def show_end(self, match) -> None:
        self._switch(EndScreen(self, match), fade=False)

    def rematch(self) -> None:
        self.start_game(*self.names)

    def run(self) -> None:
        pygame.key.start_text_input()
        running = True
        while running:
            dt = self.clock.tick(self.FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
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
        pygame.quit()
