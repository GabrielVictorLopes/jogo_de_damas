"""Componentes reutilizáveis de interface."""
from abc import ABC, abstractmethod
import pygame
from . import theme as T


class Widget(ABC):
    """Base de todos os componentes: área na tela, tratamento de evento e desenho."""

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, 0, 0)

    @abstractmethod
    def handle(self, e) -> None: ...

    @abstractmethod
    def draw(self, surf, *args) -> None: ...


class Button(Widget):
    def __init__(self, label: str, on_click, primary: bool = True, size: int = 22) -> None:
        self.label, self.on_click, self.primary, self.size = label, on_click, primary, size
        super().__init__()

    def handle(self, e) -> None:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.on_click()

    def draw(self, surf) -> None:
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        base = T.ACCENT if self.primary else T.SURFACE_HI
        color = tuple(min(255, c + 25) for c in base) if hover else base
        if self.primary:
            T.shadow(surf, self.rect, 12, 8, 80)
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        T.text(surf, self.label, self.size, T.TEXT, center=self.rect.center, bold=True)


class TextInput(Widget):
    def __init__(self, label: str, value: str, max_len: int = 16) -> None:
        self.label, self.value, self.max_len = label, value, max_len
        super().__init__()
        self.active = False
        self.blink = 0.0

    def handle(self, e) -> None:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.active = self.rect.collidepoint(e.pos)
        elif self.active and e.type == pygame.TEXTINPUT:
            self.value = (self.value + e.text)[: self.max_len]
        elif self.active and e.type == pygame.KEYDOWN and e.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]

    def draw(self, surf, dt: float) -> None:
        self.blink = (self.blink + dt) % 1.0
        T.text(surf, self.label, 16, T.MUTED, bottomleft=(self.rect.x, self.rect.y - 6))
        pygame.draw.rect(surf, T.SURFACE_HI, self.rect, border_radius=10)
        pygame.draw.rect(surf, T.ACCENT if self.active else T.SURFACE_HI, self.rect, 2, border_radius=10)
        r = T.text(surf, self.value, 22, T.TEXT, midleft=(self.rect.x + 14, self.rect.centery))
        if self.active and self.blink < 0.5:
            pygame.draw.line(surf, T.TEXT, (r.right + 2, r.top + 3), (r.right + 2, r.bottom - 3), 2)


class Toggle(Widget):
    """Interruptor liga/desliga com rótulo."""

    def __init__(self, label: str, value: bool) -> None:
        self.label, self.value, self.enabled = label, value, True
        super().__init__()

    def handle(self, e) -> None:
        if (self.enabled and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                and self.rect.collidepoint(e.pos)):
            self.value = not self.value

    def draw(self, surf) -> None:
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf, T.SURFACE_HI if hover else T.SURFACE, self.rect, border_radius=10)
        on = self.value and self.enabled
        T.text(surf, self.label, 15, T.TEXT if self.enabled else T.MUTED,
               midleft=(self.rect.x + 10, self.rect.centery))
        pill = pygame.Rect(0, 0, 38, 22)
        pill.midright = (self.rect.right - 10, self.rect.centery)
        pygame.draw.rect(surf, T.ACCENT if on else (70, 76, 94), pill, border_radius=11)
        knob_x = pill.right - 11 if self.value else pill.x + 11
        pygame.draw.circle(surf, T.TEXT if self.enabled else T.MUTED, (knob_x, pill.centery), 8)
