"""Controlador principal: laço de jogo a 60 FPS e troca de telas."""
import pygame
from checkers.game import Game
from checkers.rules import RuleSet
from .screens import MenuScreen, MatchScreen, EndScreen
from . import theme as T


class App:
    FPS = 60

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Damas")
        self.surface = pygame.display.set_mode((980, 780), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.names = ["Jogador 1", "Jogador 2"]
        self.theme = 0  # índice em theme.BOARD_THEMES
        self.rules = RuleSet()
        self.show_menu()

    def show_menu(self) -> None:
        self.screen = MenuScreen(self, self.names)

    def start_game(self, n1: str, n2: str) -> None:
        self.names = [n1, n2]
        self.screen = MatchScreen(self, Game(n1, n2, self.rules))

    def show_end(self, match) -> None:
        self.screen = EndScreen(self, match)

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
            T.text(self.surface, f"{self.clock.get_fps():.0f} FPS", 12, T.MUTED,
                   bottomright=(self.surface.get_width() - 8, self.surface.get_height() - 6))
            pygame.display.flip()
        pygame.quit()
