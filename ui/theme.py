"""Paleta e tipografia."""
import pygame
from .transform import Transform2D

BG = (17, 20, 28)
SURFACE = (29, 33, 45)
SURFACE_HI = (44, 50, 66)
TEXT = (236, 239, 245)
MUTED = (146, 154, 172)
ACCENT = (82, 160, 255)
GOLD = (246, 192, 72)
DANGER = (236, 96, 96)
SQ_LIGHT = (238, 226, 204)
SQ_DARK = (126, 92, 68)
P_LIGHT = (246, 244, 238)
P_LIGHT_EDGE = (196, 190, 178)
P_DARK = (44, 44, 54)
P_DARK_EDGE = (16, 16, 22)

_cache: dict = {}


def font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _cache:
        _cache[key] = pygame.font.SysFont("segoeui,helveticaneue,roboto,arial", size, bold=bold)
    return _cache[key]


def text(surf, msg, size, color, center=None, bold=False, **pos):
    img = font(size, bold).render(str(msg), True, color)
    rect = img.get_rect(center=center) if center else img.get_rect(**pos)
    surf.blit(img, rect)
    return rect


# ---------- Temas de tabuleiro ("campos") ----------
BOARD_THEMES = [
    {"name": "Clássico", "light": (238, 226, 204), "dark": (126, 92, 68), "frame": (74, 52, 38)},
    {"name": "Torneio", "light": (236, 238, 210), "dark": (118, 150, 86), "frame": (56, 76, 44)},
    {"name": "Oceano", "light": (222, 234, 244), "dark": (72, 116, 166), "frame": (34, 58, 92)},
    {"name": "Mármore", "light": (242, 242, 244), "dark": (128, 132, 148), "frame": (58, 60, 72)},
    {"name": "Neon", "light": (52, 46, 86), "dark": (96, 62, 170), "frame": (30, 24, 54)},
]
BG_TOP, BG_BOTTOM = (26, 31, 48), (11, 13, 19)
_bg: dict = {}


def background(surf) -> None:
    """Fundo em degradê com brilho suave (cacheado por tamanho de janela)."""
    size = surf.get_size()
    if size not in _bg:
        g = pygame.Surface(size)
        h = max(1, size[1] - 1)
        for y in range(size[1]):
            t = y / h
            pygame.draw.line(g, [int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)], (0, y), (size[0], y))
        glow = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(glow, (*ACCENT, 16), (size[0] // 2, 0), int(size[0] * 0.55))
        g.blit(glow, (0, 0))
        _bg.clear()
        _bg[size] = g
    surf.blit(_bg[size], (0, 0))


def shadow(surf, rect, radius=14, spread=12, alpha=110) -> None:
    s = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    for i in range(spread):
        pygame.draw.rect(s, (0, 0, 0, alpha // spread), (i, i, s.get_width() - 2 * i, s.get_height() - 2 * i),
                         border_radius=radius + spread - i)
    surf.blit(s, (rect.x - spread, rect.y - spread + 6))


def piece(surf, center, rad, light: bool, king=False, alpha=255, scale=1.0, crown_angle=0.0) -> None:
    """Peça com sombra, relevo, sulcos e brilho; coroa dourada para dama.

    scale e crown_angle animam a promoção: a coroa é transformada pela matriz
    T(centro) · R(ângulo) · S(escala) aplicada aos vértices do polígono.
    """
    rad = max(4, int(rad * scale))
    body, edge = (P_LIGHT, P_LIGHT_EDGE) if light else (P_DARK, P_DARK_EDGE)
    c = rad + 6
    layer = pygame.Surface((c * 2, c * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(layer, (0, 0, 0, 90), (c + 2, c + 5), rad)
    pygame.draw.circle(layer, edge, (c, c), rad)
    pygame.draw.circle(layer, body, (c, c - 3), rad - 2)
    pygame.draw.circle(layer, edge, (c, c - 3), int(rad * 0.70), 2)
    pygame.draw.circle(layer, edge, (c, c - 3), int(rad * 0.45), 1)
    pygame.draw.circle(layer, (255, 255, 255, 55 if light else 30), (c - rad * 0.3, c - rad * 0.4), rad * 0.38)
    if king:
        s, cy = rad * 0.48, c - 3
        base = [(-s, s * 0.55), (-s, -s * 0.45), (-s * 0.5, 0), (0, -s * 0.8),
                (s * 0.5, 0), (s, -s * 0.45), (s, s * 0.55)]
        m = Transform2D.translation(c, cy) @ Transform2D.rotation(crown_angle)
        pts = m.apply_points(base)
        pygame.draw.polygon(layer, GOLD, pts)
        pygame.draw.polygon(layer, (150, 105, 20), pts, 2)
    layer.set_alpha(alpha)
    surf.blit(layer, (int(center[0]) - c, int(center[1]) - c))
